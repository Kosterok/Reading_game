import random
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class WordFlashItem:
    item_id: str
    target: str
    options: list[str]
    prompt: Optional[str] = None
    correct: Optional[str] = None

# ---- Темы ----
# В каждой теме: слова по difficulty
THEMES = {
    1: {
        "name": "Школа",
        "easy": [
            "школа","класс","урок","дом","мама","папа","книга","ручка","пенал","стол","доска","лист"
        ],
        "normal": [
            "тетрадь","учебник","учитель","задание","перемена","портфель","карандаш","линейка","дневник","проверка"
        ],
        "hard": [
            "внимательный","аккуратный","объяснение","проверочный","самостоятельный","подготовка"
        ],
    },
    2: {
        "name": "Животные",
        "easy": [
            "кот","пёс","ёж","волк","лиса","заяц","рыба","утка","слон","тигр","мышь","жук"
        ],
        "normal": [
            "собака","кошка","кролик","лошадь","медведь","воробей","лягушка","черепаха","попугай"
        ],
        "hard": [
            "путешествие","наблюдение","впечатление","прекрасный","осторожный"
        ],
    },
    3: {
        "name": "Природа",
        "easy": [
            "лес","сад","река","поле","снег","дождь","ветер","солнце","облако","трава","лист"
        ],
        "normal": [
            "солнышко","дождик","мороз","туман","радуга","озеро","берёза","ромашка","тропинка"
        ],
        "hard": [
            "приближение","удивление","воображение","рассвет","сверкнуло"
        ],
    },
    4: {
        "name": "Еда",
        "easy": [
            "сок","сыр","хлеб","мёд","чай","каша","суп","лук","соль","рис","яблоко"
        ],
        "normal": [
            "молоко","печенье","компот","котлета","морковка","картофель","карамель","магазин"
        ],
        "hard": [
            "праздничный","впечатление","интересный","любопытный"
        ],
    },
}

DEFAULT_THEME_ID = 1

def list_themes():
    return [{"id": tid, "name": t["name"]} for tid, t in sorted(THEMES.items())]

def _pool_for(theme_id: int, difficulty: str) -> list[str]:
    theme = THEMES.get(theme_id) or THEMES[DEFAULT_THEME_ID]
    words = theme.get(difficulty) or theme["normal"]
    return words

def make_word_flash_items(n: int, difficulty: str, theme_id: int, options_k: int = 4) -> list[WordFlashItem]:
    words = _pool_for(theme_id, difficulty)
    pool = words[:]
    random.shuffle(pool)

    # без повторов в рамках сессии, если слов хватает
    if len(pool) >= n:
        pool = pool[:n]

    items: list[WordFlashItem] = []
    for i in range(n):
        target = pool[i % len(pool)]
        distractors = [w for w in words if w != target]
        random.shuffle(distractors)
        options = [target] + distractors[: max(0, options_k - 1)]
        random.shuffle(options)
        items.append(WordFlashItem(item_id=f"wf_t{theme_id}_{difficulty}_{i}", target=target, options=options))
    return items
def make_odd_one_out_items(n: int, difficulty: str, theme_id: int, options_k: int = 4) -> list[WordFlashItem]:
    """Generate 'odd one out' tasks.

    options: list[str] of length options_k (usually 4)
    target: the odd word (must be selected by the player)

    - pick (options_k-1) words from the chosen theme
    - pick 1 word from a different theme
    """
    if options_k < 3:
        options_k = 3

    base_words = _pool_for(theme_id, difficulty)
    base_pool = base_words[:]
    random.shuffle(base_pool)

    other_theme_ids = [tid for tid in THEMES.keys() if tid != theme_id]
    if not other_theme_ids:
        other_theme_ids = [DEFAULT_THEME_ID]

    items: list[WordFlashItem] = []
    for i in range(n):
        group_k = max(2, options_k - 1)
        group = []
        while len(group) < group_k:
            w = base_pool[(i + len(group)) % len(base_pool)]
            if w not in group:
                group.append(w)

        odd_theme_id = random.choice(other_theme_ids)
        odd_words = _pool_for(odd_theme_id, difficulty)
        odd = random.choice([w for w in odd_words if w not in group] or odd_words)

        options = group + [odd]
        options = list(dict.fromkeys(options))
        while len(options) < options_k:
            cand = random.choice([w for w in base_words if w not in options] or base_words)
            options.append(cand)

        options = options[:options_k]
        random.shuffle(options)
        items.append(WordFlashItem(item_id=f"ooo_t{theme_id}_{difficulty}_{i}", target=odd, options=options))
    return items