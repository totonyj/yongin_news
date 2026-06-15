"""
GitHub Actions에서 실행되는 Supabase 동기화 스크립트.
data/articles/*.json, data/keywords/*.json 을 읽어서 Supabase에 upsert.
"""
import os, json, requests, glob
from email.utils import parsedate_to_datetime

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

def headers(prefer="resolution=ignore-duplicates"):
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }

def upsert(table, rows, prefer="resolution=ignore-duplicates"):
    if not rows:
        print(f"  ⚠️  {table} 저장할 데이터 없음")
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, headers=headers(prefer), json=rows)
    if res.status_code not in (200, 201):
        print(f"  ❌ {table} 오류 {res.status_code}: {res.text[:300]}")
    else:
        print(f"  ✅ {table} {len(rows)}건 저장 완료")

def parse_date(date_str):
    """RFC 2822 → ISO 8601 변환. 실패 시 None 반환."""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except Exception:
        return None

# ── 기사 동기화 ───────────────────────────────────────────────
article_files = sorted(glob.glob("data/articles/*.json"))
print(f"기사 파일 {len(article_files)}개 발견")

for fpath in article_files:
    with open(fpath, encoding="utf-8") as f:
        articles = json.load(f)
    if not isinstance(articles, list):
        print(f"  ⚠️  {fpath} 형식 오류 (list가 아님)")
        continue

    print(f"  {fpath}: {len(articles)}건 처리 중...")

    rows = []
    for a in articles:
        rows.append({
            "link":         a.get("link", ""),
            "title":        a.get("title", ""),
            "publisher":    a.get("publisher", ""),
            "date":         parse_date(a.get("date", "")),   # RFC 2822 → ISO 변환
            "collected_at": a.get("collected", "")
        })

    # link가 비어있는 행 제거
    rows = [r for r in rows if r["link"]]
    upsert("news_articles", rows, "resolution=ignore-duplicates")

# ── 키워드 동기화 ─────────────────────────────────────────────
keyword_files = sorted(glob.glob("data/keywords/*.json"))
print(f"키워드 파일 {len(keyword_files)}개 발견")

for fpath in keyword_files:
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)

    date_str = data.get("date", "")
    rows = [
        {"date": date_str, "keyword": kw["keyword"], "count": kw["count"]}
        for kw in data.get("keywords", [])
    ]
    print(f"  {fpath}: {len(rows)}개 키워드 처리 중...")
    upsert("daily_keywords", rows, "resolution=merge-duplicates")

print("동기화 완료!")
