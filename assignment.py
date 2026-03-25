import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from groq_client import generate_assignment

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("/generate", response_model=schemas.AssignmentOut)
def create_assignment(
    data: schemas.AssignmentGenerateRequest,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    print(f"DEBUG: Received generation request for student_id={data.student_id} topic='{data.topic}'")
    
    # Verify student
    student = db.query(models.User).filter(
        models.User.id == data.student_id, models.User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get cognitive profile
    profile = db.query(models.CognitiveProfile).filter(
        models.CognitiveProfile.student_id == student.id
    ).first()
    
    if not profile:
        # Create default profile if missing to prevent crash
        print(f"DEBUG: No profile found for student {student.id}, creating default.")
        profile = models.CognitiveProfile(
            student_id=student.id,
            overall_iq=100.0,
            level="beginner",
            interests="general",
            completed=False
        )
        # Optionally save it or just use it in memory
        # db.add(profile); db.commit() 
    
    # -------------------------------------------------------------
    # Call Context Retrieval (RAG)
    # -------------------------------------------------------------
    from vector_store import query_material
    retrieved_chunks = query_material(query=data.topic, material_id=data.material_id, n_results=5)
    context_text = "\n".join(retrieved_chunks) if retrieved_chunks else "General topic knowledge."

    # -------------------------------------------------------------
    # Call Designer Agent (Multi-Agent System)
    # -------------------------------------------------------------
    from agents import DesignerAgent
    designer = DesignerAgent()
    
    # Generate content
    assignment_json = designer.generate_assignment(
        student_name=student.name,
        topic=data.topic,
        cognitive_profile=profile,
        context_text=context_text,
        difficulty=data.difficulty or "intermediate"
    )

    # Save Assignment
    new_assignment = models.Assignment(
        student_id=student.id,
        material_id=data.material_id,
        topic=data.topic,
        difficulty=data.difficulty or "intermediate",
        content_json=json.dumps(assignment_json),
        submitted=False
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return new_assignment


@router.get("/{assignment_id}", response_model=schemas.AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    # Students can only see their own
    if user.role == "student" and assignment.student_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return assignment


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    return {"detail": "Assignment deleted"}

@router.put("/{assignment_id}", response_model=schemas.AssignmentOut)
def update_assignment(
    assignment_id: int,
    data: schemas.AssignmentUpdateRequest,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if data.topic:
        assignment.topic = data.topic
    if data.difficulty:
        assignment.difficulty = data.difficulty
    if data.content_json:
        assignment.content_json = data.content_json
    if data.grade is not None:
        assignment.grade = data.grade
    if data.feedback:
        assignment.feedback = data.feedback
        
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/", response_model=list[schemas.AssignmentOut])
def list_assignments(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    if user.role == "teacher":
        return db.query(models.Assignment).order_by(models.Assignment.generated_at.desc()).all()
    return db.query(models.Assignment).filter(
        models.Assignment.student_id == user.id
    ).order_by(models.Assignment.generated_at.desc()).all()
