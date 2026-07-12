#!/usr/bin/env python3
"""
Scaffold một lần (chạy lại khi design site thay đổi):
1. templates/post.html       <- từ 1 trang bài viết mẫu, thay phần động bằng placeholder
2. templates/index.html     <- từ html/news/index.html
3. templates/project.html   <- từ 1 trang dự án mẫu (our-projects/golden-villa)
4. templates/projects-index.html <- từ html/our-projects/index.html
5. data/legacy-posts.json    <- quét metadata các bài viết tĩnh có sẵn (không do CMS tạo)
6. data/legacy-projects.json <- quét metadata các dự án tĩnh có sẵn

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

            <p class="post__meta">By {{AUTHOR}}</p>

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

    # 3b. Search overlay - Latest Projects
    s = re.sub(
        r'(<h4>Latest Projects</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        r"\1\n{{SEARCH_LATEST_PROJECTS}}\n            \2",
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
               "{{DATE_DISPLAY}}", "{{CONTENT}}", "{{AUTHOR}}", "{{RELATED_CARDS}}", "{{SEARCH_LATEST}}",
               "{{SEARCH_LATEST_PROJECTS}}"]:
        assert ph in s, "thiếu placeholder " + ph


def make_index_template():
    s = (HTML / "news" / "index.html").read_text(encoding="utf-8")
    s = re.sub(r'(<div class="news__grid">).*?(</div>)', r"\1\n{{NEWS_CARDS}}\n            \2", s, count=1, flags=re.S)
    s = re.sub(
        r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        r"\1\n{{SEARCH_LATEST}}\n            \2",
        s, count=1, flags=re.S,
    )
    s = re.sub(
        r'(<h4>Latest Projects</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        r"\1\n{{SEARCH_LATEST_PROJECTS}}\n            \2",
        s, count=1, flags=re.S,
    )
    out = ROOT / "templates" / "index.html"
    out.write_text(s, encoding="utf-8")
    print("wrote", out)
    assert "{{NEWS_CARDS}}" in s and "{{SEARCH_LATEST}}" in s and "{{SEARCH_LATEST_PROJECTS}}" in s



# ================= Dự án (our-projects) =================

P_SAMPLE = HTML / "our-projects" / "golden-villa" / "index.html"
P_TITLE = "GOLDEN VILLA"
P_URL = "https://mvngroup.vn/our-projects/golden-villa/"
P_IMG = "https://mvngroup.vn/our-projects/golden-villa/images/cover.jpg"
P_DATE = "26 Tháng 12, 2025"
P_ARCHITECT = "Ths. KTS Trương Anh Vương"


def make_project_template():
    s = P_SAMPLE.read_text(encoding="utf-8")

    # slider ảnh + fraction
    s = re.sub(r'<div class="pslider__slides">.*?</div>',
               '<div class="pslider__slides">\n{{SLIDER_IMAGES}}\n            </div>', s, count=1, flags=re.S)
    s = re.sub(r'id="psliderFraction">01/\d+<', 'id="psliderFraction">01/{{IMG_TOTAL}}<', s, count=1)

    # info block
    s = re.sub(r'(<h5>Location:</h5>\s*<span>).*?(</span>)', r'\1{{LOCATION}}\2', s, count=1, flags=re.S)
    s = re.sub(r'(<h5>Category:</h5>\s*<p>).*?(</p>)', r'\1{{CATEGORIES_DISPLAY}}\2', s, count=1, flags=re.S)

    # content
    s = re.sub(r'<div class="detail__content">.*?</div>',
               '<div class="detail__content">\n{{CONTENT}}\n            </div>', s, count=1, flags=re.S)

    # search overlay
    s = re.sub(r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
               r"\1\n{{SEARCH_LATEST}}\n            \2", s, count=1, flags=re.S)
    s = re.sub(r'(<h4>Latest Projects</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
               r"\1\n{{SEARCH_LATEST_PROJECTS}}\n            \2", s, count=1, flags=re.S)

    # chuỗi cụ thể -> placeholder (dài trước, ngắn sau)
    m = re.search(r'<meta name="description" content="(.*?)">', s)
    if m:
        s = s.replace(m.group(1), "{{DESCRIPTION}}")
    s = s.replace(P_IMG, "{{COVER_URL}}")
    s = s.replace(P_URL, "{{URL}}")
    s = s.replace(P_ARCHITECT, "{{ARCHITECT}}")
    s = s.replace(P_TITLE + " – MVN Group", "{{TITLE}} – MVN Group")
    s = s.replace(P_TITLE, "{{TITLE}}")
    s = s.replace('content="image/jpeg"', 'content="{{COVER_MIME}}"')
    s = s.replace(P_DATE, "{{DATE_DISPLAY}}")

    out = ROOT / "templates" / "project.html"
    out.write_text(s, encoding="utf-8")
    print("wrote", out)
    for ph in ["{{TITLE}}", "{{DESCRIPTION}}", "{{URL}}", "{{COVER_URL}}", "{{COVER_MIME}}", "{{SLIDER_IMAGES}}",
               "{{IMG_TOTAL}}", "{{ARCHITECT}}", "{{LOCATION}}", "{{DATE_DISPLAY}}", "{{CATEGORIES_DISPLAY}}",
               "{{CONTENT}}", "{{SEARCH_LATEST}}", "{{SEARCH_LATEST_PROJECTS}}"]:
        assert ph in s, "thiếu placeholder " + ph


def make_projects_index_template():
    s = (HTML / "our-projects" / "index.html").read_text(encoding="utf-8")
    s = re.sub(r'(<div class="catalog__grid" id="catalogGrid">).*?(</div>\s*<p class="catalog__empty")',
               r"\1\n{{PROJECT_CARDS}}\n            \2", s, count=1, flags=re.S)
    s = re.sub(r'(<h4>Latest News</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
               r"\1\n{{SEARCH_LATEST}}\n            \2", s, count=1, flags=re.S)
    s = re.sub(r'(<h4>Latest Projects</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
               r"\1\n{{SEARCH_LATEST_PROJECTS}}\n            \2", s, count=1, flags=re.S)
    out = ROOT / "templates" / "projects-index.html"
    out.write_text(s, encoding="utf-8")
    print("wrote", out)
    assert "{{PROJECT_CARDS}}" in s and "{{SEARCH_LATEST}}" in s and "{{SEARCH_LATEST_PROJECTS}}" in s


def scrape_legacy_projects():
    projects = []
    for d in sorted((HTML / "our-projects").iterdir()):
        page = d / "index.html"
        if not d.is_dir() or not page.exists():
            continue
        if (ROOT / "data" / "our-projects" / d.name / "project.json").exists():
            continue  # dự án do CMS quản lý, không phải legacy
        s = page.read_text(encoding="utf-8")

        def clean(text):
            prev = None
            while text != prev:
                prev, text = text, htmllib.unescape(text)
            return text.strip()

        def grab(pattern):
            m = re.search(pattern, s, flags=re.S)
            return clean(m.group(1)) if m else ""

        title = grab(r'<meta property="og:title" content="(.*?)"').replace(" – MVN Group", "").strip()
        desc = grab(r'<meta name="description" content="(.*?)"')
        architect = grab(r'<h5>Architect:</h5>\s*<span>(.*?)</span>')
        location = grab(r'<h5>Location:</h5>\s*<span>(.*?)</span>')
        date_disp = grab(r'<h5>Date:</h5>\s*<p>(.*?)</p>')
        cats = [c.strip() for c in grab(r'<h5>Category:</h5>\s*<p>(.*?)</p>').split("·") if c.strip()]

        iso = "2021-01-01"
        dm = VI_DATE.search(date_disp)
        if dm:
            day, mon, yr = dm.groups()
            iso = "%s-%02d-%02d" % (yr, int(mon), int(day))

        cover = ""
        for f in sorted((d / "images").glob("cover.*")) if (d / "images").exists() else []:
            cover = "our-projects/%s/images/%s" % (d.name, f.name)
            break

        projects.append({
            "id": "legacy-" + d.name,
            "slug": d.name,
            "title": title or d.name,
            "description": desc,
            "architect": architect,
            "location": location,
            "date": iso,
            "categories": cats,
            "cover": cover,
            "created_at": iso + "T00:00:00.000Z",
            "updated_at": iso + "T00:00:00.000Z",
        })

    projects.sort(key=lambda p: p["date"], reverse=True)
    out = ROOT / "data" / "legacy-projects.json"
    out.write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote %s (%d dự án)" % (out, len(projects)))


VI_DATE = re.compile(r"(\d{1,2}) Tháng (\d{1,2}), (\d{4})")


def scrape_legacy():
    posts = []
    for d in sorted((HTML / "news").iterdir()):
        page = d / "index.html"
        if not d.is_dir() or not page.exists():
            continue
        if (ROOT / "data" / "news" / d.name / "post.json").exists():
            continue  # bài do CMS quản lý, không phải legacy
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
    existing = [p for p in [ROOT / "templates" / "post.html", ROOT / "templates" / "index.html",
                            ROOT / "templates" / "project.html", ROOT / "templates" / "projects-index.html"] if p.exists()]
    if existing and not force:
        sys.exit("Template đã tồn tại (%s). Đây là file sửa tay — nếu thật sự muốn sinh lại từ trang có sẵn, chạy với --force." % ", ".join(str(x) for x in existing))
    make_post_template()
    make_index_template()
    make_project_template()
    make_projects_index_template()
    scrape_legacy()
    scrape_legacy_projects()
