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
from core.models import ProblemTypeEnum

st.set_page_config(layout="wide")
st.title("📊 Кондуит Занятия")

db_session_generator = get_db()
db: Session = next(db_session_generator)

CALCULATED_COLUMNS = ['Задач решено (занятие)', 'Рейтинг (занятие)']

try:
    query_params = st.query_params
    initial_group_id = query_params.get("group_id", [None])[0]
    initial_lesson_id = query_params.get("lesson_id", [None])[0]
    try:
        initial_group_id = int(initial_group_id) if initial_group_id else None
        initial_lesson_id = int(initial_lesson_id) if initial_lesson_id else None
    except (ValueError, TypeError):
        initial_group_id = None
        initial_lesson_id = None

    col1, col2 = st.columns(2)
    with col1:
        groups = crud.get_all_groups(db)
        group_options = {group.group_name: group.group_id for group in groups}
        group_id_to_name = {v: k for k, v in group_options.items()}
        group_names_list = [""] + list(group_options.keys())
        default_group_index = 0
        if initial_group_id and initial_group_id in group_id_to_name:
            group_name_to_select = group_id_to_name[initial_group_id]
            try:
                default_group_index = group_names_list.index(group_name_to_select)
            except ValueError:
                default_group_index = 0
        selected_group_name = st.selectbox(
            "1. Выберите группу:", options=group_names_list, index=default_group_index, key="conduit_group_select"
        )
        selected_group_id = group_options.get(selected_group_name)

    with col2:
        selected_lesson_id = None
        default_lesson_index = 0
        lesson_options = {}
        lesson_id_to_label = {}
        lesson_labels_list = [""]
        if selected_group_id:
            lessons = crud.get_lessons_for_group(db, selected_group_id)
            lesson_options = {f"{l.lesson_date} - {l.topic} ({l.subject_area.value})": l.lesson_id for l in lessons}
            lesson_id_to_label = {v: k for k, v in lesson_options.items()}
            lesson_labels_list = [""] + list(lesson_options.keys())
            if initial_lesson_id and selected_group_id == initial_group_id and initial_lesson_id in lesson_id_to_label:
                lesson_label_to_select = lesson_id_to_label[initial_lesson_id]
                try:
                    default_lesson_index = lesson_labels_list.index(lesson_label_to_select)
                except ValueError:
                    default_lesson_index = 0
            selected_lesson_label = st.selectbox(
                "2. Выберите занятие:", options=lesson_labels_list, index=default_lesson_index, key="conduit_lesson_select"
            )
            selected_lesson_id = lesson_options.get(selected_lesson_label)
        else:
            st.selectbox("2. Выберите занятие:", options=["Сначала выберите группу"], disabled=True, index=0)

    if selected_lesson_id and selected_group_id:
        st.header(f"Кондуит для занятия: {selected_lesson_label}")
        lesson = crud.get_lesson_by_id(db, selected_lesson_id)

        with st.expander("➕ Добавить / Управлять задачами занятия"):
            columns_in_lesson = crud.get_columns_for_lesson(db, selected_lesson_id)
            st.write("Существующие колонки:")
            if columns_in_lesson:
                cols_data = [{"ID": c.column_id, "Метка": c.column_label, "Тип": c.problem_type.value, "Порядок": c.display_order, "Разобрана": c.is_discussed} for c in columns_in_lesson]
                cols_data_df = pd.DataFrame(cols_data).set_index("ID")
                st.dataframe(cols_data_df, use_container_width=True)

                st.subheader("✏️ Пометить разобранные задачи")
                column_options_select = {col.column_label: col.column_id for col in columns_in_lesson}
                discussed_labels_current = [col.column_label for col in columns_in_lesson if col.is_discussed]
                selected_discussed_labels = st.multiselect(
                    "Выберите задачи, которые были разобраны:",
                    options=list(column_options_select.keys()),
                    default=discussed_labels_current,
                    key=f"discuss_multiselect_{selected_lesson_id}"
                )

                if st.button("Обновить статус разбора", key=f"discuss_btn_{selected_lesson_id}"):
                    try:
                        updated_count = 0
                        for label, col_id in column_options_select.items():
                            column = crud.get_column_by_id(db, col_id)
                            should_be_discussed = label in selected_discussed_labels
                            if column and column.is_discussed != should_be_discussed:
                                crud.mark_column_discussed(db, col_id, is_discussed=should_be_discussed)
                                updated_count += 1
                        if updated_count > 0:
                            st.success(f"Статус разбора обновлен ({updated_count} изменений).")
                            st.rerun()
                        else:
                            st.info("Статус разбора не изменился.")
                    except Exception as e:
                        st.error(f"Ошибка при обновлении статуса: {e}")
            else:
                st.info("На этом занятии еще нет задач.")

            st.subheader("➕ Добавить новую колонку (задачу)")
            with st.form(f"add_column_form_{selected_lesson_id}", clear_on_submit=True):
                new_col_label = st.text_input("Метка новой задачи* (напр., '1', '3a', '8+')")
                new_col_type = st.selectbox(
                    "Тип задачи*", options=[pt.value for pt in ProblemTypeEnum], format_func=lambda x: x
                )
                next_order = max([c.display_order for c in columns_in_lesson], default=-1) + 1 if columns_in_lesson else 0
                new_col_order = st.number_input("Порядок отображения*", min_value=0, value=next_order)
                submitted_col = st.form_submit_button("Добавить колонку")

                if submitted_col:
                    if not new_col_label:
                        st.warning("Метка задачи обязательна.")
                    else:
                        try:
                            problem_enum = ProblemTypeEnum(new_col_type)
                            crud.add_lesson_column(
                                db, lesson_id=selected_lesson_id, column_label=new_col_label,
                                problem_type=problem_enum, display_order=new_col_order
                            )
                            st.success(f"Колонка '{new_col_label}' добавлена.")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed: LessonColumns.lesson_id, LessonColumns.column_label" in str(e):
                                st.error(f"Ошибка: Колонка с меткой '{new_col_label}' уже существует для этого занятия.")
                            elif "UNIQUE constraint failed: LessonColumns.lesson_id, LessonColumns.display_order" in str(e):
                                st.error(f"Ошибка: Колонка с порядком '{new_col_order}' уже существует для этого занятия.")
                            else:
                                st.error(f"Ошибка добавления колонки: {e}")
                                st.exception(e)

        st.divider()
        st.subheader("Таблица результатов")

        try:
            conduit_df, problem_ratings = analysis.prepare_conduit_dataframe(db, selected_lesson_id)

            if not conduit_df.empty:
                discussed_labels = analysis.get_discussed_column_labels(db, selected_lesson_id)
                cols_to_disable = [col for col in discussed_labels if col in conduit_df.columns] + CALCULATED_COLUMNS

                student_name_to_id = analysis.get_student_name_to_id_map(db, selected_group_id)
                column_label_to_id = analysis.get_column_label_to_id_map(db, selected_lesson_id)
                editor_key = f"conduit_editor_{selected_lesson_id}"

                st.info("Поставьте/снимите галочку в ячейке и нажмите 'Сохранить изменения'.")

                edited_df = st.data_editor(
                    conduit_df,
                    key=editor_key,
                    disabled=cols_to_disable,
                    use_container_width=True
                )

                if st.button("Сохранить изменения в кондуите", key=f"save_conduit_{selected_lesson_id}"):
                    save_counter = 0
                    delete_counter = 0
                    error_flag = False

                    original_df_for_compare = conduit_df.drop(columns=CALCULATED_COLUMNS, errors='ignore')
                    edited_df_for_compare = edited_df.drop(columns=CALCULATED_COLUMNS, errors='ignore')

                    if not original_df_for_compare.equals(edited_df_for_compare):
                        diff_mask = (original_df_for_compare != edited_df_for_compare)
                        changed_cells = diff_mask.stack()
                        changed_cells = changed_cells[changed_cells]
                        changed_indices = changed_cells.index
                    else:
                        level_0_name = original_df_for_compare.index.name if original_df_for_compare.index.name else "index"
                        level_1_name = original_df_for_compare.columns.name if original_df_for_compare.columns.name else "columns"
                        changed_indices = pd.MultiIndex.from_tuples(
                            [],
                            names=[level_0_name, level_1_name]
                        )

                    if not changed_indices.empty:
                        prog_text = "Сохранение изменений..."
                        progress_bar_save = st.progress(0, text=prog_text)
                        total_changes = len(changed_indices)

                        for idx, (student_name, col_label) in enumerate(changed_indices):
                            if col_label in CALCULATED_COLUMNS:
                                continue

                            student_id = student_name_to_id.get(student_name)
                            column_id = column_label_to_id.get(col_label)
                            
                            current_value_in_edited_df = edited_df_for_compare.loc[student_name, col_label]
                            if isinstance(current_value_in_edited_df, pd.Series):
                                solved_status = current_value_in_edited_df.item() 
                            else:
                                solved_status = bool(current_value_in_edited_df)


                            if student_id is None or column_id is None:
                                st.warning(f"Не удалось найти ID для {student_name} или {col_label}. Пропускаем.")
                                continue

                            try:
                                if solved_status:
                                    crud.add_result(db, student_id, column_id, selected_lesson_id)
                                    save_counter += 1
                                else:
                                    crud.delete_result(db, student_id, column_id)
                                    delete_counter += 1
                            except Exception as save_e:
                                st.error(f"Ошибка сохранения для {student_name}, задача {col_label}: {save_e}")
                                error_flag = True
                                st.exception(save_e)
                            progress_bar_save.progress((idx + 1) / total_changes, text=f"{prog_text} ({idx+1}/{total_changes})")

                        progress_bar_save.empty()

                        if not error_flag:
                            st.success(f"Изменения успешно сохранены! Добавлено: {save_counter}, Удалено: {delete_counter} отметок.")
                            st.rerun()
                        else:
                            st.error("Произошли ошибки во время сохранения. Проверьте сообщения выше.")
                    else:
                        st.info("Нет изменений для сохранения.")
            else:
                st.info("В этой группе нет студентов или для этого занятия не добавлены задачи.")

        except Exception as e:
            st.error(f"Ошибка при загрузке или обработке данных кондуита: {e}")
            st.exception(e)

    else:
        st.info("Пожалуйста, выберите группу и занятие выше, чтобы увидеть кондуит.")

finally:
    if 'db' in locals() and db:
        db.close()