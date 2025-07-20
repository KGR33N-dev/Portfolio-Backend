from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from decouple import config

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, User as UserSchema, APIResponse

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = config('SECRET_KEY', default='your-secret-key')
ALGORITHM = config('ALGORITHM', default='HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES', default=30))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Rejestracja nowego użytkownika (funkcjonalność przyszłościowa)"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik o tej nazwie lub emailu już istnieje"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        bio=user_data.bio,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return APIResponse(
        success=True,
        message="Użytkownik został utworzony pomyślnie",
        data={"user_id": new_user.id, "username": new_user.username}
    )

@router.post("/login", response_model=APIResponse)
async def login_user(username: str, password: str, db: Session = Depends(get_db)):
    """Logowanie użytkownika (funkcjonalność przyszłościowa)"""
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowe dane logowania",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto użytkownika jest nieaktywne"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return APIResponse(
        success=True,
        message="Zalogowano pomyślnie",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    )

@router.get("/me", response_model=UserSchema)
async def get_current_user(db: Session = Depends(get_db)):
    """Pobierz dane aktualnego użytkownika (funkcjonalność przyszłościowa)"""
    # TODO: Implement JWT token verification
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Ta funkcjonalność będzie dostępna w przyszłości"
    )
