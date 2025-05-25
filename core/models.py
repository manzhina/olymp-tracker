import os
import enum
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime, Boolean,
    ForeignKey, UniqueConstraint, Enum, Float
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

DATABASE_FILENAME = "olympiad_tracker.db"
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
DATABASE_URL = f"sqlite:///{os.path.join(_project_root, DATABASE_FILENAME)}"


class SubjectAreaEnum(enum.Enum):
    ALGEBRA = "Алгебра"
    GEOMETRY = "Геометрия"
    NUMBER_THEORY = "Теория Чисел"
    COMBINATORICS = "Комбинаторика"
    LOGIC = "Логика"
    OTHER = "Другое"


class ProblemTypeEnum(enum.Enum):
    REGULAR = "regular"
    BONUS = "bonus"
    ZERO = "zero"


class EventTypeEnum(enum.Enum):
    GATHERING = "Сборы"
    CIRCLE = "Кружок"
    SUMMER_SCHOOL = "Летняя школа"
    TOURNAMENT_SERIES = "Серия турниров"
    OTHER = "Другое"


class OlympiadLevelEnum(enum.Enum):
    SCHOOL = "Школьный"
    MUNICIPAL = "Муниципальный"
    REGIONAL = "Региональный"
    NATIONAL = "Всероссийский"
    INTERNATIONAL = "Международный"
    OTHER = "Другое"


class AwardEnum(enum.Enum):
    WINNER = "Победитель"
    PRIZE_1 = "Призёр I степени"
    PRIZE_2 = "Призёр II степени"
    PRIZE_3 = "Призёр III степени"
    HONORABLE_MENTION = "Похвальный отзыв"
    PARTICIPANT = "Участник"
    DIPLOMA_1 = "Диплом I степени"
    DIPLOMA_2 = "Диплом II степени"
    DIPLOMA_3 = "Диплом III степени"
    NONE = "Ничего"


class Student(Base):
    __tablename__ = "Students"

    student_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    school_name = Column(String)
    registration_date = Column(DateTime, nullable=False, server_default=func.now())

    participations = relationship("Participant", back_populates="student", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="student", cascade="all, delete-orphan")
    event_participations = relationship("EventParticipant", back_populates="student", cascade="all, delete-orphan")
    olympiad_results = relationship("OlympiadResult", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('first_name', 'last_name', 'school_name', name='uq_student_fullname_school'),
        {'sqlite_autoincrement': True}
    )


class Event(Base):
    __tablename__ = "Events"

    event_id = Column(Integer, primary_key=True)
    event_name = Column(String, nullable=False, unique=True)
    event_type = Column(Enum(EventTypeEnum), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    organizer = Column(String)

    study_groups = relationship("StudyGroup", back_populates="event")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = ({'sqlite_autoincrement': True})


class StudyGroup(Base):
    __tablename__ = "StudyGroups"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    event_id = Column(Integer, ForeignKey("Events.event_id", ondelete="SET NULL"), nullable=True)

    event = relationship("Event", back_populates="study_groups")
    participants = relationship("Participant", back_populates="study_group", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="study_group", cascade="all, delete-orphan")

    __table_args__ = ({'sqlite_autoincrement': True})


class Participant(Base):
    __tablename__ = "Participants"

    participation_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Students.student_id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("StudyGroups.group_id", ondelete="CASCADE"), nullable=False)

    student = relationship("Student", back_populates="participations")
    study_group = relationship("StudyGroup", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('student_id', 'group_id', name='uq_student_in_group'),
        {'sqlite_autoincrement': True}
    )


class EventParticipant(Base):
    __tablename__ = "EventParticipants"

    event_participation_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Students.student_id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("Events.event_id", ondelete="CASCADE"), nullable=False)
    registration_timestamp = Column(DateTime, nullable=False, server_default=func.now())
    role = Column(String, nullable=True)

    student = relationship("Student", back_populates="event_participations")
    event = relationship("Event", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('student_id', 'event_id', name='uq_student_in_event'),
        {'sqlite_autoincrement': True}
    )


class Lesson(Base):
    __tablename__ = "Lessons"

    lesson_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("StudyGroups.group_id", ondelete="CASCADE"), nullable=False)
    lesson_date = Column(Date, nullable=False)
    topic = Column(String, nullable=False)
    subject_area = Column(Enum(SubjectAreaEnum), nullable=False)
    sheet_link = Column(String)

    study_group = relationship("StudyGroup", back_populates="lessons")
    lesson_columns = relationship("LessonColumn", back_populates="lesson", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = ({'sqlite_autoincrement': True})


class LessonColumn(Base):
    __tablename__ = "LessonColumns"

    column_id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("Lessons.lesson_id", ondelete="CASCADE"), nullable=False)
    column_label = Column(String, nullable=False)
    problem_type = Column(Enum(ProblemTypeEnum), nullable=False, default=ProblemTypeEnum.REGULAR)
    display_order = Column(Integer, nullable=False)
    is_discussed = Column(Boolean, nullable=False, default=False)

    lesson = relationship("Lesson", back_populates="lesson_columns")
    results = relationship("Result", back_populates="lesson_column", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('lesson_id', 'column_label', name='uq_lesson_column_label'),
        UniqueConstraint('lesson_id', 'display_order', name='uq_lesson_column_order'),
        {'sqlite_autoincrement': True}
    )


class Result(Base):
    __tablename__ = "Results"

    result_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Students.student_id", ondelete="CASCADE"), nullable=False)
    column_id = Column(Integer, ForeignKey("LessonColumns.column_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("Lessons.lesson_id", ondelete="CASCADE"), nullable=False)
    solved_timestamp = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("Student", back_populates="results")
    lesson_column = relationship("LessonColumn", back_populates="results")
    lesson = relationship("Lesson", back_populates="results")

    __table_args__ = (
        UniqueConstraint('student_id', 'column_id', name='uq_student_solved_column'),
        {'sqlite_autoincrement': True}
    )


class Olympiad(Base):
    __tablename__ = "Olympiads"

    olympiad_id = Column(Integer, primary_key=True)
    olympiad_name = Column(String, nullable=False)
    olympiad_date = Column(Date, nullable=False)
    olympiad_level = Column(Enum(OlympiadLevelEnum), nullable=False)
    subject = Column(String, nullable=False)
    organizer = Column(String)

    results = relationship("OlympiadResult", back_populates="olympiad", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('olympiad_name', 'olympiad_date', 'subject', name='uq_olympiad_key'),
        {'sqlite_autoincrement': True}
    )


class OlympiadResult(Base):
    __tablename__ = "OlympiadResults"

    olympiad_result_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("Students.student_id", ondelete="CASCADE"), nullable=False)
    olympiad_id = Column(Integer, ForeignKey("Olympiads.olympiad_id", ondelete="CASCADE"), nullable=False)
    award = Column(Enum(AwardEnum), nullable=False)
    score = Column(Float)
    details = Column(Text)
    result_document_link = Column(String)
    submission_timestamp = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("Student", back_populates="olympiad_results")
    olympiad = relationship("Olympiad", back_populates="results")

    __table_args__ = (
        UniqueConstraint('student_id', 'olympiad_id', 'details', name='uq_student_olympiad_result_details'),
        {'sqlite_autoincrement': True}
    )


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"An error occurred during table creation: {e}")

if __name__ == "__main__":
    create_db_and_tables()