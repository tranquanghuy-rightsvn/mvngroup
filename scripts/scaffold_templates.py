#!/usr/bin/env python3
"""
Scaffold một lần (chạy lại khi design site thay đổi):
1. templates/post.html       <- từ 1 trang bài viết mẫu, thay phần động bằng placeholder
2. templates/index.html     <- từ html/news/index.html
3. data/legacy-posts.json    <- quét metadata các bài viết tĩnh có sẵn (không do CMS tạo)

LƯU Ý: templates/ là file SỬA TAY (source of truth của design).
Script này chỉ dùng để bootstrap lại từ trang có sẵn — sẽ KHÔNG ghi đè
template đang tồn tại trừ khi chạy với --force.

Chạy: python3 scripts/scaffold_templates.py [--force]
"""
import sys
import html as htmllib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "html"
SAMPLE = HTML / "news" / "international-world" / "index.html"

# Các giá trị cụ thể của trang mẫu -> placeholder
SAMPLE_TITLE = "Một ngày ở công trình"
SAMPLE_DESC = (
    "Theo chân đội ngũ chúng tôi từ sáng tới chiều, trải nghiệm nhịp sống tại công trường."
    "Những khoảnh khắc chân thật và hăng say của anh em công nhân."
)
SAMPLE_URL = "https://mvngroup.vn/news/international-world/"
SAMPLE_IMG = "https://mvngroup.vn/news/international-world/images/cover.jpg"
SAMPLE_DATE = "10 Tháng 6, 2025"

ARTICLE_BLOCK = """<article class="post">

            <p class="post__date">{{DATE_DISPLAY}}</p>
            <h1 class="post__title">{{TITLE}}</h1>

{{CONTENT}}

            <p class="post__meta">By MVN Group</p>

        </article>"""


def make_post_template():
    s = SAMPLE.read_text(encoding="utf-8")

    # 1. Article body
    s = re.sub(r'<article class="post">.*?</article>', ARTICLE_BLOCK, s, count=1, flags=re.S)

    # 2. Related cards
    s = re.sub(
        r'(<h2 class="related__title">.*?<div class="news__grid">).*?(</div>)',
        r"\1\n{{RELATED_CARDS}}\n            \2",
        s, count=1, flags=re.S,
    )

    # 3. Search overlay - Latest News
    s = re.sub(
        r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        r"\1\n{{SEARCH_LATEST}}\n            \2",
        s, count=1, flags=re.S,
    )

    # 4. Head/meta (thay chuỗi dài trước, chuỗi ngắn sau)
    s = s.replace(SAMPLE_IMG, "{{COVER_URL}}")
    s = s.replace(SAMPLE_URL, "{{URL}}")
    s = s.replace(SAMPLE_DESC, "{{DESCRIPTION}}")
    s = s.replace(SAMPLE_TITLE + " – MVN Group", "{{TITLE}} – MVN Group")
    s = s.replace(SAMPLE_TITLE, "{{TITLE}}")
    s = s.replace('content="image/jpeg"', 'content="{{COVER_MIME}}"')
    s = s.replace(SAMPLE_DATE, "{{DATE_DISPLAY}}")

    out = ROOT / "templates" / "post.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(s, encoding="utf-8")
    print("wrote", out)
    for ph in ["{{TITLE}}", "{{DESCRIPTION}}", "{{URL}}", "{{COVER_URL}}", "{{COVER_MIME}}",
               "{{DATE_DISPLAY}}", "{{CONTENT}}", "{{RELATED_CARDS}}", "{{SEARCH_LATEST}}"]:
        assert ph in s, "thiếu placeholder " + ph


def make_index_template():
    s = (HTML / "news" / "index.html").read_text(encoding="utf-8")
    s = re.sub(r'(<div class="news__grid">).*?(</div>)', r"\1\n{{NEWS_CARDS}}\n            \2", s, count=1, flags=re.S)
    s = re.sub(
        r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        r"\1\n{{SEARCH_LATEST}}\n            \2",
        s, count=1, flags=re.S,
    )
    out = ROOT / "templates" / "index.html"
    out.write_text(s, encoding="utf-8")
    print("wrote", out)
    assert "{{NEWS_CARDS}}" in s and "{{SEARCH_LATEST}}" in s


VI_DATE = re.compile(r"(\d{1,2}) Tháng (\d{1,2}), (\d{4})")


def scrape_legacy():
    posts = []
    for d in sorted((HTML / "news").iterdir()):
        page = d / "index.html"
        if not d.is_dir() or not page.exists():
            continue
        s = page.read_text(encoding="utf-8")

        def clean(text):
            # nguồn cũ có chỗ bị escape 2 lần (&amp;amp;) -> unescape tới khi ổn định
            prev = None
            while text != prev:
                prev, text = text, htmllib.unescape(text)
            return text.strip()

        m = re.search(r'<meta property="og:title" content="(.*?)"', s)
        title = clean((m.group(1) if m else d.name).replace(" – MVN Group", ""))
        m = re.search(r'<meta name="description" content="(.*?)"', s)
        desc = clean(m.group(1)) if m else ""
        m = re.search(r'<p class="post__date">(.*?)</p>', s)
        iso = "2021-01-01T00:00:00.000Z"
        disp = m.group(1).strip() if m else ""
        dm = VI_DATE.search(disp)
        if dm:
            day, mon, yr = dm.groups()
            iso = "%s-%02d-%02dT00:00:00.000Z" % (yr, int(mon), int(day))

        cover = ""
        for f in sorted((d / "images").glob("cover.*")) if (d / "images").exists() else []:
            cover = "news/%s/images/%s" % (d.name, f.name)
            break

        posts.append({
            "id": "legacy-" + d.name,
            "slug": d.name,
            "title": title,
            "description": desc,
            "cover": cover,
            "created_at": iso,
            "updated_at": iso,
        })

    posts.sort(key=lambda p: p["updated_at"], reverse=True)
    out = ROOT / "data" / "legacy-posts.json"
    out.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote %s (%d bài)" % (out, len(posts)))


if __name__ == "__main__":
    force = "--force" in sys.argv
    existing = [p for p in [ROOT / "templates" / "post.html", ROOT / "templates" / "index.html"] if p.exists()]
    if existing and not force:
        sys.exit("Template đã tồn tại (%s). Đây là file sửa tay — nếu thật sự muốn sinh lại từ trang có sẵn, chạy với --force." % ", ".join(str(x) for x in existing))
    make_post_template()
    make_index_template()
    scrape_legacy()
