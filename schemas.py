from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List


# ==============================================================
#                       SUBJECT SCHEMAS
# ==============================================================

class SubjectBase(BaseModel):
    """Podstawowy schemat dla przedmiotów"""
    name: str
    description: Optional[str] = None
    teacher: Optional[str] = None           # nowy: prowadzący
    color: Optional[str] = "#38bdf8"        # nowy: kolor kapsułki


class SubjectCreate(SubjectBase):
    """Tworzenie nowego przedmiotu"""
    pass


class SubjectUpdate(BaseModel):
    """Aktualizacja przedmiotu"""
    name: Optional[str] = None
    description: Optional[str] = None
    teacher: Optional[str] = None
    color: Optional[str] = None


class SubjectOut(SubjectBase):
    """Zwracany przedmiot"""
    id: int

    class Config:
        from_attributes = True


# ==============================================================
#                        TASK SCHEMAS
# ==============================================================

class TaskBase(BaseModel):
    """Podstawowy schemat dla zadań"""
    title: str
    priority: str
    due_date: date
    subject_id: Optional[int] = None
    description: Optional[str] = None       # nowy: opis zadania
    image: Optional[str] = None             # nowy: base64 / URL obrazka


class TaskCreate(TaskBase):
    """Tworzenie nowego zadania"""
    pass


class TaskUpdate(BaseModel):
    """Aktualizacja zadania"""
    title: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    subject_id: Optional[int] = None
    description: Optional[str] = None
    image: Optional[str] = None


class TaskOut(TaskBase):
    """Zwracane zadanie"""
    id: int
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================
#                         USER SCHEMAS
# ==============================================================

class UserCreate(BaseModel):
    """Rejestracja użytkownika"""
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str


class UserOut(BaseModel):
    """Zwracany użytkownik"""
    id: int
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        from_attributes = True
