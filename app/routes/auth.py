from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.user_store import verify_user, register_user
from app.core.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)
    department: str = Field(default="general", max_length=50)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    department: str


@router.post("/login", response_model=AuthResponse)
async def login_endpoint(payload: AuthRequest):
    user_info = verify_user(payload.username, payload.password)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = create_access_token({
        "sub": user_info["username"],
        "role": user_info["role"],
        "department": user_info["department"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user_info["username"],
        "role": user_info["role"],
        "department": user_info["department"]
    }


@router.post("/register", response_model=AuthResponse)
async def register_endpoint(payload: RegisterRequest):
    dept = payload.department.strip().lower() if payload.department else "general"
    created = register_user(payload.username, payload.password, department=dept)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    token = create_access_token({
        "sub": payload.username.strip().lower(),
        "role": "editor",
        "department": dept
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": payload.username.strip().lower(),
        "role": "editor",
        "department": dept
    }
