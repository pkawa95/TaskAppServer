from pydantic import BaseModel, constr
from datetime import date
from typing import Optional

# ----- TASK SCHEMAS -----
class TaskBase(BaseModel):
    subject: str
    priority: str
    title: str
    due_date: date


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    completed: Optional[bool] = None


class TaskOut(TaskBase):
    id: int
    completed: bool

    class Config:
        from_attributes = True  # Zamiast orm_mode (FastAPI 2.x kompatybilność)


# ----- USER SCHEMAS -----
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=32)
    password: constr(min_length=6, max_length=72)  # bcrypt ma limit 72 bajty


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
