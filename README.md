# News Insight Extractor

뉴스 사이트에서 뉴스를 수집하여 AI(OpenAI GPT-4o-mini)를 통해 요약하고 핵심 키워드를 추출하는 애플리케이션입니다.

## 주요 기능
- **Daum 뉴스 수집**: 메인 페이지의 주요 뉴스 링크를 자동으로 가져옵니다.
- **직접 URL 입력**: 특정 기사의 URL을 입력하여 분석할 수 있습니다.
- **본문 자동 파싱**: `newspaper3k`를 사용하여 기사 제목, 본문, 일자 등을 추출합니다.
- **AI 요약 및 키워드 추출**: GPT-4o-mini를 활용하여 전문적인 요약과 핵심 키워드를 제공합니다.
- **데이터 관리**: 분석된 결과는 SQLite DB에 저장되며, 검색 및 CSV 다운로드가 가능합니다.

## 설치 및 실행 방법

### 1. 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 입력하세요.
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 앱 실행
```bash
streamlit run app.py
```

## 기술 스택
- **Language**: Python 3.x
- **UI**: Streamlit
- **Crawl/Parse**: requests, BeautifulSoup4, newspaper3k
- **AI**: OpenAI API (GPT-4o-mini)
- **Database**: SQLite, Pandas
