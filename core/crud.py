from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from .models import (
    Student, StudyGroup, Participant, Lesson, LessonColumn, Result,
    Event, EventParticipant, Olympiad, OlympiadResult,
    SessionLocal, SubjectAreaEnum, ProblemTypeEnum, EventTypeEnum,
    OlympiadLevelEnum, AwardEnum
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_all_students(db: Session) -> List[Student]:
    return db.query(Student).order_by(Student.last_name, Student.first_name).all()

def get_all_groups(db: Session) -> List[StudyGroup]:
    return db.query(StudyGroup).order_by(StudyGroup.group_name).all()

def create_group(db: Session, group_name: str, description: Optional[str] = None, event_id: Optional[int] = None) -> StudyGroup:
    new_group = StudyGroup(group_name=group_name, description=description, event_id=event_id)
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

def get_groups_for_student(db: Session, student_id: int) -> List[StudyGroup]:
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


def create_event(db: Session, event_name: str, event_type: EventTypeEnum, description: Optional[str] = None, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None, organizer: Optional[str] = None) -> Event:
    new_event = Event(
        event_name=event_name,
        event_type=event_type,
        description=description,
        start_date=start_date,
        end_date=end_date,
        organizer=organizer
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

def get_event_by_id(db: Session, event_id: int) -> Optional[Event]:
    return db.query(Event).filter(Event.event_id == event_id).first()

def get_all_events(db: Session) -> List[Event]:
    return db.query(Event).order_by(Event.event_name).all()

def update_event(db: Session, event_id: int, event_name: Optional[str] = None, event_type: Optional[EventTypeEnum] = None, description: Optional[str] = None, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None, organizer: Optional[str] = None) -> Optional[Event]:
    event = get_event_by_id(db, event_id)
    if event:
        if event_name is not None:
            event.event_name = event_name
        if event_type is not None:
            event.event_type = event_type
        if description is not None:
            event.description = description
        if start_date is not None:
            event.start_date = start_date
        if end_date is not None:
            event.end_date = end_date
        if organizer is not None:
            event.organizer = organizer
        db.commit()
        db.refresh(event)
    return event

def delete_event(db: Session, event_id: int) -> bool:
    event = get_event_by_id(db, event_id)
    if event:
        db.delete(event)
        db.commit()
        return True
    return False

def add_student_to_event(db: Session, student_id: int, event_id: int, role: Optional[str] = "Ученик") -> Optional[EventParticipant]:
    existing = db.query(EventParticipant).filter(EventParticipant.student_id == student_id, EventParticipant.event_id == event_id).first()
    if not existing:
        participation = EventParticipant(student_id=student_id, event_id=event_id, role=role)
        db.add(participation)
        db.commit()
        db.refresh(participation)
        return participation
    return existing

def remove_student_from_event(db: Session, student_id: int, event_id: int) -> bool:
    participation = db.query(EventParticipant).filter(EventParticipant.student_id == student_id, EventParticipant.event_id == event_id).first()
    if participation:
        db.delete(participation)
        db.commit()
        return True
    return False

def get_students_in_event(db: Session, event_id: int) -> List[Student]:
    return db.query(Student).join(EventParticipant).filter(EventParticipant.event_id == event_id).order_by(Student.last_name, Student.first_name).all()

def get_events_for_student(db: Session, student_id: int) -> List[Event]:
    return db.query(Event).join(EventParticipant).filter(EventParticipant.student_id == student_id).all()

def get_groups_for_event(db: Session, event_id: int) -> List[StudyGroup]:
    return db.query(StudyGroup).filter(StudyGroup.event_id == event_id).order_by(StudyGroup.group_name).all()


def create_olympiad(db: Session, olympiad_name: str, olympiad_date: datetime.date, level: OlympiadLevelEnum, subject: str, organizer: Optional[str] = None) -> Olympiad:
    new_olympiad = Olympiad(
        olympiad_name=olympiad_name,
        olympiad_date=olympiad_date,
        olympiad_level=level,
        subject=subject,
        organizer=organizer
    )
    db.add(new_olympiad)
    db.commit()
    db.refresh(new_olympiad)
    return new_olympiad

def get_olympiad_by_id(db: Session, olympiad_id: int) -> Optional[Olympiad]:
    return db.query(Olympiad).filter(Olympiad.olympiad_id == olympiad_id).first()

def get_all_olympiads(db: Session, subject_filter: Optional[str] = None) -> List[Olympiad]:
    query = db.query(Olympiad)
    if subject_filter:
        query = query.filter(Olympiad.subject == subject_filter)
    return query.order_by(Olympiad.olympiad_date.desc(), Olympiad.olympiad_name).all()

def update_olympiad(db: Session, olympiad_id: int, olympiad_name: Optional[str] = None, olympiad_date: Optional[datetime.date] = None, level: Optional[OlympiadLevelEnum] = None, subject: Optional[str] = None, organizer: Optional[str] = None) -> Optional[Olympiad]:
    olympiad = get_olympiad_by_id(db, olympiad_id)
    if olympiad:
        if olympiad_name is not None:
            olympiad.olympiad_name = olympiad_name
        if olympiad_date is not None:
            olympiad.olympiad_date = olympiad_date
        if level is not None:
            olympiad.olympiad_level = level
        if subject is not None:
            olympiad.subject = subject
        if organizer is not None:
            olympiad.organizer = organizer
        db.commit()
        db.refresh(olympiad)
    return olympiad

def delete_olympiad(db: Session, olympiad_id: int) -> bool:
    olympiad = get_olympiad_by_id(db, olympiad_id)
    if olympiad:
        db.delete(olympiad)
        db.commit()
        return True
    return False

def add_olympiad_result(db: Session, student_id: int, olympiad_id: int, award: AwardEnum, score: Optional[float] = None, details: Optional[str] = None, result_document_link: Optional[str] = None) -> Optional[OlympiadResult]:
    existing = db.query(OlympiadResult).filter(
        OlympiadResult.student_id == student_id,
        OlympiadResult.olympiad_id == olympiad_id,
        OlympiadResult.details == details
    ).first()
    if not existing:
        result = OlympiadResult(
            student_id=student_id,
            olympiad_id=olympiad_id,
            award=award,
            score=score,
            details=details,
            result_document_link=result_document_link
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    return existing

def update_olympiad_result(db: Session, olympiad_result_id: int, award: Optional[AwardEnum] = None, score: Optional[float] = None, details: Optional[str] = None, result_document_link: Optional[str] = None) -> Optional[OlympiadResult]:
    result = db.query(OlympiadResult).filter(OlympiadResult.olympiad_result_id == olympiad_result_id).first()
    if result:
        if award is not None:
            result.award = award
        if score is not None:
            result.score = score
        if details is not None:
            result.details = details
        if result_document_link is not None:
            result.result_document_link = result_document_link
        db.commit()
        db.refresh(result)
    return result

def delete_olympiad_result(db: Session, olympiad_result_id: int) -> bool:
    result = db.query(OlympiadResult).filter(OlympiadResult.olympiad_result_id == olympiad_result_id).first()
    if result:
        db.delete(result)
        db.commit()
        return True
    return False

def get_olympiad_results_for_student(db: Session, student_id: int, olympiad_id: Optional[int] = None) -> List[OlympiadResult]:
    query = db.query(OlympiadResult).filter(OlympiadResult.student_id == student_id)
    if olympiad_id:
        query = query.filter(OlympiadResult.olympiad_id == olympiad_id)
    return query.join(Olympiad).order_by(Olympiad.olympiad_date.desc()).all()

def get_olympiad_results_for_olympiad(db: Session, olympiad_id: int) -> List[OlympiadResult]:
    return db.query(OlympiadResult).filter(OlympiadResult.olympiad_id == olympiad_id).join(Student).order_by(Student.last_name, Student.first_name).all()