from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserOut)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if user_data.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="Role must be 'teacher' or 'student'")
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = auth.hash_password(user_data.password)
    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pw,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Auto-create cognitive profile for students
    if new_user.role == "student":
        profile = models.CognitiveProfile(student_id=new_user.id)
        db.add(profile)
        db.commit()
    return new_user


@router.post("/login", response_model=schemas.TokenResponse)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user:
         raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Simple fix: if password was hashed with passlib (from before), it might start with $2b$
    # but verify_password expects bytes. Let's make sure we handle the verification safely.
    try:
        if not auth.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception as e:
         # Fallback for old passwords or format mismatch
         raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token with user ID and role
    token = auth.create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        name=user.name
    )


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
