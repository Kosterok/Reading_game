from pydantic import BaseModel, Field
from typing import Literal, Optional

Difficulty = Literal["easy", "normal", "hard"]
Mode = Literal["word_flash", "survival", "odd_one_out", "letter_builder"]

class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)

class ChildOut(BaseModel):
    id: int
    name: str

class SessionStartIn(BaseModel):
    child_id: int
    mode: Mode = "word_flash"
    difficulty: Difficulty = "normal"
    theme_id: int = 1

class WordFlashPayload(BaseModel):
    item_id: str
    exposure_ms: int
    target: str
    options: list[str]
    prompt: Optional[str] = None  # что показываем на этапе "показ"
    correct: Optional[str] = None  # правильный ответ (если отличается от target)

class SessionStartOut(BaseModel):
    session_id: int
    mode: Mode
    exposure_ms: int
    items_total: int
    items: list[WordFlashPayload]
    difficulty: Difficulty
    theme_id: int
    lives_start: Optional[int] = None
    lives_left: Optional[int] = None

class AttemptIn(BaseModel):
    item_id: str
    correct: bool
    reaction_ms: int
    shown_ms: int

class SessionFinishOut(BaseModel):
    session_id: int
    accuracy: float
    avg_reaction_ms: float
    next_exposure_ms: int