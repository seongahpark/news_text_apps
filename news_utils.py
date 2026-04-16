import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# 안정적인 User-Agent 설정
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}


def get_daum_main_news_links() -> List[str]:
    """
    Daum 뉴스 메인에서 주요 뉴스 링크를 수집합니다.
    """
    url = "https://news.daum.net/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'v.daum.net/v/' in href:
                if href not in news_links:
                    news_links.append(href)
        return news_links
    except Exception as e:
        print(f"Error fetching Daum news: {e}")
        return []


def extract_article_content(url: str) -> Optional[Dict[str, str]]:
    """
    URL에서 기사 제목, 본문, 발행일을 추출합니다.
    newspaper 라이브러리에 의존하지 않고, BeautifulSoup으로 직접 파싱합니다.
    Daum 뉴스(v.daum.net) 구조에 최적화되어 있으며, 기타 사이트도 지원합니다.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # ──────────────── 제목 추출 (우선순위 순) ────────────────
        title = _extract_title(soup)

        # ──────────────── 본문 추출 (우선순위 순) ────────────────
        text = _extract_body(soup)

        # ──────────────── 발행일 추출 ────────────────
        publish_date = _extract_date(soup)

        if not title and not text:
            print(f"[WARN] 제목과 본문 모두 추출 실패: {url}")
            return None

        return {
            'title': title or "(제목 없음)",
            'text': text or "",
            'authors': [],
            'publish_date': publish_date,
            'top_image': "",
            'url': url
        }

    except Exception as e:
        print(f"Error extracting article from {url}: {e}")
        return None


def _extract_title(soup: BeautifulSoup) -> str:
    """
    기사 제목을 다양한 방법으로 추출합니다.
    Daum 뉴스의 h3.tit_view → og:title 메타 → title 태그 순으로 시도합니다.
    """
    # 1) Daum 뉴스 전용: h3.tit_view
    tit_node = soup.find('h3', class_='tit_view')
    if tit_node and tit_node.text.strip():
        return tit_node.text.strip()

    # 2) Open Graph meta tag (가장 범용적이고 신뢰도 높음)
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content', '').strip():
        return og_title['content'].strip()

    # 3) <title> 태그 (마지막 수단)
    if soup.title and soup.title.text.strip():
        return soup.title.text.strip()

    return ""


def _extract_body(soup: BeautifulSoup) -> str:
    """
    기사 본문을 다양한 방법으로 추출합니다.
    Daum 뉴스의 article_view div → 일반적인 article 태그 순으로 시도합니다.
    """
    # 1) Daum 뉴스 전용: div.article_view
    article_body = soup.find('div', class_='article_view')
    if article_body:
        return article_body.get_text(separator='\n', strip=True)

    # 2) 일반적인 article 태그
    article_tag = soup.find('article')
    if article_tag:
        return article_tag.get_text(separator='\n', strip=True)

    # 3) og:description (최소한의 정보)
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content', '').strip():
        return og_desc['content'].strip()

    return ""


def _extract_date(soup: BeautifulSoup) -> str:
    """
    기사 발행일을 추출합니다.
    """
    # 1) Daum 뉴스 전용: span.num_date
    date_span = soup.find('span', class_='num_date')
    if date_span:
        return date_span.text.strip()

    # 2) meta article:published_time
    meta_date = soup.find('meta', property='article:published_time')
    if meta_date and meta_date.get('content', ''):
        return meta_date['content'].strip()

    # 3) time 태그
    time_tag = soup.find('time')
    if time_tag:
        return time_tag.get('datetime', time_tag.text).strip()

    return ""


if __name__ == "__main__":
    links = get_daum_main_news_links()
    print(f"Found {len(links)} links")
    for i, link in enumerate(links[:3]):
        print(f"\n--- Article {i+1}: {link} ---")
        content = extract_article_content(link)
        if content:
            print(f"  Title: {content['title']}")
            print(f"  Date:  {content['publish_date']}")
            print(f"  Body:  {content['text'][:100]}...")
        else:
            print("  [FAIL] Could not extract content.")
