import streamlit as st
import PyPDF2
import re
import random
import os

st.set_page_config(page_title="題庫測驗系統", page_icon="📝", layout="centered")

@st.cache_data 
def load_and_parse_pdf(file_path):
    all_text = ""
    try:
        # 改成直接讀取伺服器上的檔案路徑
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
    except Exception as e:
        st.error(f"讀取檔案失敗: {e}")
        return []

    pattern = r'\((\d)\)\s*(\d+)\.(.*?)(?=\(\d\)\s*\d+\.|$)'
    clean_text = re.sub(r'\n(?!\(\d\)\d+\.)', '', all_text)
    matches = re.findall(pattern, clean_text, re.DOTALL)
    
    questions = []
    for ans, num, content in matches:
        questions.append({
            "id": num.strip(),
            "ans": ans.strip(),
            "text": content.strip()
        })
    return questions

st.title("📝 專屬題庫測驗系統")

# 1. 這裡定義你的題庫選單！
# 左邊是「網頁上顯示的名稱」，右邊是「實際的 PDF 檔名」
question_banks = {
    "題庫一：甲級廢水處理": "bank1.pdf",
    "題庫二：乙級廢水處理 (請自行修改)": "bank2.pdf"
}

# 2. 建立下拉式選單
selected_bank_name = st.selectbox("請選擇要練習的題庫：", list(question_banks.keys()))
selected_file_path = question_banks[selected_bank_name]

# 3. 關鍵機制：當切換題庫時，把上一份考卷的紀錄清空
if "current_bank" not in st.session_state or st.session_state.current_bank != selected_bank_name:
    st.session_state.current_bank = selected_bank_name
    if "test_set" in st.session_state:
        del st.session_state.test_set

# 檢查 PDF 檔案是否存在
if os.path.exists(selected_file_path):
    with st.spinner(f'載入 {selected_bank_name} 中，請稍候...'):
        qs = load_and_parse_pdf(selected_file_path)
    
    if not qs:
        st.error("❌ 抓不到題目。請確認 PDF 內容格式。")
    else:
        st.success(f"🎉 成功載入！共偵測到 {len(qs)} 個題目。")
        
        tab1, tab2 = st.tabs(["🎲 隨機測驗", "🔍 查看特定題號"])
        
        with tab1:
            num_q = st.number_input("想練習幾題？", min_value=1, max_value=len(qs), value=min(10, len(qs)))
            
            if st.button("產生測驗卷"):
                st.session_state.test_set = random.sample(qs, num_q)
                
            if 'test_set' in st.session_state:
                with st.form("quiz_form"):
                    user_answers = {}
                    for i, q in enumerate(st.session_state.test_set, 1):
                        st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
                        st.write(q['text'])
                        user_answers[q['id']] = st.radio(
                            "請選擇答案：", 
                            options=["1", "2", "3", "4"], 
                            key=f"q_{q['id']}",
                            horizontal=True
                        )
                        st.divider()
                        
                    submit_button = st.form_submit_button("交卷看成績")
                    if submit_button:
                        score = 0
                        for q in st.session_state.test_set:
                            if user_answers[q['id']] == q['ans']:
                                score += 1
                            else:
                                st.error(f"❌ 題號 {q['id']} 答錯了。正確答案是：({q['ans']})")
                        st.success(f"💯 測驗結束！您的得分：{score} / {len(st.session_state.test_set)}")

        with tab2:
            target = st.text_input("請輸入要查詢的題號：")
            if st.button("搜尋"):
                if target:
                    found = next((q for q in qs if q['id'] == target), None)
                    if found:
                        st.info(f"**題號 {found['id']}**\n\n{found['text']}\n\n**解答：({found['ans']})**")
                    else:
                        st.warning("找不到該題號。")
                else:
                    st.warning("請先輸入題號！")
else:
    # 如果找不到檔案，提醒使用者上傳
    st.warning(f"⚠️ 找不到檔案 `{selected_file_path}`。請確認你已經將這個 PDF 檔上傳到 GitHub！")