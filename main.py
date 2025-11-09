from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from database import Base, engine
from models import User, Task, Subject
from schemas import (
    UserCreate,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate
)
from auth import get_db, hash_password, verify_password, create_access_token, get_current_user

# --- Tworzenie tabel ---
Base.metadata.create_all(bind=engine)

# --- Konfiguracja FastAPI ---
app = FastAPI(
    title="Student Task API",
    description="Rozszerzone API do zarządzania zadaniami i przedmiotami (PWA / FastAPI / JWT)",
    version="2.0.1",
    root_path="/tasksapi"
)

# --- CORS ---
origins = [
    "https://pkawa95.github.io",
    "https://pkawa95.github.io/TaskApp",
    "https://api.pkportfolio.pl",
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ---------- REJESTRACJA ----------
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Walidacja pól
    if not all([user.first_name, user.last_name, user.email, user.password, user.confirm_password]):
        raise HTTPException(status_code=400, detail="Wszystkie pola są wymagane.")

    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Hasła nie są identyczne.")

    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Hasło jest zbyt długie (max 72 znaki).")

    existing = db.query(User).filter(User.email == user.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Użytkownik z tym adresem email już istnieje.")

    new_user = User(
        first_name=user.first_name.strip(),
        last_name=user.last_name.strip(),
        email=user.email.strip().lower(),
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Rejestracja zakończona sukcesem"}

# ---------- LOGOWANIE ----------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Błędny email lub hasło")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# ---------- WHOAMI ----------
@app.get("/whoami")
def whoami(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email
    }

# ---------- WYLOGOWANIE ----------
@app.post("/logout")
def logout():
    return {"message": "Wylogowano pomyślnie — usuń token po stronie klienta."}

# ---------- SUBJECTS ----------
@app.get("/subjects", response_model=list[SubjectOut])
def get_subjects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Subject).filter(Subject.owner_id == user.id).all()

@app.post("/subjects", response_model=SubjectOut)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not subject.name.strip():
        raise HTTPException(status_code=400, detail="Nazwa przedmiotu nie może być pusta.")

    new_subject = Subject(name=subject.name.strip(), description=subject.description, owner_id=user.id)
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return new_subject

@app.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, subject: SubjectUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_subject = db.query(Subject).filter(Subject.id == subject_id, Subject.owner_id == user.id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Nie znaleziono przedmiotu")

    for key, value in subject.dict(exclude_unset=True).items():
        setattr(db_subject, key, value)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_subject = db.query(Subject).filter(Subject.id == subject_id, Subject.owner_id == user.id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Nie znaleziono przedmiotu")

    db.delete(db_subject)
    db.commit()
    return {"message": "Usunięto przedmiot"}

# ---------- TASKS ----------
@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == user.id).all()

@app.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Sprawdzenie czy podany subject_id istnieje (jeśli został przekazany)
    if task.subject_id:
        subject_exists = db.query(Subject).filter(
            Subject.id == task.subject_id,
            Subject.owner_id == user.id
        ).first()
        if not subject_exists:
            raise HTTPException(status_code=400, detail="Nieprawidłowy ID przedmiotu.")

    new_task = Task(
        title=task.title.strip(),
        priority=task.priority,
        due_date=task.due_date,
        completed=False,
        owner_id=user.id,
        subject_id=task.subject_id,
        created_at=datetime.utcnow()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")

    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")

    db.delete(db_task)
    db.commit()
    return {"message": "Usunięto zadanie"}

# ---------- HEALTH ----------
@app.get("/health")
def health_check():
    return {"status": "ok"}
