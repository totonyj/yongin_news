"""
GitHub Actions에서 실행되는 Supabase 동기화 스크립트.
data/articles/*.json, data/keywords/*.json 을 읽어서 Supabase에 upsert.
"""
import os, json, requests, glob

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
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, headers=headers(prefer), json=rows)
    if res.status_code not in (200, 201):
        print(f"  ❌ {table} 오류 {res.status_code}: {res.text[:300]}")
    else:
        print(f"  ✅ {table} {len(rows)}건 저장")

# ── 기사 동기화 ───────────────────────────────────────────────
article_files = sorted(glob.glob("data/articles/*.json"))
print(f"기사 파일 {len(article_files)}개 발견")

for fpath in article_files:
    with open(fpath, encoding="utf-8") as f:
        articles = json.load(f)
    if not isinstance(articles, list):
        continue
    # date 필드: RFC 2822 → Supabase가 자동 파싱
    upsert("news_articles", articles, "resolution=ignore-duplicates")

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
    upsert("daily_keywords", rows, "resolution=merge-duplicates")

print("동기화 완료!")
