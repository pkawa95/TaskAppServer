from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

# --- KONFIGURACJA JWT ---
SECRET_KEY = "supersekretnyklucz"  # 🔒 możesz podmienić na bezpieczniejszy (np. z os.getenv)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

# --- KONFIGURACJA HASEŁ ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- SESJA DB ---
def get_db():
    """Zwraca połączenie z bazą danych"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- FUNKCJE HASEŁ ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikuje hasło użytkownika"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hashuje hasło z walidacją długości (bcrypt limit 72 bajty)"""
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Hasło jest za długie (maksymalnie 72 znaki)."
        )
    return pwd_context.hash(password)


# --- JWT TOKENY ---
def create_access_token(data: dict) -> str:
    """Tworzy token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- UŻYTKOWNICY ---
def get_user_by_username(db: Session, username: str):
    """Pobiera użytkownika po nazwie"""
    return db.query(User).filter(User.username == username).first()


# --- AUTORYZACJA ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Sprawdza token JWT i zwraca aktualnego użytkownika"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Niepoprawny token uwierzytelniający",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
