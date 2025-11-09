from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    ForeignKey, Text, func
)
from sqlalchemy.orm import relationship
from database import Base


# ==============================================================
#                           UŻYTKOWNICY
# ==============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    # relacje
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="owner", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="user", cascade="all, delete-orphan")


# ==============================================================
#                           PRZEDMIOTY
# ==============================================================

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    teacher = Column(String(120), nullable=True)          # prowadzący
    color = Column(String(20), default="#38bdf8")         # kolor kapsułki / tagu
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # relacje
    owner = relationship("User", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete-orphan")


# ==============================================================
#                             ZADANIA
# ==============================================================

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)             # opcjonalny opis
    image = Column(Text, nullable=True)                   # base64 lub URL obrazka
    priority = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relacje
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)

    owner = relationship("User", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")


# ==============================================================
#                      HISTORIA AKCJI ZADAŃ
# ==============================================================

class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # np. "created", "completed", "deleted"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # relacje
    task = relationship("Task", back_populates="history")
    user = relationship("User", back_populates="history")
