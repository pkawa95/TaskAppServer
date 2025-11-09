from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# ---------- SUBJECT SCHEMAS ----------
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int

    class Config:
        orm_mode = True


# ---------- TASK SCHEMAS ----------
class TaskBase(BaseModel):
    title: str
    subject: str
    priority: str
    due_date: date

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    completed: Optional[bool] = None

class TaskOut(TaskBase):
    id: int
    completed: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ---------- USER SCHEMAS ----------
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        orm_mode = True
