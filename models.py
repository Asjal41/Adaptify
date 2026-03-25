from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "teacher" or "student"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cognitive_profile = relationship("CognitiveProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")
    materials = relationship("CourseMaterial", back_populates="teacher")
    assignments = relationship("Assignment", back_populates="student", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="student", cascade="all, delete-orphan")


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    overall_iq = Column(Float, default=0.0)
    logical_score = Column(Float, default=0.0)
    memory_score = Column(Float, default=0.0)
    pattern_score = Column(Float, default=0.0)
    problem_solving_score = Column(Float, default=0.0)
    level = Column(String(20), default="beginner")  # beginner | intermediate | advanced
    interests = Column(Text, nullable=True)  # Comma-separated interests (e.g. "football, music")
    completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("User", back_populates="cognitive_profile")


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User", back_populates="materials")
    assignments = relationship("Assignment", back_populates="material", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("course_materials.id"), nullable=True)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(30), default="intermediate")
    content_json = Column(Text, nullable=True)   # JSON string of generated assignment
    submitted = Column(Boolean, default=False)
    submission_text = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    grade = Column(Float, nullable=True)     # 0-100 or scale
    feedback = Column(Text, nullable=True)   # Agent or teacher feedback

    student = relationship("User", back_populates="assignments")
    material = relationship("CourseMaterial", back_populates="assignments")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="chat_logs")

# Add backref to User for convenient access
# We need to update User to include chat_logs relationship
User.chat_logs = relationship("ChatLog", back_populates="student", order_by="ChatLog.timestamp")
