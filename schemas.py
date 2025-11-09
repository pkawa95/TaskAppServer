from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# ==============================================================
#                       SUBJECT SCHEMAS
# ==============================================================

class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubjectOut(SubjectBase):
    id: int

    class Config:
        from_attributes = True


# ==============================================================
#                        TASK SCHEMAS
# ==============================================================

class TaskBase(BaseModel):
    title: str
    priority: str
    due_date: date
    subject_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    subject_id: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    completed: bool
    created_at: datetime
    subject_id: Optional[int] = None

    class Config:
        from_attributes = True


# ==============================================================
#                         USER SCHEMAS
# ==============================================================

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
        from_attributes = True
