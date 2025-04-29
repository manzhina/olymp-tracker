import streamlit as st
from sqlalchemy.orm import Session
import pandas as pd
import datetime
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core import crud
from core.crud import get_db
from core.models import SubjectAreaEnum

st.set_page_config(layout="wide")
st.title("📚 Группы и Занятия")

db_session_generator = get_db()
db: Session = next(db_session_generator)

try:
    with st.expander("➕ Создать новую группу"):
        with st.form("new_group_form", clear_on_submit=True):
            new_group_name = st.text_input("Название группы*")
            new_group_desc = st.text_area("Описание")
            submitted_group = st.form_submit_button("Создать группу")
            if submitted_group:
                if not new_group_name:
                    st.warning("Название группы обязательно.")
                else:
                    try:
                        created_group = crud.create_group(db, group_name=new_group_name, description=new_group_desc)
                        st.success(f"Группа '{created_group.group_name}' успешно создана!")
                    except Exception as e:
                        if "UNIQUE constraint failed: StudyGroups.group_name" in str(e):
                            st.error(f"Ошибка: Группа с названием '{new_group_name}' уже существует.")
                        else:
                            st.error(f"Ошибка при создании группы: {e}")
                            st.exception(e)

    st.header("Существующие группы")
    groups = crud.get_all_groups(db)

    if not groups:
        st.info("Пока нет ни одной группы.")
    else:
        for group in groups:
            with st.expander(f"Группа: {group.group_name}"):
                st.caption(f"ID: {group.group_id} | Описание: {group.description or 'Нет'}")
                st.subheader("Занятия в этой группе:")
                lessons = crud.get_lessons_for_group(db, group.group_id)

                if lessons:
                    for lesson in lessons:
                        cols = st.columns([0.8, 0.2])
                        with cols[0]:
                            st.markdown(f"**{lesson.lesson_date}**: {lesson.topic} ({lesson.subject_area.value})")
                            st.caption(f"ID: {lesson.lesson_id} | Листок: {lesson.sheet_link or 'Нет ссылки'}")
                        with cols[1]:
                            conduit_page_name = "Conduit"
                            conduit_page_url = f"/{conduit_page_name}?group_id={group.group_id}&lesson_id={lesson.lesson_id}"
                            st.link_button("Открыть кондуит", url=conduit_page_url)
                        st.divider()
                else:
                    st.info("В этой группе пока нет занятий.")

                st.subheader("➕ Добавить новое занятие в группу")
                with st.form(key=f"new_lesson_form_{group.group_id}", clear_on_submit=True):
                    lesson_date = st.date_input("Дата занятия*", value=datetime.date.today())
                    lesson_topic = st.text_input("Тема занятия*")
                    lesson_subject = st.selectbox(
                        "Направленность*",
                        options=[area.value for area in SubjectAreaEnum],
                        format_func=lambda x: x
                    )
                    lesson_link = st.text_input("Ссылка на листок")
                    submitted_lesson = st.form_submit_button("Добавить занятие")

                    if submitted_lesson:
                        if not lesson_topic or not lesson_subject:
                            st.warning("Дата, тема и направленность занятия обязательны.")
                        else:
                            try:
                                subject_enum = SubjectAreaEnum(lesson_subject)
                                new_lesson = crud.create_lesson(
                                    db=db,
                                    group_id=group.group_id,
                                    lesson_date=lesson_date,
                                    topic=lesson_topic,
                                    subject_area=subject_enum,
                                    sheet_link=lesson_link
                                )
                                st.success(f"Занятие '{new_lesson.topic}' добавлено в группу '{group.group_name}'!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при добавлении занятия: {e}")
                                st.exception(e)
finally:
    if 'db' in locals() and db:
        db.close()