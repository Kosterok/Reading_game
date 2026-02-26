from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse


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
    "normal": {"exposure": 1200, "min": 800,  "max": 1800, "items": 7, "options": 4, "step": 150},
    "hard":   {"exposure": 900,  "min": 500,  "max": 1400, "items": 9, "options": 5, "step": 150},
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

    return schemas.SessionFinishOut(
        session_id=session.id,  # ← ДОБАВИТЬ
        accuracy=accuracy,
        avg_reaction_ms=avg_reaction_ms,
        next_exposure_ms=int(next_exposure),
    )