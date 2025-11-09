from pydantic import BaseModel
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
        orm_mode = True


# ----- USER SCHEMAS -----
class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True
