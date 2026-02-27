from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.responses import FileResponse
from sqlalchemy import select, func

from .db import Base, engine, get_db
from . import models, schemas
from .content import make_word_flash_items
from .content import (
    make_word_flash_items,
    make_odd_one_out_items,
    make_letter_builder_items,
    list_themes,
    DEFAULT_THEME_ID,
)

DIFF_PRESETS = {
    "easy":   {"exposure": 1500, "min": 1100, "max": 2000, "items": 6, "options": 3, "step": 120},
    "normal": {"exposure": 1200, "min": 800,  "max": 1800, "items": 8, "options": 4, "step": 150},
    "hard":   {"exposure": 900,  "min": 500,  "max": 1400, "items": 10, "options": 5, "step": 150},
}

SURVIVAL_LIVES = {
    "easy": 4,
    "normal": 3,
    "hard": 2,
}

app = FastAPI(title="Reading Game API")
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")
# Создать таблицы (для MVP ок; позже — миграции Alembic)
Base.metadata.create_all(bind=engine)
def seed_achievements():
    with next(get_db()) as db:
        existing = db.query(models.Achievement).count()
        if existing > 0:
            return

        rows = [
            ("streak_5", "Серия 5", "5 правильных подряд", "🔥"),
            ("perfect_game", "Идеально", "100% точность за игру", "🎯"),
            ("fast_2000", "Молния", "Средняя реакция быстрее 2000 мс", "⚡"),
            ("games_10", "Опытный", "Сыграно 10 игр", "🏆"),
            ("words_100", "Читатель", "Прочитано 100 слов", "📘"),
        ]

        for code, title, desc, icon in rows:
            db.add(models.Achievement(
                code=code,
                title=title,
                description=desc,
                icon=icon
            ))

        db.commit()

seed_achievements()
@app.get("/api/themes")
def get_themes():
    return list_themes()

@app.post("/api/children", response_model=schemas.ChildOut)
def create_child(payload: schemas.ChildCreate, db: Session = Depends(get_db)):
    child = models.Child(name=payload.name.strip())
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


@app.get("/api/children", response_model=list[schemas.ChildOut])
def list_children(db: Session = Depends(get_db)):
    return db.query(models.Child).order_by(models.Child.id.desc()).all()


@app.post("/api/sessions/start", response_model=schemas.SessionStartOut)
def start_session(payload: schemas.SessionStartIn, db: Session = Depends(get_db)):
    theme_id = payload.theme_id or DEFAULT_THEME_ID
    DIFF_PRESETS = {
        "easy": {"exposure": 1500, "min": 1100, "max": 2000, "items": 6, "options": 3, "step": 120},
        "normal": {"exposure": 1200, "min": 800, "max": 1800, "items": 7, "options": 4, "step": 150},
        "hard": {"exposure": 900, "min": 500, "max": 1400, "items": 9, "options": 5, "step": 150},
    }
    child = db.get(models.Child, payload.child_id)
    if not child:
        raise HTTPException(404, "Child not found")
    preset = DIFF_PRESETS[payload.difficulty]
    exposure_ms = preset["exposure"]
    items_total = preset["items"]
    options_k = preset["options"]

    last = (
        db.query(models.Session)
        .filter(
            models.Session.child_id == child.id,
            models.Session.mode == payload.mode,
            models.Session.difficulty == payload.difficulty,
            models.Session.finished_at.isnot(None),
        )
        .order_by(models.Session.id.desc())
        .first()
    )
    if last:
        exposure_ms = int(last.exposure_ms)

    # clamp в рамках уровня
    exposure_ms = max(preset["min"], min(preset["max"], exposure_ms))

    session = models.Session(
        child_id=child.id,
        mode=payload.mode,
        difficulty=payload.difficulty,
        theme_id=theme_id,
        exposure_ms=exposure_ms,
        items_total=items_total,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if payload.mode == "odd_one_out":
        items = make_odd_one_out_items(
            items_total,
            difficulty=payload.difficulty,
            theme_id=theme_id,
            options_k=options_k,
        )
    elif payload.mode == "letter_builder":
        items = make_letter_builder_items(
            items_total,
            difficulty=payload.difficulty,
            theme_id=theme_id,
        )
    else:
        items = make_word_flash_items(
            items_total,
            difficulty=payload.difficulty,
            theme_id=theme_id,
            options_k=options_k,
        )

    out_items = [
        schemas.WordFlashPayload(
            item_id=i.item_id,
            exposure_ms=session.exposure_ms,
            target=i.target,
            options=i.options,
            prompt=getattr(i, "prompt", None),
            correct=getattr(i, "correct", None),
        )
        for i in items
    ]

    lives_start = None
    lives_left = None
    if payload.mode == "survival":
        lives_start = SURVIVAL_LIVES.get(payload.difficulty, 3)
        lives_left = lives_start

    return schemas.SessionStartOut(
        session_id=session.id,
        mode=payload.mode,
        exposure_ms=session.exposure_ms,
        items_total=session.items_total,
        items=out_items,
        difficulty=payload.difficulty,
        theme_id=theme_id,
        lives_start=lives_start,
        lives_left=lives_left,
    )


@app.post("/api/sessions/{session_id}/attempt")
def submit_attempt(session_id: int, payload: schemas.AttemptIn, db: Session = Depends(get_db)):
    session = db.get(models.Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    a = models.Attempt(
        session_id=session.id,
        item_id=payload.item_id,
        correct=1 if payload.correct else 0,
        reaction_ms=max(0, payload.reaction_ms),
        shown_ms=max(0, payload.shown_ms),
    )
    db.add(a)
    db.commit()

    # ---- SURVIVAL логика ----
    if session.mode == "survival":
        lives_start = SURVIVAL_LIVES.get(session.difficulty, 3)

        wrong_count = (
            db.query(models.Attempt)
            .filter(models.Attempt.session_id == session.id, models.Attempt.correct == 0)
            .count()
        )

        lives_left = max(0, lives_start - wrong_count)

        finished = False
        if lives_left <= 0:
            session.finished_at = datetime.utcnow()
            db.commit()
            finished = True

        return {"ok": True, "mode": "survival", "lives_left": lives_left, "finished": finished}

    return {"ok": True}


@app.post("/api/sessions/{session_id}/finish", response_model=schemas.SessionFinishOut)
def finish_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(models.Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    attempts = (
        db.query(models.Attempt)
        .filter(models.Attempt.session_id == session.id)
        .all()
    )

    total = len(attempts)
    correct = sum(1 for a in attempts if a.correct)
    wrong = total - correct

    accuracy = (correct / total) if total else 0.0
    avg_reaction_ms = (
        sum(a.reaction_ms for a in attempts) / total
        if total else 0.0
    )

    next_exposure = session.exposure_ms
    if accuracy > 0.8 and avg_reaction_ms < 900:
        next_exposure = max(150, session.exposure_ms - 50)
    elif accuracy < 0.6:
        next_exposure = min(2000, session.exposure_ms + 100)

    # Закрываем только если ещё не закрыта
    if session.finished_at is None:
        session.finished_at = datetime.utcnow()
        session.exposure_ms = next_exposure
        db.commit()
    # ================= ACHIEVEMENTS =================

    new_achievements = []

    # считаем максимум серии
    max_streak = 0
    cur = 0
    for a in attempts:
        if a.correct:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 0

    # всего завершённых игр
    total_sessions = (
        db.query(models.Session)
        .filter(
            models.Session.child_id == session.child_id,
            models.Session.finished_at.isnot(None),
        )
        .count()
    )

    # всего слов (по attempts)
    total_attempts = (
        db.query(models.Attempt)
        .join(models.Session)
        .filter(models.Session.child_id == session.child_id)
        .count()
    )

    def unlock(code: str):
        ach = db.execute(
            select(models.Achievement).where(models.Achievement.code == code)
        ).scalar_one_or_none()
        if not ach:
            return

        exists = db.execute(
            select(models.ChildAchievement)
            .where(
                models.ChildAchievement.child_id == session.child_id,
                models.ChildAchievement.achievement_id == ach.id,
            )
        ).scalar_one_or_none()

        if exists:
            return

        db.add(models.ChildAchievement(
            child_id=session.child_id,
            achievement_id=ach.id
        ))

        new_achievements.append(
            schemas.AchievementOut(
                code=ach.code,
                title=ach.title,
                description=ach.description,
                icon=ach.icon
            )
        )

    # Условия
    if max_streak >= 5:
        unlock("streak_5")

    if accuracy >= 1.0:
        unlock("perfect_game")

    if avg_reaction_ms < 2000 and total > 0:
        unlock("fast_2000")

    if total_sessions >= 10:
        unlock("games_10")

    if total_attempts >= 100:
        unlock("words_100")

    if new_achievements:
        db.commit()
    return schemas.SessionFinishOut(
        session_id=session.id,
        accuracy=accuracy,
        avg_reaction_ms=avg_reaction_ms,
        next_exposure_ms=int(next_exposure),
        new_achievements=new_achievements
    )

def _calc_child_stats_by_mode(child: models.Child, db: Session) -> schemas.ChildStatsByModeOut:
    # берем только завершённые сессии
    sessions = (
        db.query(models.Session)
        .filter(
            models.Session.child_id == child.id,
            models.Session.finished_at.isnot(None),
        )
        .all()
    )

    by_mode: dict[str, list[models.Session]] = {}
    for s in sessions:
        by_mode.setdefault(s.mode, []).append(s)

    modes_out: list[schemas.ModeStatsOut] = []

    for mode, mode_sessions in by_mode.items():
        session_ids = [s.id for s in mode_sessions]

        attempts = (
            db.query(models.Attempt)
            .filter(models.Attempt.session_id.in_(session_ids))
            .all()
        )

        attempts_n = len(attempts)
        correct_n = sum(1 for a in attempts if a.correct)
        reaction_sum = sum(a.reaction_ms for a in attempts)

        avg_accuracy = (correct_n / attempts_n) if attempts_n else 0.0
        avg_reaction_ms = (reaction_sum / attempts_n) if attempts_n else 0.0

        modes_out.append(
            schemas.ModeStatsOut(
                mode=mode,  # type: ignore[arg-type]
                sessions=len(mode_sessions),
                attempts=attempts_n,
                avg_accuracy=avg_accuracy,
                avg_reaction_ms=avg_reaction_ms,
            )
        )

    # стабильный порядок
    order = {"word_flash": 0, "survival": 1, "odd_one_out": 2, "letter_builder": 3}
    modes_out.sort(key=lambda x: order.get(x.mode, 99))

    return schemas.ChildStatsByModeOut(
        child_id=child.id,
        child_name=child.name,
        total_sessions=len(sessions),
        modes=modes_out,
    )

@app.get("/api/stats/summary/{child_id}", response_model=schemas.ChildStatsOut)
def get_stats(child_id: int, db: Session = Depends(get_db)):
    child = db.get(models.Child, child_id)
    if not child:
        raise HTTPException(404, "Child not found")

    sessions = (
        db.query(models.Session)
        .filter(
            models.Session.child_id == child_id,
            models.Session.finished_at.isnot(None),
        )
        .all()
    )

    total_sessions = len(sessions)
    if total_sessions == 0:
        return schemas.ChildStatsOut(
            child_id=child_id,
            total_sessions=0,
            avg_accuracy=0.0,
            avg_reaction_ms=0.0,
        )

    total_attempts = 0
    total_correct = 0
    total_reaction = 0

    for s in sessions:
        attempts = (
            db.query(models.Attempt)
            .filter(models.Attempt.session_id == s.id)
            .all()
        )

        total_attempts += len(attempts)
        total_correct += sum(1 for a in attempts if a.correct)
        total_reaction += sum(a.reaction_ms for a in attempts)

    avg_accuracy = (total_correct / total_attempts) if total_attempts else 0.0
    avg_reaction_ms = (total_reaction / total_attempts) if total_attempts else 0.0

    return schemas.ChildStatsOut(
        child_id=child_id,
        total_sessions=total_sessions,
        avg_accuracy=avg_accuracy,
        avg_reaction_ms=avg_reaction_ms,
    )

@app.get("/api/stats/children/{child_id}", response_model=schemas.ChildStatsByModeOut)
def get_child_stats_by_mode(child_id: int, db: Session = Depends(get_db)):
    child = db.get(models.Child, child_id)
    if not child:
        raise HTTPException(404, "Child not found")

    return _calc_child_stats_by_mode(child, db)

@app.get("/api/stats/children", response_model=schemas.AllChildrenStatsOut)
def get_all_children_stats(db: Session = Depends(get_db)):
    children = db.query(models.Child).order_by(models.Child.id.asc()).all()

    out = [
        _calc_child_stats_by_mode(c, db)
        for c in children
    ]

    return schemas.AllChildrenStatsOut(
        total_children=len(children),
        children=out,
    )
@app.get("/api/children/{child_id}/achievements")
def get_child_achievements(child_id: int, db: Session = Depends(get_db)):
    child = db.get(models.Child, child_id)
    if not child:
        raise HTTPException(404, "Child not found")

    # все достижения
    all_achs = db.query(models.Achievement).order_by(models.Achievement.id.asc()).all()

    # какие открыты у ребёнка
    unlocked_rows = (
        db.query(models.ChildAchievement.achievement_id)
        .filter(models.ChildAchievement.child_id == child_id)
        .all()
    )
    unlocked_ids = {x[0] for x in unlocked_rows}

    return [
        {
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "unlocked": (a.id in unlocked_ids),
        }
        for a in all_achs
    ]