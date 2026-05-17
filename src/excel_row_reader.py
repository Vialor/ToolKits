excel_row_reader.py

import streamlit as st 
import pandas as pd


def is_empty_cell(value):
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def parse_column_filter(text):
    """
    支持英文逗号和中文逗号。
    例如：
    name, age, address
    name，age，address
    """
    if not text:
        return []

    text = text.replace("，", ",")
    return [item.strip() for item in text.split(",") if item.strip()]


st.set_page_config(page_title="Excel 行阅读器", layout="wide")

st.title("Excel 行阅读器")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    if "row_index" not in st.session_state:
        st.session_state.row_index = 0

    if "cheat_sheets" not in st.session_state:
        st.session_state.cheat_sheets = {}

    total_rows = len(df)
    all_columns = list(df.columns)

    all_columns_text = ", ".join(all_columns)

    # 固定项：全部列名
    st.session_state.cheat_sheets["全部列名"] = all_columns_text

    # 首次打开页面时，默认在输入框里填入全部列名
    if "column_filter_text" not in st.session_state:
        st.session_state.column_filter_text = all_columns_text

    # 使用小抄时，在 text_area 创建之前更新输入框内容
    if "pending_column_filter_text" in st.session_state:
        st.session_state.column_filter_text = st.session_state.pending_column_filter_text
        del st.session_state.pending_column_filter_text

    st.subheader("列显示过滤")

    filter_text = st.text_area(
        "输入要显示的列名，用逗号分隔",
        key="column_filter_text",
        placeholder="例如：姓名, 年龄, 地址",
        height=80,
    )

    selected_columns = parse_column_filter(filter_text)

    if selected_columns:
        existing_columns = [col for col in selected_columns if col in df.columns]
        missing_columns = [col for col in selected_columns if col not in df.columns]

        if missing_columns:
            st.warning(f"以下列名不存在：{', '.join(missing_columns)}")
    else:
        existing_columns = all_columns

    ignore_empty = st.checkbox("忽略空 cell", value=True)

    with st.expander("查看全部列名"):
        st.write(all_columns_text)
    
    with st.expander("列名小抄", expanded=False):
        cheat_col1, cheat_col2, cheat_col3 = st.columns([2, 1, 1])

        with cheat_col1:
            selected_cheat_name = st.selectbox(
                "选择小抄",
                options=list(st.session_state.cheat_sheets.keys()),
            )

        with cheat_col2:
            if st.button("使用这个小抄"):
                st.session_state.pending_column_filter_text = st.session_state.cheat_sheets[selected_cheat_name]
                st.rerun()

        with cheat_col3:
            if selected_cheat_name != "全部列名":
                if st.button("删除这个小抄"):
                    del st.session_state.cheat_sheets[selected_cheat_name]
                    st.rerun()
            else:
                st.button("删除这个小抄", disabled=True)

        new_cheat_name = st.text_input(
            "给当前过滤文本起一个名字，然后保存到小抄",
            placeholder="例如：核心字段",
        )

        if st.button("保存当前过滤文本到小抄"):
            current_filter_text = st.session_state.get("column_filter_text", "").strip()

            if not new_cheat_name.strip():
                st.error("请先输入小抄名称。")
            elif not current_filter_text:
                st.error("当前过滤文本为空，不能保存。")
            elif new_cheat_name.strip() == "全部列名":
                st.error("“全部列名”是固定项，不能覆盖。")
            else:
                st.session_state.cheat_sheets[new_cheat_name.strip()] = current_filter_text
                st.success(f"已保存小抄：{new_cheat_name.strip()}")
                st.rerun()
    
    st.divider()
    
    st.write(f"共 {total_rows} 行")

    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

    with col1:
        if st.button("← 上一行"):
            st.session_state.row_index = max(0, st.session_state.row_index - 1)

    with col2:
        jump_to = st.number_input(
            "跳转到行号",
            min_value=1,
            max_value=total_rows,
            value=st.session_state.row_index + 1,
            step=1,
        )

    with col3:
        if st.button("跳转"):
            st.session_state.row_index = jump_to - 1

    with col4:
        if st.button("下一行 →"):
            st.session_state.row_index = min(total_rows - 1, st.session_state.row_index + 1)

    current_row = df.iloc[st.session_state.row_index]
    
    st.subheader(f"第 {st.session_state.row_index + 1} 行")

    for column in existing_columns:
        value = current_row[column]

        if ignore_empty and is_empty_cell(value):
            continue

        with st.container(border=True):
            st.markdown(f"**{column}**")
            st.write(value)