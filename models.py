from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database import Base


# ---------- UŻYTKOWNICY ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    # relacje
    tasks = relationship("Task", back_populates="owner", cascade="all, delete")
    subjects = relationship("Subject", back_populates="owner", cascade="all, delete")


# ---------- PRZEDMIOTY ----------
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete")


# ---------- ZADANIA ----------
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(150), nullable=False)
    priority = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)

    owner = relationship("User", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")
