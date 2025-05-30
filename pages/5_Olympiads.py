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
from core.models import OlympiadLevelEnum, AwardEnum

st.set_page_config(layout="wide")
st.title("🏆 Олимпиады и Результаты")

db_session_generator = get_db()
db: Session = next(db_session_generator)

try:
    if 'selected_olympiad_id' not in st.session_state:
        st.session_state.selected_olympiad_id = None
    if 'previous_subject_filter' not in st.session_state:
        st.session_state.previous_subject_filter = "Все"

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Список Олимпиад")
        
        olympiads_all = crud.get_all_olympiads(db)
        subjects = sorted(list(set(o.subject for o in olympiads_all)))
        
        current_subject_filter = st.selectbox(
            "Фильтр по предмету:", 
            options=["Все"] + subjects, 
            key="olympiad_subject_filter_select"
        )

        if current_subject_filter != st.session_state.get('previous_filter_value_for_olympiads', current_subject_filter) :
            st.session_state.selected_olympiad_id = None
            st.session_state.previous_filter_value_for_olympiads = current_subject_filter

        st.session_state.previous_filter_value_for_olympiads = current_subject_filter


        if current_subject_filter == "Все":
            olympiads_query = olympiads_all
        else:
            olympiads_query = [o for o in olympiads_all if o.subject == current_subject_filter]

        valid_ids_in_query = {o.olympiad_id for o in olympiads_query}
        if st.session_state.selected_olympiad_id not in valid_ids_in_query:
            if st.session_state.selected_olympiad_id is not None:
                 st.session_state.selected_olympiad_id = None

        if not olympiads_query:
            st.info("Пока нет ни одной олимпиады (или по выбранному фильтру).")
        else:
            olympiad_names = [f"{o.olympiad_name} ({o.olympiad_date.strftime('%Y-%m-%d')})" for o in olympiads_query]
            name_to_id_map = {name: olympiads_query[i].olympiad_id for i, name in enumerate(olympiad_names)}
            id_to_name_map = {v: k for k,v in name_to_id_map.items()}


            default_radio_index = 0
            if st.session_state.selected_olympiad_id in id_to_name_map:
                try:
                    name_of_selected_id = id_to_name_map[st.session_state.selected_olympiad_id]
                    default_radio_index = olympiad_names.index(name_of_selected_id)
                except (KeyError, ValueError):
                    st.session_state.selected_olympiad_id = None
                    default_radio_index = 0
            else:
                 st.session_state.selected_olympiad_id = None
                 default_radio_index = 0

            
            selected_olympiad_name_display_from_radio = st.radio(
                "Выберите олимпиаду для просмотра деталей:",
                options=olympiad_names,
                index=default_radio_index,
                key="olympiad_selector_radio_key"
            )
            
            newly_selected_id_by_radio = name_to_id_map.get(selected_olympiad_name_display_from_radio)

            if newly_selected_id_by_radio is not None and newly_selected_id_by_radio != st.session_state.selected_olympiad_id:
                st.session_state.selected_olympiad_id = newly_selected_id_by_radio
                st.rerun()

        with st.expander("➕ Добавить новую олимпиаду", expanded=False):
            with st.form("new_olympiad_form", clear_on_submit=True):
                ol_name = st.text_input("Название олимпиады*")
                ol_date = st.date_input("Дата проведения*", value=datetime.date.today())
                ol_level_value = st.selectbox(
                    "Уровень олимпиады*",
                    options=[ol.value for ol in OlympiadLevelEnum],
                    format_func=lambda x: x
                )
                ol_subject = st.text_input("Предмет*", placeholder="Математика")
                ol_organizer = st.text_input("Организатор")
                submitted_ol = st.form_submit_button("Добавить олимпиаду")

                if submitted_ol:
                    if not ol_name or not ol_date or not ol_level_value or not ol_subject:
                        st.warning("Название, дата, уровень и предмет олимпиады обязательны.")
                    else:
                        try:
                            ol_level_enum = OlympiadLevelEnum(ol_level_value)
                            created_ol = crud.create_olympiad(
                                db, olympiad_name=ol_name, olympiad_date=ol_date,
                                level=ol_level_enum, subject=ol_subject, organizer=ol_organizer
                            )
                            st.success(f"Олимпиада '{created_ol.olympiad_name}' успешно добавлена!")
                            st.session_state.selected_olympiad_id = created_ol.olympiad_id
                            if current_subject_filter != "Все" and created_ol.subject != current_subject_filter:
                                pass
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed: Olympiads.olympiad_name, Olympiads.olympiad_date, Olympiads.subject" in str(e):
                                st.error(f"Ошибка: Олимпиада с таким названием, датой и предметом уже существует.")
                            else:
                                st.error(f"Ошибка при добавлении олимпиады: {e}")
    
    with col2:
        if st.session_state.selected_olympiad_id:
            olympiad = crud.get_olympiad_by_id(db, st.session_state.selected_olympiad_id)
            if olympiad:
                st.header(f"Результаты олимпиады: {olympiad.olympiad_name}")
                st.markdown(f"**Дата:** {olympiad.olympiad_date.strftime('%d.%m.%Y')} | **Уровень:** {olympiad.olympiad_level.value} | **Предмет:** {olympiad.subject}")
                if olympiad.organizer:
                    st.markdown(f"**Организатор:** {olympiad.organizer}")
                
                st.divider()
                st.subheader("Внести результат участника")
                with st.form(f"add_olympiad_result_form_{olympiad.olympiad_id}", clear_on_submit=True):
                    all_students = crud.get_all_students(db)
                    student_options = {f"{s.last_name} {s.first_name} (ID: {s.student_id})": s.student_id for s in all_students}
                    
                    if not student_options:
                        st.warning("В базе нет учеников для добавления результатов.")
                    else:
                        selected_student_label = st.selectbox("Ученик*:", options=list(student_options.keys()))
                        
                        award_value = st.selectbox(
                            "Награда*:",
                            options=[aw.value for aw in AwardEnum],
                            format_func=lambda x: x
                        )
                        score = st.number_input("Балл (опционально):", value=None, step=0.1, format="%.1f")
                        details = st.text_input("Детали (опционально, напр. '8 класс', 'Заочный тур'):")
                        doc_link = st.text_input("Ссылка на диплом/сертификат (опционально):")
                        
                        submitted_result = st.form_submit_button("Добавить результат")

                        if submitted_result:
                            if not selected_student_label or not award_value: 
                                st.warning("Ученик и награда обязательны.")
                            else:
                                student_id_to_add = student_options[selected_student_label]
                                award_enum = AwardEnum(award_value)
                                try:
                                    crud.add_olympiad_result(
                                        db, student_id=student_id_to_add, olympiad_id=olympiad.olympiad_id,
                                        award=award_enum, score=score, 
                                        details=details if details else None,
                                        result_document_link=doc_link if doc_link else None
                                    )
                                    st.success(f"Результат для '{selected_student_label}' успешно добавлен/обновлен.")
                                    st.rerun()
                                except Exception as e:
                                    if "UNIQUE constraint failed" in str(e): 
                                        st.error("Ошибка: Такой результат (ученик, олимпиада, детали) уже существует.")
                                    else:
                                        st.error(f"Ошибка при добавлении результата: {e}")
                
                st.divider()
                st.subheader("Список результатов по этой олимпиаде")
                results_for_olympiad = crud.get_olympiad_results_for_olympiad(db, olympiad.olympiad_id)
                if results_for_olympiad:
                    results_data = []
                    for res in results_for_olympiad:
                        student = crud.get_student_by_id(db, res.student_id) 
                        results_data.append({
                            "ID": res.olympiad_result_id,
                            "Фамилия": student.last_name if student else "N/A",
                            "Имя": student.first_name if student else "N/A",
                            "Награда": res.award.value,
                            "Балл": res.score,
                            "Детали": res.details or "-",
                            "Ссылка": res.result_document_link or "-"
                        })
                    
                    df_results = pd.DataFrame(results_data)
                    for col_name in ["Фамилия", "Имя", "Награда", "Детали", "Ссылка"]:
                         if col_name in df_results.columns:
                            df_results[col_name] = df_results[col_name].astype(str)
                    st.dataframe(df_results.set_index("ID"), use_container_width=True)
                else:
                    st.info("По этой олимпиаде пока нет внесенных результатов.")
            else:
                st.info("Выбранная олимпиада не найдена. Возможно, она была удалена.")
                if st.session_state.selected_olympiad_id is not None:
                    st.session_state.selected_olympiad_id = None
                    st.rerun()
        else:
            st.info("Выберите олимпиаду из списка слева для просмотра деталей.")

finally:
    if 'db' in locals() and db:
        db.close()