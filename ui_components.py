import streamlit as st
from llm_utils import translate_and_summarize, analyze_related_stocks
from db_utils import delete_news

def render_news_card(row, translate_lang, translate_summary):
    """
    단일 뉴스 카드를 렌더링하는 UI 컴포넌트
    """
    with st.container():
        # 데이터 준비
        sentiment_val = row.get('sentiment', '중립(Neutral)') or '중립(Neutral)'
        sentiment_reason = row.get('sentiment_reason', '') or ''
        impact_score = int(row.get('impact_score', 0) or 0)
        impact_pct = impact_score * 10
        
        # 데이터 보정: 지정된 범주를 벗어나는 경우 '중립'으로 강제 변환
        if '호재' in sentiment_val:
            sentiment_val = '호재 (Positive)'
            badge_cls, sentiment_icon = ('sentiment-positive', '📈')
        elif '악재' in sentiment_val:
            sentiment_val = '악재 (Negative)'
            badge_cls, sentiment_icon = ('sentiment-negative', '📉')
        else:
            sentiment_val = '중립 (Neutral)'
            badge_cls, sentiment_icon = ('sentiment-neutral', '➡️')

        # 네이티브 컨테이너 (테두리 포함)
        with st.container(border=True):
            # 카테고리 뱃지 + 제목
            cat_val = row.get('category', 'Other') or 'Other'
            cat_kws = row.get('category_keywords', '') or ''
            cat_css = f'cat-{cat_val}'
            cat_emoji_map = {'Politics': '🏛️', 'Economy': '💰', 'Society': '👥', 'IT': '💻', 'Securities': '📊', 'Other': '📎'}
            cat_emoji = cat_emoji_map.get(cat_val, '📎')
            st.html(f'<span class="category-badge {cat_css}">{cat_emoji} {cat_val}</span>')
            st.markdown(f"### {row['title']}")
            
            # 카테고리 분류 키워드 표시
            if cat_kws:
                cat_kw_list = [f'#{k.strip()}' for k in cat_kws.split(',') if k.strip()]
                if cat_kw_list:
                    st.caption(f"분류 근거: {' '.join(cat_kw_list)}")
            st.caption(f"📅 {row['publish_date'] or row['created_at']} | [원문 보기]({row['url']})")
            
            # 뱃지 및 영향도 바 (st.html 사용으로 마크다운 간섭 차단)
            st.html(f'<span class="sentiment-badge {badge_cls}">{sentiment_icon} {sentiment_val}</span>')
            if sentiment_reason:
                st.html(f'<div style="font-size:0.88rem; color:#475569; margin-top:5px; margin-bottom:12px;"><strong>📌 판별 근거:</strong> {sentiment_reason}</div>')
            
            st.html(f'<strong>📊 시장 영향도:</strong> <span style="float:right; font-weight:700; color:#4338ca;">{impact_score} / 10</span><div class="impact-bar-wrap"><div class="impact-bar-fill" style="width:{impact_pct}%;"></div></div>')
            
            # 요약 (네이티브)
            st.markdown("---")
            st.write("🤖 **AI 요약:**")
            st.write(row['summary'])

        # 키워드 태그
        keywords = [k.strip() for k in str(row['keywords']).split(',') if k.strip()]
        if keywords:
            kw_html = "".join([f'<span class="keyword-tag">{kw}</span>' for kw in keywords])
            st.html(kw_html)

        # 액션 버튼
        col_btn1, col_btn2, col_btn3, col_empty = st.columns([1, 1, 1, 3])
        if col_btn1.button("🗑️ 삭제", key=f"del_{row['id']}", use_container_width=True):
            delete_news(row['id'])
            st.rerun()
        if col_btn2.button("🌐 번역", key=f"trs_{row['id']}", use_container_width=True):
            st.session_state[f"show_translate_{row['id']}"] = True
        if col_btn3.button("📈 종목분석", key=f"stk_{row['id']}", use_container_width=True):
            st.session_state[f"show_stocks_{row['id']}"] = True

        # 번역 결과 표시
        if st.session_state.get(f"show_translate_{row['id']}", False):
            with st.spinner(f"🌐 {translate_lang}(으)로 번역 중..."):
                translated = translate_and_summarize(
                    row['text'] if 'text' in row and row['text'] else row['summary'],
                    translate_lang,
                    translate_summary
                )
            if translated:
                with st.container(border=True):
                    st.markdown(f"**🌐 {translate_lang} Translation ({translate_summary})**")
                    st.write(translated)
            st.session_state[f"show_translate_{row['id']}"] = False

        # 관련 종목 분석 결과 표시
        if st.session_state.get(f"show_stocks_{row['id']}", False):
            with st.spinner("📈 관련 종목 분석 중..."):
                stock_result = analyze_related_stocks(
                    row['text'] if 'text' in row and row['text'] else row['summary']
                )
            stocks = stock_result.get('stocks', [])
            if stocks:
                with st.container(border=True):
                    st.markdown("**📈 Related Stock Analysis**")
                    for s in stocks:
                        impact_cls = 'stock-positive' if s['impact'] == 'Positive' else 'stock-negative'
                        impact_emoji = '🟢' if s['impact'] == 'Positive' else '🔴'
                        st.html(f'<div class="{impact_cls}"><strong>{impact_emoji} {s["name"]}</strong> ({s["impact"]})<br><span style="font-size:0.88rem; color:#475569;">{s["reason"]}</span></div>')
                    st.caption("⚠️ 본 분석은 절대적인 투자 권유가 아니며, 뉴스 기반의 정보 제공 목적입니다. 투자 판단은 본인의 책임하에 이루어져야 합니다.")
            else:
                st.info("관련 종목을 분석할 수 없습니다.")
            st.session_state[f"show_stocks_{row['id']}"] = False

        st.markdown("<br>", unsafe_allow_html=True)
