from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas, auth
from file_parser import parse_file
from vector_store import add_material, delete_material as vs_delete

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.post("/upload-material", response_model=schemas.CourseMaterialOut)
async def upload_material(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    print(f"DEBUG: upload_material called with file={file.filename}")
    file_bytes = await file.read()
    print(f"DEBUG: file read {len(file_bytes)} bytes")
    try:
        content_text = parse_file(file.filename, file_bytes)
        print(f"DEBUG: parsed text length={len(content_text)}")
    except ValueError as e:
        print(f"DEBUG: ValueError in parse_file: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG: Unexpected error in parse_file: {e}")
        raise e

    material = models.CourseMaterial(
        teacher_id=teacher.id,
        filename=file.filename,
        content_text=content_text
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    # Add to vector store
    add_material(material.id, content_text)
    return material


@router.get("/materials", response_model=list[schemas.CourseMaterialOut])
def get_my_materials(
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    return db.query(models.CourseMaterial).filter(
        models.CourseMaterial.teacher_id == teacher.id
    ).all()


@router.delete("/materials/{material_id}")
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    mat = db.query(models.CourseMaterial).filter(
        models.CourseMaterial.id == material_id,
        models.CourseMaterial.teacher_id == teacher.id
    ).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    vs_delete(material_id)
    db.delete(mat)
    db.commit()
    return {"detail": "Material deleted"}


@router.get("/students", response_model=list[schemas.UserOut])
def get_all_students(
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    return db.query(models.User).filter(models.User.role == "student").all()


@router.get("/students/{student_id}/analytics", response_model=schemas.StudentAnalytics)
def get_student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    student = db.query(models.User).filter(
        models.User.id == student_id, models.User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    profile = db.query(models.CognitiveProfile).filter(
        models.CognitiveProfile.student_id == student_id
    ).first()

    total = db.query(models.Assignment).filter(models.Assignment.student_id == student_id).count()
    submitted = db.query(models.Assignment).filter(
        models.Assignment.student_id == student_id,
        models.Assignment.submitted == True
    ).count()

    return schemas.StudentAnalytics(
        student=student,
        profile=profile,
        assignment_count=total,
        submitted_count=submitted
    )


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    student = db.query(models.User).filter(
        models.User.id == student_id, models.User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"detail": "Student and all associated data deleted"}


@router.get("/analytics/overview", response_model=schemas.OverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    teacher: models.User = Depends(auth.require_teacher)
):
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_teachers = db.query(models.User).filter(models.User.role == "teacher").count()
    total_assignments = db.query(models.Assignment).count()
    total_materials = db.query(models.CourseMaterial).count()
    avg_iq_result = db.query(func.avg(models.CognitiveProfile.overall_iq)).scalar()

    return schemas.OverviewStats(
        total_students=total_students,
        total_teachers=total_teachers,
        total_assignments=total_assignments,
        total_materials=total_materials,
        avg_iq=round(avg_iq_result or 0, 1)
    )
