import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# API 키 설정
# 환경 변수에 없을 경우를 대비해 None 리턴 처리를 하거나 예외 처리를 합니다.
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def summarize_text(text: str, summary_len: str = "3줄") -> Optional[str]:
    """
    뉴스 본문을 요약합니다.
    summary_len: '3줄', '5줄', '500자' 등
    """
    if not client:
        return "OpenAI API Key가 설정되지 않았습니다."

    if not text or len(text) < 50:
        return "요약할 본문 내용이 너무 짧습니다."

    prompt = f"""아래 뉴스 본문을 {summary_len} 정도로 요약해줘.
한국어로 작성하고, 뉴스 앵커가 브리핑하는 듯한 전문적인 말투를 사용해.

뉴스 본문:
\"\"\"
{text}
\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 유능한 뉴스 요약 AI 조수야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in summarization: {e}")
        return None

def extract_keywords(text: str, num_keywords: int = 5) -> List[str]:
    """
    뉴스 본문에서 핵심 키워드를 추출합니다.
    """
    if not client:
        return []

    if not text or len(text) < 50:
        return []

    prompt = f"""아래 뉴스 본문에서 가장 중요한 핵심 키워드 {num_keywords}개를 뽑아줘.
결과는 쉼표(,)로 구분된 단어 리스트로만 답변해. 다른 설명은 하지 마.

뉴스 본문:
\"\"\"
{text}
\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 텍스트 분석 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        keywords_str = response.choices[0].message.content
        keywords = [k.strip() for k in keywords_str.split(',')]
        return keywords[:num_keywords]
    except Exception as e:
        print(f"Error in keyword extraction: {e}")
        return []

def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    금융/경제 뉴스 본문을 감성 분석합니다.
    반환값:
        sentiment   : '긍정(Positive)' | '부정(Negative)' | '중립(Neutral)'
        reason      : 판별 근거 (2~3문장 요약)
        impact_score: 시장 영향도 점수 (1~10)
    """
    fallback = {"sentiment": "중립(Neutral)", "reason": "분석 불가", "impact_score": 0}

    if not client:
        return {**fallback, "reason": "OpenAI API Key가 설정되지 않았습니다."}

    if not text or len(text) < 50:
        return {**fallback, "reason": "본문 내용이 너무 짧아 감성 분석이 불가능합니다."}

    prompt = f"""당신은 금융 및 경제 뉴스 데이터를 분석하는 수석 애널리스트입니다.
아래 뉴스 본문을 읽고 다음 세 가지를 JSON 형식으로만 답변하세요. 다른 설명은 절대 포함하지 마세요.

1. sentiment: 뉴스의 전반적인 뉘앙스를 '호재 (Positive)', '악재 (Negative)', '중립 (Neutral)' 중 하나로 판별 (절대 이 세 단어 외의 다른 단어를 사용하지 마세요.)
2. reason: 왜 그렇게 판별했는지 핵심 근거를 뉴스 본문에서 발췌하여 2~3문장으로 요약 (한국어, 전문적인 말투 사용)
3. impact_score: 이 뉴스가 관련 산업이나 시장에 미칠 파급력을 1~10 사이의 정수로 평가 (정수만 반환)

뉴스 본문:
\"\"\"
{text[:3000]}
\"\"\"

응답 예시:
{{"sentiment": "호재 (Positive)", "reason": "삼성전자가 예상치를 상회하는 실적을 발표하며 반도체 경기 회복의 신호를 보냈습니다. 이에 따라 관련 소부장 기업들의 동반 성장이 기대됩니다.", "impact_score": 8}}

반드시 위 JSON 형식으로만 답변하세요:
{{"sentiment": "...", "reason": "...", "impact_score": 숫자}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 금융·경제 뉴스 감성 분석 전문가야. 반드시 JSON 형식으로만 응답해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        # 필드 검증 및 기본값 보정
        sentiment = result.get("sentiment", "중립 (Neutral)")
        reason = result.get("reason", "판별 근거 없음")
        impact_score = int(result.get("impact_score", 5))
        impact_score = max(1, min(10, impact_score))  # 1~10 범위 강제
        return {"sentiment": sentiment, "reason": reason, "impact_score": impact_score}
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return fallback

def classify_category(text: str) -> Dict[str, any]:
    """
    뉴스 본문을 주제별로 자동 분류합니다.
    반환값:
        category         : 'Politics' | 'Economy' | 'Society' | 'IT' | 'Securities' | 'Other'
        category_keywords: 분류 근거 핵심 키워드 3개 (리스트)
    """
    VALID_CATEGORIES = ['Politics', 'Economy', 'Society', 'IT', 'Securities', 'Other']
    fallback = {"category": "Other", "category_keywords": []}

    if not client:
        return fallback

    if not text or len(text) < 50:
        return fallback

    prompt = f"""당신은 뉴스 콘텐츠를 카테고리별로 자동 분류하는 편집 데스크입니다.
아래 뉴스 본문을 읽고, 가장 적합한 주제 카테고리 하나와 분류 근거가 되는 핵심 키워드 3개를 JSON 형식으로만 답변하세요.

카테고리 후보: Politics, Economy, Society, IT, Securities, Other
(반드시 위 6개 영어 단어 중 하나만 선택하세요. 한글이나 다른 단어는 절대 사용하지 마세요.)

뉴스 본문:
\"\"\"
{text[:3000]}
\"\"\"

응답 예시:
{{"category": "Economy", "category_keywords": ["금리 인상", "연준", "인플레이션"]}}
{{"category": "IT", "category_keywords": ["AI 반도체", "엔비디아", "GPU 수출규제"]}}

반드시 위 JSON 형식으로만 답변하세요:
{{"category": "...", "category_keywords": ["키워드1", "키워드2", "키워드3"]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 뉴스 편집 데스크 전문가야. 반드시 JSON 형식으로만 응답해. category 값은 반드시 영어(Politics, Economy, Society, IT, Securities, Other)로만 답변해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        category = result.get("category", "Other")
        # 유효한 카테고리인지 검증
        if category not in VALID_CATEGORIES:
            category = "Other"
        category_keywords = result.get("category_keywords", [])
        if not isinstance(category_keywords, list):
            category_keywords = []
        return {"category": category, "category_keywords": category_keywords[:3]}
    except Exception as e:
        print(f"Error in category classification: {e}")
        return fallback


def translate_and_summarize(text: str, target_lang: str = "English", summary_option: str = "3줄 요약") -> Optional[str]:
    """
    뉴스 본문을 타겟 언어로 번역하고 요약합니다.
    Args:
        text          : 원문 뉴스 본문
        target_lang   : 번역 대상 언어 (English, Japanese, Chinese 등)
        summary_option: 요약 옵션 ('3줄 요약', '5줄 요약', '500자 이내 요약')
    Returns:
        번역+요약된 텍스트 (str)
    """
    if not client:
        return "OpenAI API Key가 설정되지 않았습니다."

    if not text or len(text) < 50:
        return "번역할 본문 내용이 너무 짧습니다."

    prompt = f"""You are a professional translator and content summary editor.
Translate and summarize the following news article into {target_lang}.

Rules:
1. The final output MUST be written entirely in {target_lang}.
2. Summarize according to this option: {summary_option}
3. Maintain the original news tone (objectivity, factual reporting).
4. Do NOT add your own opinions or commentary.
5. Output ONLY the translated summary text, no extra labels or headers.

Original article:
\"\"\"
{text[:4000]}
\"\"\""""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional news translator. Always respond in {target_lang} only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in translation: {e}")
        return None


def analyze_related_stocks(text: str) -> Dict[str, any]:
    """
    뉴스 본문을 분석하여 관련 주식 종목을 추천합니다.
    반환값:
        stocks: [
            {"name": "종목명", "impact": "Positive|Negative", "reason": "이유"},
            ...
        ]
    """
    fallback = {"stocks": []}

    if not client:
        return fallback

    if not text or len(text) < 50:
        return fallback

    prompt = f"""당신은 기업 분석 및 주식 포트폴리오 전략가입니다.
아래 뉴스 본문을 분석하여, 해당 이슈로 인해 직·간접적인 수혜를 보거나 리스크가 발생할 수 있는 관련 주식 종목을 추천하세요.

규칙:
1. 뉴스 내용과 가장 밀접하게 연관된 주식 종목(국내/해외 무관)을 최대 3개 도출하세요.
2. 각 종목의 impact는 반드시 "Positive" 또는 "Negative" 중 하나만 사용하세요.
3. reason은 해당 종목이 이 뉴스와 왜 연관이 있고, 주가에 어떤 영향을 미칠지 2문장 이내로 한국어로 설명하세요.
4. 반드시 JSON 형식으로만 답변하세요.

뉴스 본문:
\"\"\"
{text[:3000]}
\"\"\"

응답 예시:
{{"stocks": [
  {{"name": "삼성전자", "impact": "Negative", "reason": "반도체 업황 악화로 인해 영업이익 급감이 예상되며, 외국인 매도세가 지속되고 있습니다."}},
  {{"name": "SK하이닉스", "impact": "Negative", "reason": "메모리 반도체 시장의 전반적 침체로 동반 하락 압력을 받을 수 있습니다."}},
  {{"name": "ASML", "impact": "Negative", "reason": "반도체 장비 수요 감소가 예상되어 매출 성장에 부정적 영향이 우려됩니다."}}
]}}

반드시 위 JSON 형식으로만 답변하세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 기업 분석 및 주식 포트폴리오 전략가야. 반드시 JSON 형식으로만 응답해. impact 값은 반드시 Positive 또는 Negative만 사용해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        stocks = result.get("stocks", [])
        if not isinstance(stocks, list):
            return fallback
        # 각 종목 데이터 검증
        validated = []
        for s in stocks[:3]:
            if isinstance(s, dict) and "name" in s:
                s["impact"] = s.get("impact", "Positive") if s.get("impact") in ["Positive", "Negative"] else "Positive"
                s["reason"] = s.get("reason", "")
                validated.append(s)
        return {"stocks": validated}
    except Exception as e:
        print(f"Error in stock analysis: {e}")
        return fallback


if __name__ == "__main__":
    test_text = "삼성전자가 올 2분기 영업이익이 전년 대비 30% 급감할 것으로 전망된다고 발표했다. 반도체 업황 악화와 글로벌 수요 부진이 주된 원인으로 꼽힌다. 이에 따라 외국인 투자자들의 매도세가 이어지며 코스피 지수도 약세를 보이고 있다."
    print("Summary:", summarize_text(test_text))
    print("Keywords:", extract_keywords(test_text))
    print("Sentiment:", analyze_sentiment(test_text))
    print("Category:", classify_category(test_text))
    print("Translation:", translate_and_summarize(test_text, "English", "3줄 요약"))
    print("Stocks:", analyze_related_stocks(test_text))
