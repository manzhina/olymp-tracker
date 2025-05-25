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
from core.models import EventTypeEnum

st.set_page_config(layout="wide")
st.title("🎉 Мероприятия")

db_session_generator = get_db()
db: Session = next(db_session_generator)

try:
    if 'selected_event_id' not in st.session_state:
        st.session_state.selected_event_id = None

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Список Мероприятий")
        events = crud.get_all_events(db)
        if not events:
            st.info("Пока нет ни одного мероприятия.")
        else:
            event_names = [f"{event.event_name} ({event.event_type.value})" for event in events]
            selected_event_name_display = st.radio(
                "Выберите мероприятие для просмотра деталей:",
                options=event_names,
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
                participants_in_event = crud.get_students_in_event(db, event.event_id)
                if participants_in_event:
                    participant_data = [{"ID": p.student_id, "Фамилия": p.last_name, "Имя": p.first_name, "Школа": p.school_name or "-"} for p in participants_in_event]
                    st.dataframe(pd.DataFrame(participant_data).set_index("ID"), use_container_width=True)

                    with st.form(f"remove_participant_form_{event.event_id}"):
                        student_to_remove_options = {f"{s.last_name} {s.first_name}": s.student_id for s in participants_in_event}
                        student_to_remove_name = st.selectbox("Удалить участника:", options=list(student_to_remove_options.keys()))
                        submitted_remove_participant = st.form_submit_button("Удалить участника")
                        if submitted_remove_participant and student_to_remove_name:
                            student_id_to_remove = student_to_remove_options[student_to_remove_name]
                            try:
                                crud.remove_student_from_event(db, student_id_to_remove, event.event_id)
                                st.success(f"Участник '{student_to_remove_name}' удален с мероприятия.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при удалении участника: {e}")

                else:
                    st.info("На этом мероприятии пока нет зарегистрированных участников.")

                with st.form(f"add_participant_form_{event.event_id}", clear_on_submit=True):
                    st.write("Добавить существующего ученика как участника:")
                    all_students = crud.get_all_students(db)
                    student_options = {f"{s.last_name} {s.first_name} (ID: {s.student_id})": s.student_id for s in all_students if s not in participants_in_event}
                    
                    if student_options:
                        selected_student_label = st.selectbox("Выберите ученика:", options=list(student_options.keys()))
                        participant_role = st.text_input("Роль на мероприятии (опционально)", value="Ученик")
                        submitted_add_participant = st.form_submit_button("Добавить участника")

                        if submitted_add_participant and selected_student_label:
                            student_id_to_add = student_options[selected_student_label]
                            try:
                                crud.add_student_to_event(db, student_id_to_add, event.event_id, role=participant_role)
                                st.success(f"Ученик '{selected_student_label}' добавлен на мероприятие.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при добавлении участника: {e}")
                    else:
                        st.info("Все существующие ученики уже являются участниками этого мероприятия или учеников нет в базе.")

                st.divider()
                st.subheader("Статистика (базовая)")
                st.write(f"Общее количество участников: {len(participants_in_event)}")
                st.write(f"Количество учебных групп: {len(groups_in_event)}")


            else:
                st.info("Мероприятие не найдено или было удалено.")
        else:
            st.info("Выберите мероприятие из списка слева для просмотра деталей.")

finally:
    if 'db' in locals() and db:
        db.close()