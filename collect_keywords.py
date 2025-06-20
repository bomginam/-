# collect_keywords.py – GitHub Actions용 Selenium‑less 버전
"""
60대 타깃 ‘황금 키워드’ 자동 수집기 (requests + BeautifulSoup 전용)
1) 네이버 데이터랩(연령 60대) – 가벼운 HTML 구간만 파싱 시도
2) YouTube Trending – 제목 태그에서 키워드 토큰 추출
3) 실버넷뉴스 – 최신 기사 제목 토큰 추출

결과: keywords_YYYYMMDD.csv 로 저장
필요 패키지:
    pip install requests beautifulsoup4 pandas lxml
"""
import requests, re, pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, date

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ───────────────── 1) 네이버 데이터랩 ─────────────────

def naver_keywords(age: str = "60-") -> list:
    url = f"https://datalab.naver.com/keyword/realtimeList.naver?age={age}"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "lxml")
        return [tag.text.strip() for tag in soup.select(".item_title")]
    except Exception as e:
        print("[naver] 수집 실패 →", e)
        return []

# ───────────────── 2) YouTube Trending ─────────────────

def youtube_keywords(max_titles: int = 25) -> list:
    url = "https://www.youtube.com/feed/trending"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "lxml")
        titles = [t.get_text(strip=True) for t in soup.select("a#video-title")][:max_titles]
        tokens = {
            tok.lower()
            for title in titles
            for tok in re.split(r"\W+", title)
            if 2 < len(tok) < 15 and tok.isalpha()
        }
        return list(tokens)
    except Exception as e:
        print("[youtube] 수집 실패 →", e)
        return []

# ───────────────── 3) 실버넷뉴스 ─────────────────

def silvernet_keywords(max_posts: int = 20) -> list:
    url = "https://www.silvernetnews.com/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "lxml")
        posts = [h.get_text(strip=True) for h in soup.select("h4.entry-title")][:max_posts]
        tokens = {
            tok.lower()
            for title in posts
            for tok in re.split(r"\W+", title)
            if 2 < len(tok) < 15 and tok.isalpha()
        }
        return list(tokens)
    except Exception as e:
        print("[silvernet] 수집 실패 →", e)
        return []

# ───────────────── 실행 & CSV 저장 ─────────────────
if __name__ == "__main__":
    today = date.today().strftime("%Y%m%d")
    rows = []
    for src, func in [
        ("naver", naver_keywords),
        ("youtube", youtube_keywords),
        ("silvernet", silvernet_keywords),
    ]:
        for kw in func():
            rows.append({"date": today, "source": src, "keyword": kw})

    df = pd.DataFrame(rows).drop_duplicates(subset=["keyword", "source"])
    out_file = f"keywords_{today}.csv"
    df.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"✔ 저장 완료: {out_file} (총 {len(df)}개)")
