from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models import User, Task
from schemas import UserCreate, TaskCreate, TaskOut, TaskUpdate
from auth import get_db, hash_password, verify_password, create_access_token, get_current_user

# Tworzenie tabel (jeśli nie istnieją)
Base.metadata.create_all(bind=engine)

# Konfiguracja FastAPI
app = FastAPI(
    title="Mini Task API",
    description="API do zarządzania zadaniami (PWA / FastAPI / JWT)",
    version="1.0.2",
    root_path="/tasksapi"
)

# --- CORS ---
origins = [
    "http://127.0.0.1:5500",       # lokalne testy (VS Code Live Server)
    "http://localhost:5500",       # alternatywa
    "https://pkawa95.github.io",   # Twój frontend (GitHub Pages)
    "https://api.pkportfolio.pl",  # domena API
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- REJESTRACJA ----------
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Hasło jest zbyt długie (max 72 znaki).")

    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Użytkownik już istnieje")

    new_user = User(username=user.username, password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Zarejestrowano pomyślnie"}

# ---------- LOGOWANIE ----------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Błędny login lub hasło")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ---------- TASKS ----------
@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == user.id).all()

@app.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_task = Task(**task.dict(), owner_id=user.id)
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
