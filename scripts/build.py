#!/usr/bin/env python3
"""
Build HTML tĩnh từ data/ (chạy bởi GitHub Actions, chỉ dùng stdlib).

Input:
  data/posts.json               # bài do CMS quản lý (GAS ghi)
  data/news/<slug>/post.json    # content HTML từng bài CMS
  data/legacy-posts.json        # metadata bài tĩnh có sẵn (không build lại trang)
  templates/post.html, templates/index.html
  html/news/<slug>/images/*     # ảnh đã được CMS đẩy thẳng vào đây

Output:
  html/news/<slug>/index.html   # chỉ cho bài CMS
  html/news/index.html          # danh sách tất cả bài (CMS + legacy)
  html/sitemap.xml              # cập nhật URL bài viết

Chạy local để thử: python3 scripts/build.py
"""
import html as htmllib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "html"
DATA = ROOT / "data"
SITE = "https://mvngroup.vn"

MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml"}


def esc(s):
    return htmllib.escape(s or "", quote=True)


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def parse_iso(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return datetime(2021, 1, 1, tzinfo=timezone.utc)


def date_display(iso):
    d = parse_iso(iso)
    return "%d Tháng %d, %d" % (d.day, d.month, d.year)


def cover_of(p):
    return ("/" + p["cover"]) if p.get("cover") else "/thumbnail.png"


def truncate(s, n=110):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


# ---------- card renderers ----------

def news_card(p):
    """Card trong html/news/index.html (đường dẫn tương đối với /news/)."""
    desc = ""
    if p.get("description"):
        desc = '\n                    <p class="news-card__desc">%s</p>' % esc(truncate(p["description"], 160))
    return """                <a href="%s/" class="news-card">
                    <img class="news-card__image" loading="lazy" alt="%s"
                        src="%s">
                    <span class="news-card__date">%s</span>
                    <h3 class="news-card__title">%s</h3>%s
                </a>""" % (p["slug"], esc(p["title"]), cover_of(p), date_display(p["created_at"]), esc(p["title"]), desc)


def related_card(p):
    """Card 'Bài viết liên quan' trong trang bài viết."""
    return """                <a href="/news/%s/" class="news-card">
                    <img class="news-card__image" loading="lazy" alt="%s"
                        src="%s">
                    <span class="news-card__date">%s</span>
                    <h3 class="news-card__title">%s</h3>
                </a>""" % (p["slug"], esc(p["title"]), cover_of(p), date_display(p["created_at"]), esc(p["title"]))


def search_card(p):
    """Card trong search overlay (Latest News)."""
    return """                <a class="search-overlay__card" href="/news/%s/">
                    <img loading="lazy" alt="%s" src="%s">
                    <div>
                        <h5>%s</h5>
                        <p>%s</p>
                    </div>
                </a>""" % (p["slug"], esc(p["title"]), cover_of(p), esc(p["title"]), esc(truncate(p.get("description", ""))))


# ---------- content transform ----------

def transform_content(content, slug):
    # src tương đối news/<slug>/images/.. -> tuyệt đối /news/<slug>/images/..
    content = re.sub(r'src="news/', 'src="/news/', content)
    content = re.sub(r"src='news/", "src='/news/", content)
    # lazy-load ảnh
    content = re.sub(r"<img (?!loading)", '<img loading="lazy" ', content)
    # thụt lề cho đẹp nguồn trang
    return "\n".join("            " + line if line.strip() else line for line in content.splitlines())


# ---------- builders ----------

def build_post_page(post, merged, tpl):
    slug = post["slug"]
    cover = post.get("cover") or ""
    ext = cover.rsplit(".", 1)[-1].lower() if "." in cover else "jpg"
    related = [p for p in merged if p["slug"] != slug][:3]
    latest = merged[:3]

    page = (
        tpl.replace("{{TITLE}}", esc(post["title"]))
        .replace("{{DESCRIPTION}}", esc(post.get("description", "")))
        .replace("{{URL}}", "%s/news/%s/" % (SITE, slug))
        .replace("{{COVER_URL}}", SITE + cover_of(post))
        .replace("{{COVER_MIME}}", MIME.get(ext, "image/jpeg"))
        .replace("{{DATE_DISPLAY}}", date_display(post["created_at"]))
        .replace("{{AUTHOR}}", esc(post.get("author") or "MVN Group"))
        .replace("{{CONTENT}}", transform_content(post.get("content", ""), slug))
        .replace("{{RELATED_CARDS}}", "\n\n".join(related_card(p) for p in related))
        .replace("{{SEARCH_LATEST}}", "\n".join(search_card(p) for p in latest))
    )
    out = HTML / "news" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("built", out.relative_to(ROOT))


def build_news_index(merged, tpl):
    page = tpl.replace("{{NEWS_CARDS}}", "\n\n".join(news_card(p) for p in merged)).replace(
        "{{SEARCH_LATEST}}", "\n".join(search_card(p) for p in merged[:3])
    )
    (HTML / "news" / "index.html").write_text(page, encoding="utf-8")
    print("built html/news/index.html")


def update_homepage(merged):
    """Cập nhật tại chỗ 2 khối trên trang chủ: grid LATEST NEWS + search overlay (3 bài mới nhất).
    Phần còn lại của html/index.html giữ nguyên (trang chủ vẫn sửa tay được)."""
    path = HTML / "index.html"
    if not path.exists():
        return
    s = path.read_text(encoding="utf-8")
    top3 = merged[:3]

    cards = "\n\n".join(related_card(p) for p in top3)
    s = re.sub(
        r'(<section class="section--news">.*?<div class="news__grid">).*?(</div>)',
        lambda m: m.group(1) + "\n" + cards + "\n            " + m.group(2),
        s, count=1, flags=re.S,
    )
    search = "\n".join(search_card(p) for p in top3)
    s = re.sub(
        r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        lambda m: m.group(1) + "\n" + search + "\n            " + m.group(2),
        s, count=1, flags=re.S,
    )
    path.write_text(s, encoding="utf-8")
    print("built html/index.html (latest news + search overlay)")


def build_sitemap(merged):
    path = HTML / "sitemap.xml"
    s = path.read_text(encoding="utf-8")
    blocks = re.findall(r"[ \t]*<url>.*?</url>\n?", s, flags=re.S)
    kept = [b for b in blocks if not re.search(r"<loc>%s/news/.+</loc>" % re.escape(SITE), b)]
    post_blocks = [
        "    <url>\n        <loc>%s/news/%s/</loc>\n        <lastmod>%s</lastmod>\n        <priority>0.6</priority>\n    </url>\n"
        % (SITE, p["slug"], parse_iso(p["updated_at"]).strftime("%Y-%m-%d"))
        for p in merged
    ]
    out = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    out += "".join(kept) + "".join(post_blocks) + "</urlset>\n"
    path.write_text(out, encoding="utf-8")
    print("built html/sitemap.xml (%d url bài viết)" % len(post_blocks))


def main():
    cms = load_json(DATA / "posts.json", [])
    legacy = load_json(DATA / "legacy-posts.json", [])

    by_slug = {}
    for p in legacy + cms:  # CMS ghi đè legacy nếu trùng slug
        by_slug[p["slug"]] = p
    merged = sorted(by_slug.values(), key=lambda p: str(p["created_at"]), reverse=True)

    post_tpl = (ROOT / "templates" / "post.html").read_text(encoding="utf-8")
    index_tpl = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")

    built = 0
    for p in cms:
        pj = DATA / "news" / p["slug"] / "post.json"
        if not pj.exists():
            print("WARN: thiếu", pj.relative_to(ROOT), "- bỏ qua")
            continue
        build_post_page(load_json(pj, {}), merged, post_tpl)
        built += 1

    build_news_index(merged, index_tpl)
    update_homepage(merged)
    build_sitemap(merged)
    print("Done: %d bài CMS, %d bài tổng (gồm %d legacy)" % (built, len(merged), len(legacy)))


if __name__ == "__main__":
    main()
