import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_NAME = "news_insight.db"

def init_db():
    """
    데이터베이스와 테이블을 초기화합니다.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            text TEXT,
            summary TEXT,
            keywords TEXT,
            sentiment TEXT,
            sentiment_reason TEXT,
            impact_score INTEGER,
            category TEXT DEFAULT 'Other',
            category_keywords TEXT DEFAULT '',
            publish_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 기존 DB 마이그레이션: 컬럼이 없으면 추가
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(news)").fetchall()]
    for col, col_def in [
        ("sentiment", "TEXT DEFAULT '중립(Neutral)'"),
        ("sentiment_reason", "TEXT DEFAULT ''"),
        ("impact_score", "INTEGER DEFAULT 0"),
        ("category", "TEXT DEFAULT 'Other'"),
        ("category_keywords", "TEXT DEFAULT ''")
    ]:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE news ADD COLUMN {col} {col_def}")
    conn.commit()
    conn.close()

def save_news(news_data: Dict[str, Any]):
    """
    뉴스 데이터를 저장합니다. 이미 존재하는 URL은 무시하거나 업데이트할 수 있습니다.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    sentiment_data = news_data.get('sentiment_analysis', {})
    category_data = news_data.get('category_analysis', {})
    try:
        cursor.execute('''
            INSERT INTO news (url, title, text, summary, keywords, sentiment, sentiment_reason, impact_score, category, category_keywords, publish_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            text=excluded.text,
            summary=excluded.summary,
            keywords=excluded.keywords,
            sentiment=excluded.sentiment,
            sentiment_reason=excluded.sentiment_reason,
            impact_score=excluded.impact_score,
            category=excluded.category,
            category_keywords=excluded.category_keywords,
            publish_date=excluded.publish_date
        ''', (
            news_data['url'],
            news_data['title'],
            news_data['text'],
            news_data.get('summary', ''),
            ",".join(news_data.get('keywords', [])),
            sentiment_data.get('sentiment', '중립(Neutral)'),
            sentiment_data.get('reason', ''),
            sentiment_data.get('impact_score', 0),
            category_data.get('category', 'Other'),
            ",".join(category_data.get('category_keywords', [])),
            news_data.get('publish_date', '')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving news to DB: {e}")
    finally:
        conn.close()

def get_all_news() -> pd.DataFrame:
    """
    저장된 모든 뉴스 데이터를 DataFrame으로 가져옵니다.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM news ORDER BY created_at DESC", conn)
    conn.close()
    return df

def delete_news(news_id: int):
    """
    특정 뉴스를 삭제합니다.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()
    conn.close()

def delete_all_news():
    """
    저장된 모든 뉴스를 삭제합니다.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
