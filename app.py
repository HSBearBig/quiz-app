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

# --- 💡 這裡加入了智慧排序功能 ---
def get_sort_key(filename):
    # 尋找檔名中的數字，例如「第1科_XXX.pdf」會抓出 '1'
    numbers = re.findall(r'\d+', filename)
    # 轉換成整數來正確排序(1, 2, 3...10)；如果檔名剛好沒數字，就排到最下面
    return int(numbers[0]) if numbers else float('inf')

# 抓取所有 PDF 並進行排序
raw_pdf_files = [f for f in os.listdir() if f.endswith('.pdf')]
pdf_files = sorted(raw_pdf_files, key=get_sort_key)
# ---------------------------------

if not pdf_files:
    st.warning("⚠️ 找不到任何 PDF 檔案，請確認有將題庫上傳至 GitHub。")
    st.stop()

selected_file = st.selectbox("請選擇要練習的題庫：", pdf_files)

if 'mistakes' not in st.session_state:
    st.session_state.mistakes = {}

if "current_bank" not in st.session_state or st.session_state.current_bank != selected_file:
    st.session_state.current_bank = selected_file
    for key in ['test_set', 'submitted', 'user_answers', 'quick_q', 'quick_ans']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.mistakes = {} 

with st.spinner(f'載入 {selected_file} 中，請稍候...'):
    qs = load_and_parse_pdf(selected_file)

if not qs:
    st.error("❌ 抓不到題目。請確認 PDF 內容格式。")
    st.stop()

st.success(f"🎉 成功載入！共偵測到 {len(qs)} 個題目。")

tab1, tab2, tab3, tab4 = st.tabs(["🎲 隨機測驗", "🔍 查看特定題號", "⚡ 馬上讀", "📔 專屬錯題本"])

with tab1:
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    if 'test_set' not in st.session_state:
        num_q = st.number_input("想練習幾題？", min_value=1, max_value=len(qs), value=min(10, len(qs)))
        if st.button("產生測驗卷"):
            st.session_state.test_set = random.sample(qs, num_q)
            st.session_state.submitted = False
            st.rerun() 

    elif not st.session_state.submitted:
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.test_set, 1):
                st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
                st.write(q['text'])
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
                if None in user_answers.values():
                    st.warning("⚠️ 還有題目未作答喔！請確認每一題都已勾選。")
                else:
                    st.session_state.user_answers = user_answers
                    st.session_state.submitted = True
                    st.rerun() 

    else:
        st.subheader("📊 測驗結果")
        score = 0
        total = len(st.session_state.test_set)
        
        for i, q in enumerate(st.session_state.test_set, 1):
            st.markdown(f"**【第 {i} 題 / 題號 {q['id']}】**")
            st.write(q['text'])
            
            user_ans = st.session_state.user_answers[q['id']]
            correct_ans = q['ans']
            
            if user_ans == correct_ans:
                score += 1
                st.success(f"✅ 你的答案：({user_ans}) —— 答對了！")
            else:
                st.error(f"❌ 你的答案：({user_ans}) —— 答錯了！ **正確答案是：({correct_ans})**")
                st.session_state.mistakes[q['id']] = q
            st.divider()
            
        st.info(f"💯 最終得分：{score} / {total}")
        
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

with tab3:
    st.subheader("⚡ 馬上讀 (一題一答)")

    if 'quick_q' not in st.session_state:
        st.session_state.quick_q = random.choice(qs)

    q = st.session_state.quick_q

    st.markdown(f"**【題號 {q['id']}】**")
    st.write(q['text'])

    quick_ans = st.radio(
        "請選擇答案：",
        options=["1", "2", "3", "4"],
        key="quick_ans",
        horizontal=True,
        index=None
    )

    if quick_ans is not None:
        if quick_ans == q['ans']:
            st.success("✅ 答對了！")
        else:
            st.error(f"❌ 答錯了！正確答案是：({q['ans']})")
            st.session_state.mistakes[q['id']] = q

        if st.button("➡️ 下一題", key="next_quick_q"):
            st.session_state.quick_q = random.choice(qs)
            del st.session_state.quick_ans
            st.rerun()

with tab4:
    st.subheader("📔 專屬錯題本")
    
    if not st.session_state.mistakes:
        st.info("太棒了！目前沒有任何錯題紀錄喔，請繼續保持！")
    else:
        st.warning(f"目前累積了 {len(st.session_state.mistakes)} 題需要複習的錯題：")
        
        for q_id, wrong_q in st.session_state.mistakes.items():
            st.markdown(f"**【題號 {wrong_q['id']}】**")
            st.write(wrong_q['text'])
            st.markdown(f"👉 **正確解答：({wrong_q['ans']})**")
            st.divider()
            
        if st.button("🗑️ 清空錯題本"):
            st.session_state.mistakes = {}
            st.rerun()



