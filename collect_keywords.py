"""
collect_keywords.py - Selenium 없이 작동하는 무료 키워드 수집기
1) YouTube 트렌딩 제목 키워드
2) 실버넷뉴스 최신 글 제목 키워드
결과: keywords_YYYYMMDD.csv 저장
필요 패키지: requests, bs4, pandas, lxml
"""
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# ───────────── 1) YouTube 트렌딩 ──────────────
def youtube_keywords(max_titles=30):
    url = "https://www.youtube.com/feed/trending"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "lxml")
    titles = [t.text.strip() for t in soup.select("a#video-title")][:max_titles]
    tokens = {
        tok.strip('"\' ,.!?').lower()
        for title in titles
        for tok in re.split(r"\s+", title)
        if 2 < len(tok) < 15 and tok.isalpha()
    }
    return list(tokens)

# ─────── 2) 실버넷뉴스 (시니어 커뮤니티) ────────
def silvernet_keywords(max_posts=20):
    url = "https://www.silvernetnews.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "lxml")
    posts = [h.text.strip() for h in soup.select("h4.entry-title")]
    tokens = {
        tok.lower()
        for title in posts[:max_posts]
        for tok in re.split(r"\W+", title)
        if 2 < len(tok) < 15 and tok.isalpha()
    }
    return list(tokens)

# ───────────── 실행 & 저장 ──────────────
if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y%m%d")

    data = []
    for src, func in [("youtube", youtube_keywords),
                      ("silvernet", silvernet_keywords)]:
        try:
            kws = func()
            for kw in kws:
                data.append({"date": today_str, "source": src, "keyword": kw})
        except Exception as e:
            print(f"[{src}] 수집 실패 →", e)

    df = pd.DataFrame(data).drop_duplicates(subset=["keyword", "source"])
    out_path = f"keywords_{today_str}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✔ 저장 완료: {out_path}  (총 {len(df)}개)")
