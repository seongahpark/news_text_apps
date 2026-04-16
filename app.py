import streamlit as st
import pandas as pd
from news_utils import get_daum_main_news_links, extract_article_content
from llm_utils import summarize_text, extract_keywords, analyze_sentiment, classify_category, translate_and_summarize, analyze_related_stocks
from db_utils import init_db, save_news, get_all_news, delete_news, delete_all_news
from ui_components import render_news_card
import time

# --- Page Config ---
st.set_page_config(
    page_title="News Insight Extractor",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 브라우저 자동 번역 방지용 메타 태그 주입
st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
""", unsafe_allow_html=True)

# --- Initialize DB ---
init_db()

# --- Custom CSS ---
with open("assets/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.info("뉴스 수집 및 분석 설정을 관리합니다.")
    
    summary_option = st.selectbox(
        "요약 길이 선택",
        ["3줄", "5줄", "500자 이내"],
        index=0
    )
    
    keyword_count = st.slider("추출 키워드 개수", 3, 10, 5)
    
    if st.button("🗑️ 모든 데이터 초기화"):
        delete_all_news()
        st.success("✅ 모든 데이터가 삭제되었습니다.")
        st.rerun()

    st.divider()
    st.subheader("🌐 번역 설정")
    translate_lang = st.selectbox(
        "번역 대상 언어",
        ["영어", "일본어", "중국어(간체)", "중국어(번체)", "스페인어", "프랑스어", "독일어", "베트남어", "태국어"],
        index=0
    )
    translate_summary = st.selectbox(
        "요약 옵션",
        ["3줄 요약", "5줄 요약", "500자 이내"],
        index=0
    )

# --- Main Logic ---
st.title("📰 News Insight Extractor")
st.markdown("#### 실시간 주요 뉴스 수집 및 AI 요약 분석 서비스")

tab1, tab2 = st.tabs(["🚀 수집 및 분석", "📁 저장된 인사이트"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔗 뉴스 소스 선택")
        input_type = st.radio("방식 선택", ["Daum 주요 뉴스 자동 수집", "직접 URL 입력"], horizontal=True)
        
        if input_type == "Daum 주요 뉴스 자동 수집":
            cnt = st.number_input("가져올 뉴스 개수", 1, 10, 3)
            if st.button("뉴스 가져오기"):
                with st.spinner("뉴스를 불러오는 중입니다..."):
                    links = get_daum_main_news_links()[:cnt]
                    if not links:
                        st.error("뉴스를 가져오지 못했습니다.")
                    else:
                        st.session_state['pending_links'] = links
                        st.success(f"{len(links)}개의 뉴스를 찾았습니다.")
        else:
            url_input = st.text_input("분석할 뉴스 URL을 입력하세요")
            if st.button("URL 추가"):
                if url_input:
                    st.session_state['pending_links'] = [url_input]
                else:
                    st.error("URL을 입력해주세요.")

    # 뉴스 처리
    if 'pending_links' in st.session_state and st.session_state['pending_links']:
        st.divider()
        head_col1, head_col2 = st.columns([5, 1])
        with head_col1:
            st.subheader("⌛ 분석 대기 목록")
        with head_col2:
            analyze_all_clicked = st.button("🚀 모두 분석", use_container_width=True)

        if analyze_all_clicked:
            total_links = len(st.session_state['pending_links'])
            my_bar = st.progress(0, text="전체 뉴스 분석을 준비 중입니다...")
            success_count = 0

            # 리스트 복사본으로 순차 분석 진행
            for idx, url in enumerate(list(st.session_state['pending_links'])):
                my_bar.progress(idx / total_links, text=f"AI 분석 중... ({idx+1}/{total_links})")
                content = extract_article_content(url)
                if content:
                    summary   = summarize_text(content['text'], summary_option)
                    keywords  = extract_keywords(content['text'], keyword_count)
                    sentiment = analyze_sentiment(content['text'])
                    category  = classify_category(content['text'])

                    content['summary']            = summary
                    content['keywords']           = keywords
                    content['sentiment_analysis'] = sentiment
                    content['category_analysis']  = category

                    save_news(content)
                    success_count += 1
                    st.session_state['pending_links'].remove(url)
            
            my_bar.progress(1.0, text="✨ 모든 분석이 완료되었습니다!")
            if success_count > 0:
                st.success(f"✅ 총 {success_count}개의 뉴스 분석이 완료 및 저장되었습니다!")
            else:
                st.error("처리할 수 있는 뉴스가 없거나 실패했습니다.")
            time.sleep(1.5)
            st.rerun()
        
        for i, url in enumerate(st.session_state['pending_links']):
            with st.expander(f"처리 대기: {url}", expanded=True):
                if st.button(f"분석 시작 ({i})", key=f"btn_{i}"):
                    with st.spinner("AI가 분석 중입니다... (요약 → 키워드 → 감성 분석 → 카테고리 분류 순으로 진행)"):
                        content = extract_article_content(url)
                        if content:
                            summary   = summarize_text(content['text'], summary_option)
                            keywords  = extract_keywords(content['text'], keyword_count)
                            sentiment = analyze_sentiment(content['text'])
                            category  = classify_category(content['text'])

                            content['summary']            = summary
                            content['keywords']           = keywords
                            content['sentiment_analysis'] = sentiment
                            content['category_analysis']  = category

                            save_news(content)
                            st.success("✅ 분석 완료 및 저장되었습니다!")
                            st.session_state['pending_links'].pop(i)
                            st.rerun()
                        else:
                            st.error("본문 추출에 실패했습니다.")

with tab2:
    st.subheader("📊 추출된 인사이트 목록")
    
    df = get_all_news()
    
    if df.empty:
        st.info("아직 저장된 뉴스 데이터가 없습니다.")
    else:
        # 필터링 UI
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search_query = st.text_input("🔍 키워드 또는 제목 검색")
        with filter_col2:
            cat_options = {"전체": "All", "정치": "Politics", "경제": "Economy", "사회": "Society", "IT": "IT", "증권": "Securities", "기타": "Other"}
            category_display = st.selectbox("📂 카테고리 필터", list(cat_options.keys()))
            category_filter = cat_options[category_display]
        if search_query:
            sq_ns = "".join(search_query.split())  # 검색어에서 모든 공백 제거
            df = df[
                df['title'].str.replace(r'\s+', '', regex=True).str.contains(sq_ns, case=False, na=False) | 
                df['keywords'].str.replace(r'\s+', '', regex=True).str.contains(sq_ns, case=False, na=False)
            ]
        if category_filter != "All":
            df = df[df['category'].str.contains(category_filter, na=False)]
        
        for idx, row in df.iterrows():
            render_news_card(row, translate_lang, translate_summary)

        # 다운로드 기능
        st.divider()
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 결과 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"news_insights_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
