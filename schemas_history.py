from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ==============================================================
#                         HISTORIA AKCJI
# ==============================================================

class TaskHistoryBase(BaseModel):
    task_id: int
    action: str
    timestamp: datetime


class TaskHistoryOut(TaskHistoryBase):
    task_title: Optional[str] = None  # Tytuł zadania (opcjonalnie)
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
