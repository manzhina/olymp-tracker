import datetime
import os
import random
import sys

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


try:
    from core import crud
    from core.crud import get_db
    from core.models import (
        ProblemTypeEnum, SubjectAreaEnum, EventTypeEnum,
        OlympiadLevelEnum, AwardEnum, Event, Olympiad, Student
    )
except ImportError as e:
    print(f"Ошибка: {e}")
    sys.exit(1)


NUM_STUDENTS_TOTAL = 60
NUM_EVENTS = 3
GROUPS_PER_EVENT_MIN = 1
GROUPS_PER_EVENT_MAX = 2
NUM_INDEPENDENT_GROUPS = 2
STUDENTS_PER_GROUP_MIN = 10
STUDENTS_PER_GROUP_MAX = 20
LESSONS_PER_GROUP_MIN = 5
LESSONS_PER_GROUP_MAX = 10
COLUMNS_PER_LESSON_MIN = 4
COLUMNS_PER_LESSON_MAX = 8
SOLVED_PROBABILITY = 0.6
NUM_OLYMPIADS = 8
OLYMPIAD_PARTICIPATION_PROBABILITY = 0.25
EVENT_GENERAL_PARTICIPATION_PROBABILITY = 0.1


FIRST_NAMES = ["Александр", "Михаил", "Иван", "Дмитрий", "Сергей", "Андрей", "Алексей", "Максим", "Евгений", "Владимир",
               "Анна", "Мария", "Екатерина", "Ольга", "Наталья", "Елена", "Ирина", "Светлана", "Татьяна", "Юлия"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов", "Михайлов", "Новиков",
              "Федорова", "Морозова", "Волкова", "Алексеева", "Лебедева", "Семенова", "Егорова", "Павлова", "Козлова", "Степанова"]
SCHOOL_NAMES = [f"Школа №{i}" for i in range(1, 11)] + ["Лицей Вторая Школа", "СУНЦ МГУ", "Физтех-лицей", "Школа 179", "Школа 57"]
EVENT_ORGANIZERS = ["МЦНМО", "ФПМИ МФТИ", "Яндекс", "Сириус", "Местная Администрация"]
OLYMPIAD_SUBJECTS = ["Математика", "Информатика", "Физика"]
OLYMPIAD_NAMES_MATH = ["Всероссийская олимпиада школьников", "Московская математическая олимпиада", "Турнир Городов", "Олимпиада \"Физтех\"", "Олимпиада \"Ломоносов\"", "СПбГУ олимпиада"]
OLYMPIAD_NAMES_INF = ["Всероссийская олимпиада по информатике", "Открытая олимпиада по программированию", "Технокубок", "Innopolis Open"]


def get_random_date(start_date=datetime.date(2022, 9, 1), end_date=datetime.date.today()):
    time_between_dates = end_date - start_date
    if time_between_dates.days <= 0:
        return start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + datetime.timedelta(days=random_number_of_days)
    return random_date

def seed_data():
    print("Начинаем заполнение базы данных тестовыми данными...")
    db_session_generator = get_db()
    db: Session = next(db_session_generator)

    all_created_students_db = []
    all_created_events_db = []
    all_created_groups_db = []
    all_created_olympiads_db = []

    try:
        print("1. Создание учеников...")
        unique_students_dict = {}
        for i in range(NUM_STUDENTS_TOTAL):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            school = random.choice(SCHOOL_NAMES) if random.random() > 0.2 else None
            try:
                student = db.query(Student).filter_by(first_name=fname, last_name=lname, school_name=school).first()
                if not student:
                    student = crud.create_student(db, first_name=fname, last_name=lname, school_name=school)
                
                if student and student.student_id not in unique_students_dict:
                    unique_students_dict[student.student_id] = student
            except IntegrityError:
                db.rollback()
                student = db.query(Student).filter_by(first_name=fname, last_name=lname, school_name=school).first()
                if student and student.student_id not in unique_students_dict:
                     unique_students_dict[student.student_id] = student
            except Exception as e:
                db.rollback()
                print(f"  ! Ошибка создания/поиска студента {lname} {fname}: {e}. Пропускаем.")
        
        all_created_students_db = list(unique_students_dict.values())
        print(f"  -> Создано/найдено {len(all_created_students_db)} уникальных учеников.")


        print("\n2. Создание мероприятий...")
        for i in range(NUM_EVENTS):
            event_name = f"Мероприятие {chr(ord('А') + i)} ({random.choice(['Весна', 'Лето', 'Осень', 'Зима'])} {random.randint(2023,2024)})"
            event_type = random.choice(list(EventTypeEnum))
            start_d = get_random_date(datetime.date(2023,1,1), datetime.date(2024,6,1))
            end_d = start_d + datetime.timedelta(days=random.randint(5, 60))
            try:
                event = crud.create_event(db,
                                          event_name=event_name,
                                          event_type=event_type,
                                          description=f"Тестовое мероприятие типа '{event_type.value}'.",
                                          start_date=start_d,
                                          end_date=end_d,
                                          organizer=random.choice(EVENT_ORGANIZERS))
                all_created_events_db.append(event)
                print(f"  Создано мероприятие: {event.event_name} (ID: {event.event_id})")
            except IntegrityError:
                db.rollback()
                existing_event = db.query(Event).filter_by(event_name=event_name).first()
                if existing_event:
                    all_created_events_db.append(existing_event)
                    print(f"  Найдено существующее мероприятие: {existing_event.event_name}")
                else:
                    print(f"  ! Не удалось создать или найти мероприятие {event_name}.")
            except Exception as e:
                db.rollback()
                print(f"  ! Ошибка создания мероприятия {event_name}: {e}.")
        print(f"  -> Создано/найдено {len(all_created_events_db)} мероприятий.")


        print("\n3. Создание учебных групп...")
        group_counter_for_event_groups = {} 
        
        for event_idx, event_obj in enumerate(all_created_events_db):
            if event_obj.event_id not in group_counter_for_event_groups:
                group_counter_for_event_groups[event_obj.event_id] = 1

            num_groups_for_event = random.randint(GROUPS_PER_EVENT_MIN, GROUPS_PER_EVENT_MAX)
            event_char_code = chr(ord('A') + event_idx)

            for _ in range(num_groups_for_event):
                current_group_num_in_event = group_counter_for_event_groups[event_obj.event_id]
                group_name = f"Группа {event_char_code}-{current_group_num_in_event}"
                
                try:
                    group = crud.create_group(db, group_name=group_name, description=f"Группа для мероприятия '{event_obj.event_name}'", event_id=event_obj.event_id)
                    all_created_groups_db.append(group)
                    print(f"  Создана группа '{group.group_name}' для мероприятия '{event_obj.event_name}'.")
                    group_counter_for_event_groups[event_obj.event_id] += 1
                except IntegrityError:
                    db.rollback()
                    group_name_fallback = f"{group_name}-dup{random.randint(100,999)}"
                    print(f"  ! Имя группы '{group_name}' уже существует, пробую '{group_name_fallback}'")
                    try:
                        group = crud.create_group(db, group_name=group_name_fallback, description=f"Группа для мероприятия '{event_obj.event_name}'", event_id=event_obj.event_id)
                        all_created_groups_db.append(group)
                        print(f"  Создана группа '{group.group_name}' для мероприятия '{event_obj.event_name}'.")
                        group_counter_for_event_groups[event_obj.event_id] += 1
                    except Exception as e_fallback:
                        db.rollback()
                        print(f"  ! Ошибка создания группы {group_name_fallback}: {e_fallback}.")
                except Exception as e:
                    db.rollback()
                    print(f"  ! Ошибка создания группы {group_name}: {e}.")

        independent_group_counter = 1
        for i in range(NUM_INDEPENDENT_GROUPS):
            group_name = f"Независимая Группа {independent_group_counter}" 
            try:
                group = crud.create_group(db, group_name=group_name, description="Независимая тестовая группа.")
                all_created_groups_db.append(group)
                print(f"  Создана независимая группа: {group.group_name}")
                independent_group_counter += 1
            except IntegrityError:
                db.rollback()
                group_name_fallback = f"{group_name}-dup{random.randint(100,999)}"
                print(f"  ! Имя независимой группы '{group_name}' уже существует, пробую '{group_name_fallback}'")
                try:
                    group = crud.create_group(db, group_name=group_name_fallback, description="Независимая тестовая группа.")
                    all_created_groups_db.append(group)
                    print(f"  Создана независимая группа: {group.group_name}")
                    independent_group_counter += 1
                except Exception as e_fallback:
                    db.rollback()
                    print(f"  ! Ошибка создания независимой группы {group_name_fallback}: {e_fallback}.")
            except Exception as e:
                db.rollback()
                print(f"  ! Ошибка создания независимой группы {group_name}: {e}.")
        
        print(f"  -> Создано/найдено {len(all_created_groups_db)} учебных групп (включая привязанные и независимые).")


        print("\n4. Распределение учеников по группам и мероприятиям...")
        students_in_groups_map = {} 
        for group_obj in all_created_groups_db:
            students_in_groups_map[group_obj.group_id] = []
            num_students_in_group = random.randint(STUDENTS_PER_GROUP_MIN, STUDENTS_PER_GROUP_MAX)
            
            if not all_created_students_db:
                print("  ! Нет доступных учеников для добавления в группы.")
                break
                
            group_students_sample = random.sample(all_created_students_db, min(num_students_in_group, len(all_created_students_db)))
            
            for student_obj in group_students_sample:
                try:
                    crud.add_student_to_group(db, student_id=student_obj.student_id, group_id=group_obj.group_id)
                    if student_obj.student_id not in students_in_groups_map[group_obj.group_id]:
                         students_in_groups_map[group_obj.group_id].append(student_obj.student_id)
                    
                    if group_obj.event_id:
                        crud.add_student_to_event(db, student_id=student_obj.student_id, event_id=group_obj.event_id, role="Ученик группы")
                except Exception as e:
                    print(f"  ! Ошибка при обработке студента {student_obj.student_id} для группы {group_obj.group_id}: {e}.")
            print(f"    В группу '{group_obj.group_name}' добавлено {len(students_in_groups_map[group_obj.group_id])} учеников.")
        
        for event_obj in all_created_events_db:
            event_participants_count = 0
            current_event_participant_ids = {p.student_id for p in crud.get_students_in_event(db, event_obj.event_id)}
            for student_obj in all_created_students_db:
                if student_obj.student_id not in current_event_participant_ids and random.random() < EVENT_GENERAL_PARTICIPATION_PROBABILITY :
                    try:
                        crud.add_student_to_event(db, student_id=student_obj.student_id, event_id=event_obj.event_id, role="Участник мероприятия")
                        event_participants_count+=1
                    except Exception as e:
                        print(f"  ! Ошибка добавления студента {student_obj.student_id} как общего участника мероприятия {event_obj.event_id}: {e}.")
            if event_participants_count > 0:
                print(f"    Дополнительно добавлено {event_participants_count} общих участников на мероприятие '{event_obj.event_name}'.")


        print("\n5. Создание занятий и задач (колонок)...")
        lessons_with_cols = {} 
        for group_obj in all_created_groups_db:
            num_lessons = random.randint(LESSONS_PER_GROUP_MIN, LESSONS_PER_GROUP_MAX)
            for j in range(num_lessons):
                lesson_date = get_random_date(start_date=group_obj.start_date or datetime.date(2023,9,1), end_date=group_obj.end_date or datetime.date.today())
                subject = random.choice(list(SubjectAreaEnum))
                topic = f"Занятие {j+1} ({subject.value})"
                try:
                    lesson = crud.create_lesson(db, group_id=group_obj.group_id, lesson_date=lesson_date, topic=topic, subject_area=subject)
                except Exception as e:
                    db.rollback()
                    print(f"  ! Ошибка создания занятия '{topic}' для группы {group_obj.group_id}: {e}. Пропускаем.")
                    continue

                lessons_with_cols[lesson.lesson_id] = []
                num_columns = random.randint(COLUMNS_PER_LESSON_MIN, COLUMNS_PER_LESSON_MAX)
                for k in range(num_columns):
                    col_label = f"{k+1}"
                    if random.random() < 0.15: col_label += random.choice(['a', 'b', '+', '*'])
                    col_type = random.choice(list(ProblemTypeEnum))
                    try:
                        column = crud.add_lesson_column(db, lesson_id=lesson.lesson_id, column_label=col_label, problem_type=col_type, display_order=k)
                        lessons_with_cols[lesson.lesson_id].append(column.column_id)
                    except IntegrityError:
                        db.rollback()
                    except Exception as e:
                        db.rollback()
                        print(f"    ! Ошибка добавления колонки '{col_label}' к занятию {lesson.lesson_id}: {e}. Пропускаем.")
            if num_lessons > 0:
                 print(f"  Для группы '{group_obj.group_name}' создано {num_lessons} занятий с задачами.")


        print("\n6. Генерируем результаты по задачам на занятиях...")
        total_lesson_results_added = 0
        for group_obj in all_created_groups_db:
            group_student_ids = students_in_groups_map.get(group_obj.group_id, [])
            if not group_student_ids: continue
            
            group_lessons = crud.get_lessons_for_group(db, group_obj.group_id)
            for lesson_obj in group_lessons:
                lesson_column_ids = lessons_with_cols.get(lesson_obj.lesson_id, [])
                if not lesson_column_ids: continue

                for student_id in group_student_ids:
                    for column_id in lesson_column_ids:
                        if random.random() < SOLVED_PROBABILITY:
                            try:
                                crud.add_result(db, student_id=student_id, column_id=column_id, lesson_id=lesson_obj.lesson_id)
                                total_lesson_results_added += 1
                            except Exception as e:
                                print(f"    ! Ошибка добавления результата урока для s={student_id}, c={column_id}, l={lesson_obj.lesson_id}: {e}")
        print(f"  -> Добавлено {total_lesson_results_added} записей о результатах на уроках.")


        print("\n7. Создание Олимпиад...")
        for i in range(NUM_OLYMPIADS):
            subject = random.choice(OLYMPIAD_SUBJECTS)
            if subject == "Математика":
                name = random.choice(OLYMPIAD_NAMES_MATH) + f" {random.randint(2023,2024)}"
            elif subject == "Информатика":
                name = random.choice(OLYMPIAD_NAMES_INF) + f" {random.randint(2023,2024)}"
            else:
                name = f"Олимпиада по {subject} #{i+1} ({random.randint(2023,2024)})"
            
            date = get_random_date(datetime.date(2023,1,1), datetime.date.today())
            level = random.choice(list(OlympiadLevelEnum))
            organizer = random.choice(EVENT_ORGANIZERS) if random.random() > 0.5 else None
            try:
                olympiad = crud.create_olympiad(db, olympiad_name=name, olympiad_date=date, level=level, subject=subject, organizer=organizer)
                all_created_olympiads_db.append(olympiad)
            except IntegrityError:
                db.rollback()
                existing_olympiad = db.query(Olympiad).filter_by(olympiad_name=name, olympiad_date=date, subject=subject).first()
                if existing_olympiad:
                    all_created_olympiads_db.append(existing_olympiad)
            except Exception as e:
                db.rollback()
                print(f"  ! Ошибка создания олимпиады {name}: {e}.")
        print(f"  -> Создано/найдено {len(all_created_olympiads_db)} олимпиад.")


        print("\n8. Генерируем результаты олимпиад...")
        total_olympiad_results_added = 0
        if all_created_students_db and all_created_olympiads_db:
            for student_obj in all_created_students_db:
                num_olympiads_for_student = int(len(all_created_olympiads_db) * OLYMPIAD_PARTICIPATION_PROBABILITY * (1 + random.random()))
                if num_olympiads_for_student == 0 and random.random() < 0.1 : # Дадим шанс тем, кому не повезло
                    num_olympiads_for_student = 1
                
                if num_olympiads_for_student > 0:
                    participated_olympiads = random.sample(all_created_olympiads_db, min(num_olympiads_for_student, len(all_created_olympiads_db)))

                    for olympiad_obj in participated_olympiads:
                        award = random.choice(list(AwardEnum))
                        score = None
                        if award not in [AwardEnum.NONE, AwardEnum.PARTICIPANT]:
                            if olympiad_obj.subject == "Математика":
                                score = round(random.uniform(10, 70)/7) * 7 if random.random() > 0.3 else None 
                            else:
                                score = random.randint(20, 300) if random.random() > 0.3 else None
                        details = f"{random.randint(7,11)} класс" if random.random() > 0.6 else None
                        try:
                            crud.add_olympiad_result(db, student_id=student_obj.student_id, olympiad_id=olympiad_obj.olympiad_id,
                                                     award=award, score=score, details=details)
                            total_olympiad_results_added +=1
                        except IntegrityError:
                            db.rollback()
                        except Exception as e:
                            print(f"  ! Ошибка добавления результата олимпиады для s={student_obj.student_id}, o={olympiad_obj.olympiad_id}: {e}")
        print(f"  -> Добавлено {total_olympiad_results_added} записей о результатах олимпиад.")


        print("\nЗавершение транзакции...")
        db.commit()
        print("База данных успешно заполнена тестовыми данными!")

    except Exception as e:
        print("\n!!! Произошла ошибка во время заполнения базы данных !!!")
        print(f"Ошибка: {e}")
        print("Откатываем изменения...")
        db.rollback()
        print("Изменения отменены.")
        import traceback
        traceback.print_exc()
    finally:
        print("Закрываем сессию базы данных.")
        if db:
            db.close()


if __name__ == "__main__":
    from core.models import create_db_and_tables
    print("Проверка и создание таблиц базы данных (если не существуют)...")
    create_db_and_tables()
    print("Таблицы проверены/созданы.\n")
    
    seed_data()