from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/submit-iq", response_model=schemas.CognitiveProfileOut)
def submit_iq(
    data: schemas.IQSubmission,
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    profile = db.query(models.CognitiveProfile).filter(
        models.CognitiveProfile.student_id == student.id
    ).first()
    if not profile:
        profile = models.CognitiveProfile(student_id=student.id)
        db.add(profile)

    profile.logical_score = data.logical_score
    profile.memory_score = data.memory_score
    profile.pattern_score = data.pattern_score
    profile.problem_solving_score = data.problem_solving_score
    if data.interests:
        profile.interests = data.interests

    # Calculate overall IQ (weighted average)
    overall = (data.logical_score * 0.3 + data.memory_score * 0.2 +
               data.pattern_score * 0.25 + data.problem_solving_score * 0.25)

    profile.overall_iq = round(overall, 1)

    # Determine level
    if overall >= 75:
        profile.level = "advanced"
    elif overall >= 45:
        profile.level = "intermediate"
    else:
        profile.level = "beginner"

    profile.completed = True
    db.commit()
    db.refresh(profile)
    return profile


from groq_client import chat_with_agent

@router.post("/chat", response_model=schemas.ChatResponse)
def chat_with_teacher_agent(
    data: schemas.ChatRequest,
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    from agents import TutorAgent # Import Tutor Agent
    
    # 1. Save User Message
    user_log = models.ChatLog(
        student_id=student.id,
        role="user",
        content=data.message
    )
    db.add(user_log)
    db.commit()

    # 2. Fetch History (Last 5 messages for quick context)
    history_logs = db.query(models.ChatLog)\
        .filter(models.ChatLog.student_id == student.id)\
        .order_by(models.ChatLog.timestamp.desc())\
        .limit(6)\
        .all()
    history = [{"role": h.role, "content": h.content} for h in reversed(history_logs)]
    context_msgs = history[:-1] # Remove current message from history

    # Fetch profile
    profile = db.query(models.CognitiveProfile).filter(
        models.CognitiveProfile.student_id == student.id
    ).first()

    assignment_context = "" # ... (existing logic for assignment context) ...

    # 3. Call Tutor Agent
    tutor = TutorAgent()
    response_text = tutor.chat(
        student_name=student.name,
        profile=profile,
        message=data.message,
        history=context_msgs,
        context=data.problem_context or "",
        assignment_context=assignment_context
    )

    # 4. Save Agent Response
    agent_log = models.ChatLog(
        student_id=student.id,
        role="assistant",
        content=response_text
    )
    db.add(agent_log)
    db.commit()
    return schemas.ChatResponse(reply=response_text)


@router.get("/chat/history", response_model=list[schemas.ChatLogOut])
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    """Retrieve chat history for the logged-in student."""
    return db.query(models.ChatLog).filter(
        models.ChatLog.student_id == student.id
    ).order_by(models.ChatLog.timestamp.asc()).limit(limit).all()


@router.get("/profile", response_model=schemas.CognitiveProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    profile = db.query(models.CognitiveProfile).filter(
        models.CognitiveProfile.student_id == student.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No cognitive profile found. Take the IQ test first.")
    return profile


@router.get("/assignments", response_model=list[schemas.AssignmentOut])
def get_my_assignments(
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    return db.query(models.Assignment).filter(
        models.Assignment.student_id == student.id
    ).order_by(models.Assignment.generated_at.desc()).all()


@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    data: schemas.AssignmentSubmitRequest,
    db: Session = Depends(get_db),
    student: models.User = Depends(auth.require_student)
):
    # Verify Assignment
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.student_id == student.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Update Submission
    assignment.submission_text = data.submission_text
    assignment.submitted = True
    
    # -------------------------------------------------------------
    # Call Grader Agent (Multi-Agent System)
    # -------------------------------------------------------------
    from agents import GraderAgent # Import our agent
    
    grader = GraderAgent()
    evaluation = grader.evaluate_submission(
        assignment.topic,
        assignment.content_json,
        data.submission_text
    )
    
    # Store Agent's Evaluation
    assignment.grade = evaluation.get("grade", 0.0)
    assignment.feedback = evaluation.get("feedback", "Automated grading pending.")
    
    db.commit()
    return {"message": "Assignment submitted and graded by AI.", "grade": assignment.grade, "feedback": assignment.feedback}
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.student_id == student.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.submitted:
        raise HTTPException(status_code=400, detail="Assignment already submitted")

    assignment.submitted = True
    assignment.submission_text = data.submission_text
    db.commit()
    return {"detail": "Assignment submitted successfully"}
