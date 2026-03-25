from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # "teacher" or "student"

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    name: str


# ─── Cognitive Profile ────────────────────────────────────────────────────────

class IQSubmission(BaseModel):
    logical_score: float
    memory_score: float
    pattern_score: float
    problem_solving_score: float
    interests: Optional[str] = None  # New field for user interests

class CognitiveProfileOut(BaseModel):
    id: int
    student_id: int
    overall_iq: float
    logical_score: float
    memory_score: float
    pattern_score: float
    problem_solving_score: float
    level: str
    interests: Optional[str]
    completed: bool

    class Config:
        from_attributes = True

# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    assignment_id: Optional[int] = None
    problem_context: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    reply: str



# ─── Course Material ──────────────────────────────────────────────────────────

class CourseMaterialOut(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    teacher_id: int

    class Config:
        from_attributes = True


# ─── Assignment ───────────────────────────────────────────────────────────────

class AssignmentGenerateRequest(BaseModel):
    student_id: int
    topic: str
    material_id: Optional[int] = None
    difficulty: Optional[str] = None

class AssignmentSubmitRequest(BaseModel):
    submission_text: str

class AssignmentUpdateRequest(BaseModel):
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    content_json: Optional[str] = None
    grade: Optional[float] = None
    feedback: Optional[str] = None

class AssignmentOut(BaseModel):
    id: int
    student_id: int
    material_id: Optional[int]
    topic: str
    difficulty: str
    content_json: Optional[str]
    submitted: bool
    submission_text: Optional[str]
    generated_at: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True

class ChatLogOut(BaseModel):
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True
    topic: str
    difficulty: str
    content_json: Optional[str]
    submitted: bool
    submission_text: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True

class AssignmentSubmitRequest(BaseModel):
    submission_text: str


# ─── Analytics ────────────────────────────────────────────────────────────────

class StudentAnalytics(BaseModel):
    student: UserOut
    profile: Optional[CognitiveProfileOut]
    assignment_count: int
    submitted_count: int

class OverviewStats(BaseModel):
    total_students: int
    total_teachers: int
    total_assignments: int
    total_materials: int
    avg_iq: float
