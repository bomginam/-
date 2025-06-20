# collect_keywords.py – 무료판 Selenium 스크립트
"""
매일 60대 대상 황금 키워드 자동 수집기
1) 네이버 데이터랩(연령 60대) 실시간 키워드
2) YouTube Trending 영상 제목 키워드
3) 실버넷뉴스(시니어 커뮤니티) 최신 글 제목
결과를 keywords_YYYYMMDD.csv 로 저장
필요 패키지:
  pip install selenium webdriver-manager beautifulsoup4 pandas lxml
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time, re, pandas as pd, datetime, os

# ───────────────── Selenium 공통 설정 ─────────────────
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
DRIVER = webdriver.Chrome(service=service, options=opts)

# ───────────────── 1) 네이버 데이터랩 (60대) ─────────────────
def naver_keywords(age="60-"):
    url = f"https://datalab.naver.com/keyword/realtimeList.naver?age={age}"
    DRIVER.get(url)
    time.sleep(2)
    soup = BeautifulSoup(DRIVER.page_source, "lxml")
    kw = [tag.text.strip() for tag in soup.select(".item_title")]
    return kw

# ───────────────── 2) YouTube 트렌딩 ─────────────────
YOUTUBE_TITLE_CSS = "a#video-title"

def youtube_keywords(max_titles=25):
    DRIVER.get("https://www.youtube.com/feed/trending")
    time.sleep(3)
    soup = BeautifulSoup(DRIVER.page_source, "lxml")
    titles = [t.text.strip() for t in soup.select(YOUTUBE_TITLE_CSS)][:max_titles]
    # 간단 토큰화: 2~15글자 단어만 추출
    tokens = {
        tok.strip('"\' ,.!?').lower()
        for title in titles
        for tok in re.split(r"\s+", title)
        if 2 < len(tok) < 15 and tok.isalpha()
    }
    return list(tokens)

# ───────────────── 3) 실버넷뉴스 (시니어 커뮤니티) ─────────────────
def silvernet_keywords(max_posts=20):
    url = "https://www.silvernetnews.com/"
    DRIVER.get(url)
    time.sleep(2)
    soup = BeautifulSoup(DRIVER.page_source, "lxml")
    posts = [h.text.strip() for h in soup.select("h4.entry-title")]  # 구조 변경 시 수정
    tokens = {
        tok.lower()
        for title in posts[:max_posts]
        for tok in re.split(r"\W+", title)
        if 2 < len(tok) < 15 and tok.isalpha()
    }
    return list(tokens)

# ───────────────── 실행 & 저장 ─────────────────
if __name__ == "__main__":
    today_str = datetime.date.today().strftime("%Y%m%d")

    data = []
    for src, func in [("naver", naver_keywords),
                      ("youtube", youtube_keywords),
                      ("silvernet", silvernet_keywords)]:
        try:
            kws = func()
            for kw in kws:
                data.append({"date": today_str, "source": src, "keyword": kw})
        except Exception as e:
            print(f"[{src}] 수집 실패 →", e)

    DRIVER.quit()

    df = pd.DataFrame(data).drop_duplicates(subset=["keyword", "source"])
    out_path = f"keywords_{today_str}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✔ 저장 완료: {out_path}  (총 {len(df)}개)")
