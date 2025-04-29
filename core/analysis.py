from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Dict, List, Tuple
import pandas as pd
from . import crud
from .models import Lesson, LessonColumn, Result

def calculate_problem_ratings(db: Session, lesson_id: int) -> Dict[int, int]:
    lesson = crud.get_lesson_by_id(db, lesson_id)
    if not lesson:
        return {}

    group_id = lesson.group_id
    students_in_group = crud.get_students_in_group(db, group_id)
    num_participants = len(students_in_group)
    if num_participants == 0:
        return {}

    columns = crud.get_columns_for_lesson(db, lesson_id)
    if not columns:
        return {}

    results = crud.get_results_for_lesson(db, lesson_id)

    solved_counts = {}
    for res in results:
        solved_counts[res.column_id] = solved_counts.get(res.column_id, 0) + 1

    problem_ratings = {}
    for col in columns:
        solved_count = solved_counts.get(col.column_id, 0)
        rating = (num_participants - solved_count) + 1
        problem_ratings[col.column_id] = rating

    return problem_ratings

def calculate_student_lesson_score(db: Session, student_id: int, lesson_id: int, problem_ratings: Dict[int, int]) -> int:
    results = db.query(Result).filter(
        Result.student_id == student_id,
        Result.lesson_id == lesson_id
    ).all()
    score = sum(problem_ratings.get(res.column_id, 0) for res in results)
    return score

def calculate_student_lesson_solved_count(db: Session, student_id: int, lesson_id: int) -> int:
    """Рассчитывает количество задач, решенных студентом на занятии."""
    count = db.query(func.count(Result.result_id)).filter(
        Result.student_id == student_id,
        Result.lesson_id == lesson_id
    ).scalar()
    return count or 0

def calculate_student_total_score_in_group(db: Session, student_id: int, group_id: int) -> int:
    total_score = 0
    lessons = crud.get_lessons_for_group(db, group_id)
    for lesson in lessons:
        problem_ratings = calculate_problem_ratings(db, lesson.lesson_id)
        if problem_ratings:
            lesson_score = calculate_student_lesson_score(db, student_id, lesson.lesson_id, problem_ratings)
            total_score += lesson_score
    return total_score

def calculate_student_total_solved_in_group(db: Session, student_id: int, group_id: int) -> int:
    count = db.query(func.count(Result.result_id)).join(Lesson).filter(
        Result.student_id == student_id,
        Lesson.group_id == group_id
    ).scalar()
    return count or 0

def prepare_conduit_dataframe(db: Session, lesson_id: int) -> Tuple[pd.DataFrame, Dict[int, int]]:
    df_empty = pd.DataFrame()
    empty_ratings = {}

    lesson = crud.get_lesson_by_id(db, lesson_id)
    if not lesson:
        return df_empty, empty_ratings

    students = crud.get_students_in_group(db, lesson.group_id)
    columns = crud.get_columns_for_lesson(db, lesson_id)
    results = crud.get_results_for_lesson(db, lesson_id)

    if not students or not columns:
         return df_empty, empty_ratings

    problem_ratings = calculate_problem_ratings(db, lesson_id)

    student_map = {s.student_id: f"{s.last_name} {s.first_name}" for s in students}
    column_map = {c.column_id: c.column_label for c in columns}
    column_order = [c.column_label for c in columns]

    df = pd.DataFrame(
        index=[student_map[s.student_id] for s in students],
        columns=column_order
    )
    df = df.fillna(False)

    solved_map = {}
    for res in results:
        if res.student_id not in solved_map:
            solved_map[res.student_id] = set()
        solved_map[res.student_id].add(res.column_id)

    for s in students:
        student_name = student_map[s.student_id]
        solved_cols_ids = solved_map.get(s.student_id, set())
        for col in columns:
            if col.column_id in solved_cols_ids:
                 df.loc[student_name, col.column_label] = True

    lesson_scores = {}
    lesson_solved_counts = {}
    for s in students:
        student_name = student_map[s.student_id]
        lesson_scores[student_name] = calculate_student_lesson_score(db, s.student_id, lesson_id, problem_ratings)
        lesson_solved_counts[student_name] = calculate_student_lesson_solved_count(db, s.student_id, lesson_id)

    df['Задач решено (занятие)'] = df.index.map(lesson_solved_counts)
    df['Рейтинг (занятие)'] = df.index.map(lesson_scores)

    return df, problem_ratings

def get_discussed_column_labels(db: Session, lesson_id: int) -> List[str]:
    columns = db.query(LessonColumn).filter(
        LessonColumn.lesson_id == lesson_id,
        LessonColumn.is_discussed == True
    ).all()
    return [col.column_label for col in columns]

def get_column_label_to_id_map(db: Session, lesson_id: int) -> Dict[str, int]:
    columns = crud.get_columns_for_lesson(db, lesson_id)
    return {col.column_label: col.column_id for col in columns}

def get_student_name_to_id_map(db: Session, group_id: int) -> Dict[str, int]:
    students = crud.get_students_in_group(db, group_id)
    return {f"{s.last_name} {s.first_name}": s.student_id for s in students}