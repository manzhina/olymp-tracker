import streamlit as st
from sqlalchemy.orm import Session
import pandas as pd
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core import crud
from core.crud import get_db
from core.models import EventTypeEnum, Student
st.set_page_config(layout="wide")
st.title("🎉 Мероприятия")

db_session_generator = get_db()
db: Session = next(db_session_generator)

try:
    if 'selected_event_id' not in st.session_state:
        st.session_state.selected_event_id = None
    if 'add_participant_mode' not in st.session_state:
        st.session_state.add_participant_mode = "Выбрать существующего"


    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Список Мероприятий")
        events = crud.get_all_events(db)
        if not events:
            st.info("Пока нет ни одного мероприятия.")
        else:
            event_names = [f"{event.event_name} ({event.event_type.value})" for event in events]
            
            current_selected_event_index = None
            if st.session_state.selected_event_id:
                try:
                    selected_event_obj = next(e for e in events if e.event_id == st.session_state.selected_event_id)
                    current_selected_event_index = event_names.index(f"{selected_event_obj.event_name} ({selected_event_obj.event_type.value})")
                except (StopIteration, ValueError):
                    current_selected_event_index = 0
            
            selected_event_name_display = st.radio(
                "Выберите мероприятие для просмотра деталей:",
                options=event_names,
                index=current_selected_event_index if current_selected_event_index is not None else 0,
                key="event_selector_radio"
            )
            if selected_event_name_display:
                st.session_state.selected_event_id = events[event_names.index(selected_event_name_display)].event_id


        with st.expander("➕ Создать новое мероприятие", expanded=False):
            with st.form("new_event_form", clear_on_submit=True):
                event_name = st.text_input("Название мероприятия*")
                event_type_value = st.selectbox(
                    "Тип мероприятия*",
                    options=[et.value for et in EventTypeEnum],
                    format_func=lambda x: x
                )
                event_desc = st.text_area("Описание")
                event_start_date = st.date_input("Дата начала", value=None)
                event_end_date = st.date_input("Дата окончания", value=None)
                event_organizer = st.text_input("Организатор")
                submitted_event = st.form_submit_button("Создать мероприятие")

                if submitted_event:
                    if not event_name or not event_type_value:
                        st.warning("Название и тип мероприятия обязательны.")
                    else:
                        try:
                            event_type_enum = EventTypeEnum(event_type_value)
                            created_event = crud.create_event(
                                db,
                                event_name=event_name,
                                event_type=event_type_enum,
                                description=event_desc,
                                start_date=event_start_date,
                                end_date=event_end_date,
                                organizer=event_organizer
                            )
                            st.success(f"Мероприятие '{created_event.event_name}' успешно создано!")
                            st.session_state.selected_event_id = created_event.event_id
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed: Events.event_name" in str(e):
                                st.error(f"Ошибка: Мероприятие с названием '{event_name}' уже существует.")
                            else:
                                st.error(f"Ошибка при создании мероприятия: {e}")
                                st.exception(e)
    
    with col2:
        if st.session_state.selected_event_id:
            event = crud.get_event_by_id(db, st.session_state.selected_event_id)
            if event:
                st.header(f"Детали мероприятия: {event.event_name}")
                st.markdown(f"**Тип:** {event.event_type.value}")
                if event.start_date:
                    st.markdown(f"**Дата начала:** {event.start_date.strftime('%d.%m.%Y')}")
                if event.end_date:
                    st.markdown(f"**Дата окончания:** {event.end_date.strftime('%d.%m.%Y')}")
                if event.organizer:
                    st.markdown(f"**Организатор:** {event.organizer}")
                if event.description:
                    st.markdown(f"**Описание:** {event.description}")
                
                st.divider()
                st.subheader("Учебные группы в рамках мероприятия")
                groups_in_event = crud.get_groups_for_event(db, event.event_id)
                if groups_in_event:
                    group_data = [{"ID": g.group_id, "Название": g.group_name, "Описание": g.description or "-"} for g in groups_in_event]
                    st.dataframe(pd.DataFrame(group_data).set_index("ID"), use_container_width=True)
                else:
                    st.info("К этому мероприятию пока не привязано ни одной учебной группы.")
                
                st.divider()
                st.subheader("Участники мероприятия")
                participants_in_event_objects = crud.get_students_in_event(db, event.event_id)
                participant_ids_in_event = [p.student_id for p in participants_in_event_objects]

                if participants_in_event_objects:
                    participant_data = [{"ID": p.student_id, "Фамилия": p.last_name, "Имя": p.first_name, "Школа": p.school_name or "-"} for p in participants_in_event_objects]
                    st.dataframe(pd.DataFrame(participant_data).set_index("ID"), use_container_width=True)

                    with st.form(f"remove_participant_form_{event.event_id}"):
                        student_to_remove_options = {f"{s.last_name} {s.first_name} (ID: {s.student_id})": s.student_id for s in participants_in_event_objects}
                        selected_student_to_remove_label = st.selectbox("Удалить участника из мероприятия:", options=list(student_to_remove_options.keys()))
                        submitted_remove_participant = st.form_submit_button("Удалить участника")
                        if submitted_remove_participant and selected_student_to_remove_label:
                            student_id_to_remove = student_to_remove_options[selected_student_to_remove_label]
                            try:
                                crud.remove_student_from_event(db, student_id_to_remove, event.event_id)
                                st.success(f"Участник '{selected_student_to_remove_label}' удален с мероприятия.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при удалении участника: {e}")
                else:
                    st.info("На этом мероприятии пока нет зарегистрированных участников.")

                st.divider()
                st.subheader("👤 Добавить/зарегистрировать участника на мероприятие")
                
                unique_radio_key = f"add_mode_radio_{event.event_id}"
                
                current_mode_index = 0
                if st.session_state.get(f"add_participant_mode_{event.event_id}") == "Создать нового и добавить":
                    current_mode_index = 1

                add_mode = st.radio(
                    "Выберите способ добавления:",
                    ("Выбрать существующего", "Создать нового и добавить"),
                    index=current_mode_index,
                    key=unique_radio_key,
                    on_change=lambda: st.session_state.update({f"add_participant_mode_{event.event_id}": st.session_state[unique_radio_key]})
                )
                st.session_state.add_participant_mode = st.session_state.get(f"add_participant_mode_{event.event_id}", "Выбрать существующего")


                with st.form(f"add_participant_form_{event.event_id}", clear_on_submit=True):
                    student_id_to_add = None
                    
                    if st.session_state.add_participant_mode == "Выбрать существующего":
                        st.caption("Добавление существующего ученика из базы данных.")
                        all_students = crud.get_all_students(db)
                        available_students_for_event = [s for s in all_students if s.student_id not in participant_ids_in_event]
                        
                        student_options = {f"{s.last_name} {s.first_name} (ID: {s.student_id})": s.student_id for s in available_students_for_event}
                        
                        if student_options:
                            selected_student_label = st.selectbox(
                                "Выберите ученика*:", 
                                options=[""] + list(student_options.keys()),
                                key=f"select_existing_student_{event.event_id}"
                                )
                            if selected_student_label:
                                student_id_to_add = student_options.get(selected_student_label)
                        else:
                            st.info("Все существующие ученики уже являются участниками этого мероприятия, или в базе нет учеников, которых можно добавить.")
                    
                    elif st.session_state.add_participant_mode == "Создать нового и добавить":
                        st.caption("Создание новой записи об ученике и добавление его на мероприятие.")
                        s_last_name = st.text_input("Фамилия нового ученика*", key=f"new_s_lname_{event.event_id}")
                        s_first_name = st.text_input("Имя нового ученика*", key=f"new_s_fname_{event.event_id}")
                        s_school = st.text_input("Школа нового ученика (опционально)", key=f"new_s_school_{event.event_id}")
                    
                    participant_role = st.text_input("Роль на мероприятии (опционально)", value="Ученик", key=f"participant_role_{event.event_id}")
                    submitted_add_participant = st.form_submit_button("Подтвердить и добавить участника")

                    if submitted_add_participant:
                        final_student_id = None
                        student_display_name = ""

                        if st.session_state.add_participant_mode == "Выбрать существующего":
                            if not student_id_to_add:
                                st.warning("Пожалуйста, выберите ученика из списка.")
                            else:
                                final_student_id = student_id_to_add
                                student_obj = crud.get_student_by_id(db, final_student_id)
                                if student_obj:
                                    student_display_name = f"{student_obj.last_name} {student_obj.first_name}"

                        elif st.session_state.add_participant_mode == "Создать нового и добавить":
                            if not s_last_name or not s_first_name:
                                st.warning("Фамилия и Имя для нового ученика обязательны.")
                            else:
                                try:
                                    existing_student = db.query(Student).filter(
                                        Student.first_name == s_first_name,
                                        Student.last_name == s_last_name,
                                        Student.school_name == (s_school if s_school else None)
                                    ).first()

                                    if existing_student:
                                        st.info(f"Найден существующий ученик: {existing_student.last_name} {existing_student.first_name} (Школа: {existing_student.school_name or 'не указана'}). Он будет добавлен на мероприятие.")
                                        final_student_id = existing_student.student_id
                                        student_display_name = f"{existing_student.last_name} {existing_student.first_name}"
                                        if existing_student.student_id in participant_ids_in_event:
                                            st.warning(f"Ученик '{student_display_name}' уже является участником этого мероприятия.")
                                            final_student_id = None
                                    else:
                                        new_student = crud.create_student(
                                            db, 
                                            first_name=s_first_name, 
                                            last_name=s_last_name, 
                                            school_name=s_school if s_school else None
                                        )
                                        st.success(f"Создан новый ученик: {new_student.last_name} {new_student.first_name} (ID: {new_student.student_id}).")
                                        final_student_id = new_student.student_id
                                        student_display_name = f"{new_student.last_name} {new_student.first_name}"
                                
                                except Exception as e:
                                    if "UNIQUE constraint failed: Students.first_name, Students.last_name, Students.school_name" in str(e):
                                        st.error(f"Ошибка: Ученик {s_last_name} {s_first_name} из школы '{s_school or 'не указана'}' уже существует в базе. Пожалуйста, используйте опцию 'Выбрать существующего'.")
                                    else:
                                        st.error(f"Ошибка при создании ученика: {e}")
                                        st.exception(e)
                        
                        if final_student_id:
                            try:
                                crud.add_student_to_event(db, student_id=final_student_id, event_id=event.event_id, role=participant_role)
                                st.success(f"Ученик '{student_display_name}' успешно добавлен на мероприятие '{event.event_name}' с ролью '{participant_role}'.")
                                st.session_state[f"add_participant_mode_{event.event_id}"] = "Выбрать существующего"
                                st.session_state.add_participant_mode = "Выбрать существующего" # Общий сброс
                                st.rerun()
                            except Exception as e:
                                if "UNIQUE constraint failed: EventParticipants.student_id, EventParticipants.event_id" in str(e):
                                     st.warning(f"Ученик '{student_display_name}' уже является участником этого мероприятия.")
                                else:
                                    st.error(f"Ошибка при добавлении участника на мероприятие: {e}")
                                    st.exception(e)

                st.divider()
                st.subheader("Статистика (базовая)")
                st.write(f"Общее количество участников: {len(participants_in_event_objects)}")
                st.write(f"Количество учебных групп: {len(groups_in_event)}")

            else:
                st.error("Мероприятие не найдено или было удалено.")
                st.session_state.selected_event_id = None
        else:
            st.info("Выберите мероприятие из списка слева для просмотра деталей.")

finally:
    if 'db' in locals() and db:
        db.close()