import streamlit as st
from sqlalchemy.orm import Session
import pandas as pd
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core import crud, analysis
from core.crud import get_db

st.set_page_config(layout="wide")
st.title("🧑‍🎓 Ученики")

db_session_generator = get_db()
db: Session = next(db_session_generator)

try:
    groups = crud.get_all_groups(db)
    group_options = {group.group_name: group.group_id for group in groups}
    selected_group_name = st.selectbox(
        "Выберите группу для просмотра учеников и добавления новых:",
        options=[""] + list(group_options.keys()),
        key="student_page_group_selector"
    )
    selected_group_id = group_options.get(selected_group_name)

    if selected_group_id:
        st.header(f"Ученики в группе: {selected_group_name}")
        students_in_group = crud.get_students_in_group(db, selected_group_id)

        if students_in_group:
            student_data = []
            prog_text = "Расчет статистики для учеников..."
            prog_bar = st.progress(0, text=prog_text)
            total_students = len(students_in_group)

            for i, s in enumerate(students_in_group):
                total_score = analysis.calculate_student_total_score_in_group(db, s.student_id, selected_group_id)
                total_solved = analysis.calculate_student_total_solved_in_group(db, s.student_id, selected_group_id)
                student_data.append({
                    "ID": s.student_id,
                    "Фамилия": s.last_name,
                    "Имя": s.first_name,
                    "Школа": s.school_name or "-",
                    "Задач решено (группа)": total_solved,
                    "Общий балл (группа)": total_score
                })
                prog_bar.progress((i + 1) / total_students, text=f"{prog_text} ({i+1}/{total_students})")
            prog_bar.empty()

            students_df = pd.DataFrame(student_data).set_index("ID")
            st.subheader("Список учеников (нажмите на заголовок для сортировки)")
            st.dataframe(students_df, use_container_width=True)
        else:
            st.info("В этой группе пока нет учеников.")

        st.divider()

        st.subheader("➕ Добавить ученика в группу")
        with st.form("add_student_form", clear_on_submit=True):
            st.write("Введите данные нового ученика или существующего для поиска.")
            s_last_name = st.text_input("Фамилия*")
            s_first_name = st.text_input("Имя*")
            s_school = st.text_input("Школа")
            submitted_add = st.form_submit_button("Найти / Создать и добавить в группу")

            if submitted_add:
                if not s_last_name or not s_first_name:
                    st.warning("Фамилия и Имя обязательны.")
                else:
                    found_students = crud.find_students_by_name(db, first_name=s_first_name, last_name=s_last_name)
                    student_to_add = None

                    if found_students:
                        if len(found_students) == 1:
                             student_to_add = found_students[0]
                             st.info(f"Найден существующий ученик: {student_to_add.last_name} {student_to_add.first_name} (ID: {student_to_add.student_id}).")
                        else:
                            st.warning(f"Найдено несколько учеников с именем {s_first_name} {s_last_name}. Пожалуйста, уточните школу или используйте уникальные данные.")
                            student_to_add = None
                    
                    if not student_to_add and not found_students:
                        try:
                            student_to_add = crud.create_student(db, first_name=s_first_name, last_name=s_last_name, school_name=s_school if s_school else None)
                            st.success(f"Создан новый ученик: {student_to_add.last_name} {student_to_add.first_name} (ID: {student_to_add.student_id}).")
                        except Exception as create_e:
                            if "UNIQUE constraint failed: Students.first_name, Students.last_name, Students.school_name" in str(create_e):
                                st.error(f"Ошибка: Ученик {s_last_name} {s_first_name} из школы '{s_school}' уже существует. Попробуйте найти его.")
                            else:
                                st.error(f"Ошибка при создании ученика: {create_e}")
                            student_to_add = None

                    if student_to_add:
                        try:
                            participation = crud.add_student_to_group(db, student_id=student_to_add.student_id, group_id=selected_group_id)
                            if participation:
                                st.success(f"Ученик '{student_to_add.last_name} {student_to_add.first_name}' успешно добавлен/уже состоит в группе '{selected_group_name}'.")
                                st.rerun()
                            else:
                                st.warning(f"Ученик '{student_to_add.last_name} {student_to_add.first_name}' уже состоит в группе.")
                        except Exception as add_e:
                             st.error(f"Ошибка при добавлении ученика в группу: {add_e}")
                             st.exception(add_e)
    else:
        st.warning("Пожалуйста, выберите группу из списка выше, чтобы управлять учениками.")
    
    st.divider()
    st.header("Все ученики в базе данных")
    all_db_students = crud.get_all_students(db)
    if all_db_students:
        all_student_data = [{
            "ID": s.student_id, "Фамилия": s.last_name, "Имя": s.first_name, 
            "Школа": s.school_name or "-", 
            "Дата регистрации": s.registration_date.strftime('%Y-%m-%d %H:%M')
        } for s in all_db_students]
        st.dataframe(pd.DataFrame(all_student_data).set_index("ID"), use_container_width=True)
    else:
        st.info("В базе данных пока нет ни одного ученика.")


finally:
    if 'db' in locals() and db:
        db.close()