from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Student, StudyGroup, Participant, Lesson, LessonColumn, Result, SessionLocal, SubjectAreaEnum, ProblemTypeEnum

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_all_groups(db: Session) -> List[StudyGroup]:
    return db.query(StudyGroup).order_by(StudyGroup.group_name).all()

def create_group(db: Session, group_name: str, description: Optional[str] = None) -> StudyGroup:
    new_group = StudyGroup(group_name=group_name, description=description)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

def get_group_by_id(db: Session, group_id: int) -> Optional[StudyGroup]:
    return db.query(StudyGroup).filter(StudyGroup.group_id == group_id).first()

def find_students_by_name(db: Session, first_name: str, last_name: str) -> List[Student]:
    return db.query(Student).filter(Student.last_name == last_name, Student.first_name == first_name).all()

def create_student(db: Session, first_name: str, last_name: str, school_name: Optional[str] = None) -> Student:
    new_student = Student(first_name=first_name, last_name=last_name, school_name=school_name)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.student_id == student_id).first()

def add_student_to_group(db: Session, student_id: int, group_id: int) -> Optional[Participant]:
    existing = db.query(Participant).filter(Participant.student_id == student_id, Participant.group_id == group_id).first()
    if not existing:
        participation = Participant(student_id=student_id, group_id=group_id)
        db.add(participation)
        db.commit()
        db.refresh(participation)
        return participation
    return existing

def get_students_in_group(db: Session, group_id: int) -> List[Student]:
    return db.query(Student).join(Participant).filter(Participant.group_id == group_id).order_by(Student.last_name, Student.first_name).all()

def get_student_participation_history(db: Session, student_id: int) -> List[StudyGroup]:
     return db.query(StudyGroup).join(Participant).filter(Participant.student_id == student_id).all()

def create_lesson(db: Session, group_id: int, lesson_date, topic: str, subject_area: SubjectAreaEnum, sheet_link: Optional[str] = None) -> Lesson:
    lesson = Lesson(group_id=group_id, lesson_date=lesson_date, topic=topic, subject_area=subject_area, sheet_link=sheet_link)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson

def get_lessons_for_group(db: Session, group_id: int) -> List[Lesson]:
    return db.query(Lesson).filter(Lesson.group_id == group_id).order_by(Lesson.lesson_date.desc()).all()

def get_lesson_by_id(db: Session, lesson_id: int) -> Optional[Lesson]:
     return db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()

def add_lesson_column(db: Session, lesson_id: int, column_label: str, problem_type: ProblemTypeEnum, display_order: int) -> LessonColumn:
    column = LessonColumn(lesson_id=lesson_id, column_label=column_label, problem_type=problem_type, display_order=display_order)
    db.add(column)
    db.commit()
    db.refresh(column)
    return column

def get_columns_for_lesson(db: Session, lesson_id: int) -> List[LessonColumn]:
    return db.query(LessonColumn).filter(LessonColumn.lesson_id == lesson_id).order_by(LessonColumn.display_order).all()

def mark_column_discussed(db: Session, column_id: int, is_discussed: bool) -> Optional[LessonColumn]:
    column = db.query(LessonColumn).filter(LessonColumn.column_id == column_id).first()
    if column:
        column.is_discussed = is_discussed
        db.commit()
        db.refresh(column)
        return column
    return None

def get_column_by_id(db: Session, column_id: int) -> Optional[LessonColumn]:
     return db.query(LessonColumn).filter(LessonColumn.column_id == column_id).first()

def add_result(db: Session, student_id: int, column_id: int, lesson_id: int) -> Optional[Result]:
    existing = db.query(Result).filter(Result.student_id == student_id, Result.column_id == column_id).first()
    if not existing:
        result = Result(student_id=student_id, column_id=column_id, lesson_id=lesson_id)
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    return existing

def delete_result(db: Session, student_id: int, column_id: int) -> bool:
    result = db.query(Result).filter(Result.student_id == student_id, Result.column_id == column_id).first()
    if result:
        db.delete(result)
        db.commit()
        return True
    return False

def get_results_for_lesson(db: Session, lesson_id: int) -> List[Result]:
     return db.query(Result).filter(Result.lesson_id == lesson_id).all()