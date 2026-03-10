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
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
    except Exception as e:
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

# 💡 自動抓取資料夾內所有的 PDF 檔
pdf_files = [f for f in os.listdir() if f.endswith('.pdf')]
if not pdf_files:
    st.warning("⚠️ 找不到任何 PDF 檔案，請確認有將題庫上傳至 GitHub。")
    st.stop()

# 下拉式選單現在會自動帶入所有 PDF 檔名
selected_file = st.selectbox("請選擇要練習的題庫：", pdf_files)

# 切換題庫時，清除上一份考卷的紀錄
if "current_bank" not in st.session_state or st.session_state.current_bank != selected_file:
    st.session_state.current_bank = selected_file
    for key in ['test_set', 'submitted', 'user_answers']:
        if key in st.session_state:
            del st.session_state[key]

# 讀取題庫
with st.spinner(f'載入 {selected_file} 中，請稍候...'):
    qs = load_and_parse_pdf(selected_file)

if not qs:
    st.error("❌ 抓不到題目。請確認 PDF 內容格式。")
    st.stop()

st.success(f"🎉 成功載入！共偵測到 {len(qs)} 個題目。")

tab1, tab2 = st.tabs(["🎲 隨機測驗", "🔍 查看特定題號"])

with tab1:
    # 初始化「是否已交卷」的狀態
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # 狀態 1：尚未產生測驗卷
    if 'test_set' not in st.session_state:
        num_q = st.number_input("想練習幾題？", min_value=1, max_value=len(qs), value=min(10, len(qs)))
        if st.button("產生測驗卷"):
            st.session_state.test_set = random.sample(qs, num_q)
            st.session_state.submitted = False
            st.rerun() # 重新整理網頁進入測驗模式

    # 狀態 2：正在測驗中 (還沒交卷)
    elif not st.session_state.submitted:
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.test_set, 1):
                st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
                st.write(q['text'])
                # index=None 讓選項預設為空白，避免不小心猜中
                user_answers[q['id']] = st.radio(
                    "請選擇答案：", 
                    options=["1", "2", "3", "4"], 
                    key=f"q_{q['id']}",
                    horizontal=True,
                    index=None 
                )
                st.divider()
                
            submit_button = st.form_submit_button("交卷看成績")
            if submit_button:
                # 檢查是不是每一題都寫了
                if None in user_answers.values():
                    st.warning("⚠️ 還有題目未作答喔！請確認每一題都已勾選。")
                else:
                    st.session_state.user_answers = user_answers
                    st.session_state.submitted = True
                    st.rerun() # 重新整理網頁進入檢討模式

    # 狀態 3：已經交卷 (檢討模式 - 直接顯示對錯)
    else:
        st.subheader("📊 測驗結果")
        score = 0
        total = len(st.session_state.test_set)
        
        for i, q in enumerate(st.session_state.test_set, 1):
            st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
            st.write(q['text'])
            
            user_ans = st.session_state.user_answers[q['id']]
            correct_ans = q['ans']
            
            # 💡 這裡就是你想要的 UI 優化：把對錯結果直接畫在題目下方！
            if user_ans == correct_ans:
                score += 1
                st.success(f"✅ 你的答案：({user_ans}) —— 答對了！")
            else:
                st.error(f"❌ 你的答案：({user_ans}) —— 答錯了！ **正確答案是：({correct_ans})**")
            st.divider()
            
        st.info(f"💯 最終得分：{score} / {total}")
        
        # 點擊後清除記憶，重新開始
        if st.button("🔄 再測驗一次"):
            del st.session_state.test_set
            del st.session_state.submitted
            del st.session_state.user_answers
            st.rerun()

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
