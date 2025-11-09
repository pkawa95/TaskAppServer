from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import base64

from database import Base, engine
from models import User, Task, Subject, TaskHistory
from schemas import (
    UserCreate, UserOut,
    TaskCreate, TaskOut, TaskUpdate,
    SubjectCreate, SubjectOut, SubjectUpdate
)
from schemas_history import TaskHistoryOut
from auth import get_db, hash_password, verify_password, create_access_token, get_current_user

# Tworzenie tabel
Base.metadata.create_all(bind=engine)

# Konfiguracja FastAPI
app = FastAPI(
    title="Student Task API",
    description="API do zarządzania zadaniami, przedmiotami, kolorami i historią działań",
    version="2.2.0",
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

# ==============================================================
#                      FUNKCJA LOGOWANIA HISTORII
# ==============================================================

def log_history(db: Session, user_id: int, task_id: int, action: str):
    entry = TaskHistory(
        user_id=user_id,
        task_id=task_id,
        action=action,
        timestamp=datetime.utcnow()
    )
    db.add(entry)
    db.commit()


# ==============================================================
#                         UŻYTKOWNICY
# ==============================================================

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
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


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Błędny email lub hasło")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/whoami", response_model=UserOut)
def whoami(current_user: User = Depends(get_current_user)):
    return current_user


# ==============================================================
#                           PRZEDMIOTY
# ==============================================================

@app.get("/subjects", response_model=list[SubjectOut])
def get_subjects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Subject).filter(Subject.owner_id == user.id).all()


@app.post("/subjects", response_model=SubjectOut)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not subject.name.strip():
        raise HTTPException(status_code=400, detail="Nazwa przedmiotu nie może być pusta.")

    new_subject = Subject(
        name=subject.name.strip(),
        description=subject.description,
        teacher=subject.teacher.strip() if subject.teacher else None,
        color=subject.color or "#38bdf8",
        owner_id=user.id
    )
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


# ==============================================================
#                             ZADANIA
# ==============================================================

@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == user.id).all()


@app.get("/tasks/active", response_model=list[TaskOut])
def get_active_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == user.id, Task.completed == False).all()


@app.get("/tasks/completed", response_model=list[TaskOut])
def get_completed_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == user.id, Task.completed == True).all()


from datetime import datetime, date

@app.post("/tasks", response_model=TaskOut)
async def create_task(
    title: str = Form(...),
    priority: str = Form(...),
    due_date: str = Form(...),
    subject_id: int = Form(None),
    description: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # 🧩 Konwersja daty (ważne!)
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()

        image_data = None
        if image:
            image_data = base64.b64encode(await image.read()).decode("utf-8")

        new_task = Task(
            title=title.strip(),
            priority=priority,
            due_date=due_date_obj,  # ← tu przekazujemy date, nie string!
            description=description,
            image=image_data,
            completed=False,
            owner_id=user.id,
            subject_id=subject_id,
            created_at=datetime.utcnow()
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        log_history(db, user.id, new_task.id, "created")

        return new_task

    except Exception as e:
        print("❌ Błąd przy tworzeniu zadania:", e)
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    log_history(db, user.id, db_task.id, "updated")
    return db_task


@app.put("/tasks/{task_id}/done")
def mark_task_done(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")
    db_task.completed = True
    db.commit()
    log_history(db, user.id, db_task.id, "completed")
    return {"message": "Zadanie oznaczone jako ukończone"}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania")
    db.delete(db_task)
    db.commit()
    log_history(db, user.id, task_id, "deleted")
    return {"message": "Usunięto zadanie"}


# ==============================================================
#                             HISTORIA
# ==============================================================

@app.get("/history", response_model=list[TaskHistoryOut])
def get_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500)
):
    history = (
        db.query(TaskHistory)
        .filter(TaskHistory.user_id == user.id)
        .order_by(TaskHistory.timestamp.desc())
        .limit(limit)
        .all()
    )

    results = []
    for h in history:
        task = db.query(Task).filter(Task.id == h.task_id).first()
        results.append(
            TaskHistoryOut(
                task_id=h.task_id,
                task_title=task.title if task else "Usunięte zadanie",
                action=h.action,
                timestamp=h.timestamp,
                user_id=h.user_id
            )
        )
    return results


# ==============================================================
#                              HEALTH
# ==============================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.2.0"}
