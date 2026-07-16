#!/usr/bin/env python3
"""
Build HTML tĩnh từ data/ (chạy bởi GitHub Actions, chỉ dùng stdlib).

Input:
  data/posts.json               # bài do CMS quản lý (GAS ghi)
  data/news/<slug>/post.json    # content HTML từng bài CMS
  data/legacy-posts.json        # metadata bài tĩnh có sẵn (không build lại trang)
  data/projects.json            # dự án do CMS quản lý (GAS ghi)
  data/our-projects/<slug>/project.json
  data/legacy-projects.json     # metadata dự án tĩnh có sẵn
  templates/post.html, templates/index.html, templates/project.html, templates/projects-index.html
  html/news/<slug>/images/*     # ảnh đã được CMS đẩy thẳng vào đây

Output:
  html/news/<slug>/index.html          # chỉ cho bài CMS
  html/news/index.html                 # danh sách tất cả bài (CMS + legacy)
  html/our-projects/<slug>/index.html  # chỉ cho dự án CMS
  html/our-projects/index.html         # danh sách tất cả dự án (CMS + legacy)
  html/index.html                      # trang chủ: latest news + 6 công trình mới nhất + search overlay
  html/search/index.html                # danh sách search (client-side filter theo title/description)
  html/sitemap.xml                     # URL bài viết + dự án

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



def project_card(p, prefix=""):
    """Card dự án (catalog grid /our-projects/ với prefix rỗng; trang chủ với prefix "/our-projects/").
    Ảnh cover mang view-transition-name để morph mượt sang ảnh đầu slider ở trang chi tiết (xem build_project_page)."""
    cats = p.get("categories") or []
    href = prefix + p["slug"] + "/"
    vt_name = "vt-proj-" + p["slug"]
    cat_spans = "\n".join('                        <span class="project-card__cat">%s</span>' % esc(c) for c in cats)
    return """                <article class="project-card" data-tags="%s">
                    <a href="%s"><img class="project-card__image" loading="lazy" alt="%s" src="%s" style="view-transition-name: %s"></a>
                    <div class="project-card__body">
                        <h3 class="project-card__title"><a href="%s">%s</a></h3>
                        <div class="project-card__cats">
%s
                    </div>
                        <div class="project-card__footer">
                            <a class="project-card__link" href="%s" aria-label="View %s"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9,5 16,12 9,19"></polyline></svg></a>
                        </div>
                    </div>
                </article>""" % (esc("|".join(cats)), href, esc(p["title"]), project_cover_of(p), vt_name,
                                href, esc(p["title"]), cat_spans, href, esc(p["title"]))


def project_cover_of(p):
    if p.get("cover"):
        return "/" + p["cover"]
    imgs = p.get("images") or []
    return ("/" + imgs[0]) if imgs else "/thumbnail.png"


def search_project_card(p):
    """Card dự án trong search overlay (Latest Projects)."""
    return """                <a class="search-overlay__card" href="/our-projects/%s/">
                    <img loading="lazy" alt="%s" src="%s">
                    <div>
                        <h5>%s</h5>
                        <p>%s</p>
                    </div>
                </a>""" % (p["slug"], esc(p["title"]), project_cover_of(p), esc(p["title"]), esc(truncate(p.get("description", ""))))


def search_item(p, kind):
    """
    Item trong html/search/index.html. data-search quyết định phạm vi khớp của ô tìm kiếm:
    - news: title + description
    - project: CHỈ title (theo yêu cầu nghiệp vụ)
    """
    if kind == "project":
        href = "/our-projects/" + p["slug"] + "/"
        img = project_cover_of(p)
        search_text = p["title"]
    else:
        href = "/news/" + p["slug"] + "/"
        img = cover_of(p)
        search_text = p["title"] + " " + (p.get("description") or "")
    return """        <a class="sr__item" data-kind="%s" data-search="%s" href="%s">
            <img loading="lazy" src="%s" alt="%s">
            <div>
                <h5>%s</h5>
                <p>%s</p>
            </div>
        </a>""" % (kind, esc(search_text), href, img, esc(p["title"]), esc(p["title"]), esc(p.get("description") or ""))


def build_search_page(merged, projects_merged):
    path = HTML / "search" / "index.html"
    if not path.exists():
        return
    s = path.read_text(encoding="utf-8")
    items = [search_item(p, "news") for p in merged] + [search_item(p, "project") for p in projects_merged]
    block = "\n".join(items)
    s, n = re.subn(
        r'(<div id="srList">).*?(\n\s*</div>\s*<p class="sr__empty")',
        lambda m: m.group(1) + "\n" + block + m.group(2),
        s, count=1, flags=re.S,
    )
    if not n:
        print("WARN: không tìm thấy #srList trong html/search/index.html — bỏ qua")
        return
    path.write_text(s, encoding="utf-8")
    print("built html/search/index.html (%d bài, %d dự án)" % (len(merged), len(projects_merged)))


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

def build_post_page(post, merged, projects, tpl):
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
        .replace("{{SEARCH_LATEST_PROJECTS}}", "\n".join(search_project_card(p) for p in projects[:3]))
    )
    out = HTML / "news" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("built", out.relative_to(ROOT))


def build_news_index(merged, projects, tpl):
    page = (
        tpl.replace("{{NEWS_CARDS}}", "\n\n".join(news_card(p) for p in merged))
        .replace("{{SEARCH_LATEST}}", "\n".join(search_card(p) for p in merged[:3]))
        .replace("{{SEARCH_LATEST_PROJECTS}}", "\n".join(search_project_card(p) for p in projects[:3]))
    )
    (HTML / "news" / "index.html").write_text(page, encoding="utf-8")
    print("built html/news/index.html")


def build_project_page(prj, posts_merged, projects_merged, tpl):
    slug = prj["slug"]
    cover = project_cover_of(prj)  # "/our-projects/.../cover.jpg" hoặc ảnh đầu
    ext = cover.rsplit(".", 1)[-1].lower() if "." in cover else "jpg"
    images = prj.get("images") or []

    vt_name = "vt-proj-" + slug
    slides = "\n".join(
        '                    <img%s loading="lazy" src="/%s" alt="%s %d"%s>'
        % (' class="is-active"' if i == 0 else "", img, esc(prj["title"]), i + 1,
           ' style="view-transition-name: %s"' % vt_name if i == 0 else "")
        for i, img in enumerate(images)
    )
    cats = prj.get("categories") or []

    page = (
        tpl.replace("{{TITLE}}", esc(prj["title"]))
        .replace("{{DESCRIPTION}}", esc(truncate(prj.get("description", ""), 220)))
        .replace("{{URL}}", "%s/our-projects/%s/" % (SITE, slug))
        .replace("{{COVER_URL}}", SITE + cover)
        .replace("{{COVER_MIME}}", MIME.get(ext, "image/jpeg"))
        .replace("{{SLIDER_IMAGES}}", slides)
        .replace("{{IMG_TOTAL}}", "%02d" % max(len(images), 1))
        .replace("{{ARCHITECT}}", esc(prj.get("architect", "")))
        .replace("{{LOCATION}}", esc(prj.get("location", "")))
        .replace("{{DATE_DISPLAY}}", date_display(prj.get("date") or prj.get("created_at")))
        .replace("{{CATEGORIES_DISPLAY}}", esc(" · ".join(cats)))
        .replace("{{CONTENT}}", transform_content(prj.get("content", ""), slug))
        .replace("{{SEARCH_LATEST}}", "\n".join(search_card(p) for p in posts_merged[:3]))
        .replace("{{SEARCH_LATEST_PROJECTS}}", "\n".join(search_project_card(p) for p in projects_merged[:3]))
    )
    out = HTML / "our-projects" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("built", out.relative_to(ROOT))


def build_projects_index(projects_merged, posts_merged, tpl):
    page = (
        tpl.replace("{{PROJECT_CARDS}}", "\n".join(project_card(p) for p in projects_merged))
        .replace("{{SEARCH_LATEST}}", "\n".join(search_card(p) for p in posts_merged[:3]))
        .replace("{{SEARCH_LATEST_PROJECTS}}", "\n".join(search_project_card(p) for p in projects_merged[:3]))
    )
    (HTML / "our-projects" / "index.html").write_text(page, encoding="utf-8")
    print("built html/our-projects/index.html")


def update_homepage(merged, projects_merged):
    """Cập nhật tại chỗ trang chủ: grid LATEST NEWS + search overlay (news + projects).
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
    searchprj = "\n".join(search_project_card(p) for p in projects_merged[:3])
    s = re.sub(
        r'(<h4>Latest Projects</h4>\s*<div class="search-overlay__grid">).*?(</div>\s*</div>)',
        lambda m: m.group(1) + "\n" + searchprj + "\n            " + m.group(2),
        s, count=1, flags=re.S,
    )
    # "Những công trình mới nhất": 6 dự án mới nhất trong dải kéo ngang
    scroller = "\n\n".join(project_card(p, "/our-projects/") for p in projects_merged[:6])
    s = re.sub(
        r'(<div class="projects__scroller">).*?(</div>\s*</section>)',
        lambda m: m.group(1) + "\n\n" + scroller + "\n\n        " + m.group(2),
        s, count=1, flags=re.S,
    )
    path.write_text(s, encoding="utf-8")
    print("built html/index.html (latest news + 6 công trình mới nhất + search overlay)")


def build_sitemap(merged, projects_merged):
    path = HTML / "sitemap.xml"
    s = path.read_text(encoding="utf-8")
    blocks = re.findall(r"[ \t]*<url>.*?</url>\n?", s, flags=re.S)
    kept = [b for b in blocks
            if not re.search(r"<loc>%s/news/.+</loc>" % re.escape(SITE), b)
            and not re.search(r"<loc>%s/our-projects/.+</loc>" % re.escape(SITE), b)]
    post_blocks = [
        "    <url>\n        <loc>%s/news/%s/</loc>\n        <lastmod>%s</lastmod>\n        <priority>0.6</priority>\n    </url>\n"
        % (SITE, p["slug"], parse_iso(p["updated_at"]).strftime("%Y-%m-%d"))
        for p in merged
    ]
    prj_blocks = [
        "    <url>\n        <loc>%s/our-projects/%s/</loc>\n        <lastmod>%s</lastmod>\n        <priority>0.6</priority>\n    </url>\n"
        % (SITE, p["slug"], parse_iso(p["updated_at"]).strftime("%Y-%m-%d"))
        for p in projects_merged
    ]
    out = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    out += "".join(kept) + "".join(post_blocks) + "".join(prj_blocks) + "</urlset>\n"
    path.write_text(out, encoding="utf-8")
    print("built html/sitemap.xml (%d bài viết, %d dự án)" % (len(post_blocks), len(prj_blocks)))


def merge_by_slug(legacy, cms, sort_key):
    by_slug = {}
    for p in legacy + cms:  # CMS ghi đè legacy nếu trùng slug
        by_slug[p["slug"]] = p
    return sorted(by_slug.values(), key=sort_key, reverse=True)


def main():
    cms = load_json(DATA / "posts.json", [])
    legacy = load_json(DATA / "legacy-posts.json", [])
    merged = merge_by_slug(legacy, cms, lambda p: str(p["created_at"]))

    cms_projects = load_json(DATA / "projects.json", [])
    legacy_projects = load_json(DATA / "legacy-projects.json", [])
    projects_merged = merge_by_slug(legacy_projects, cms_projects, lambda p: str(p.get("date") or p["created_at"]))

    post_tpl = (ROOT / "templates" / "post.html").read_text(encoding="utf-8")
    index_tpl = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    project_tpl = (ROOT / "templates" / "project.html").read_text(encoding="utf-8")
    projects_index_tpl = (ROOT / "templates" / "projects-index.html").read_text(encoding="utf-8")

    built = 0
    for p in cms:
        pj = DATA / "news" / p["slug"] / "post.json"
        if not pj.exists():
            print("WARN: thiếu", pj.relative_to(ROOT), "- bỏ qua")
            continue
        build_post_page(load_json(pj, {}), merged, projects_merged, post_tpl)
        built += 1

    built_prj = 0
    for p in cms_projects:
        pj = DATA / "our-projects" / p["slug"] / "project.json"
        if not pj.exists():
            print("WARN: thiếu", pj.relative_to(ROOT), "- bỏ qua")
            continue
        build_project_page(load_json(pj, {}), merged, projects_merged, project_tpl)
        built_prj += 1

    build_news_index(merged, projects_merged, index_tpl)
    build_projects_index(projects_merged, merged, projects_index_tpl)
    build_search_page(merged, projects_merged)
    update_homepage(merged, projects_merged)
    build_sitemap(merged, projects_merged)
    print("Done: %d bài + %d dự án CMS | tổng %d bài, %d dự án" % (built, built_prj, len(merged), len(projects_merged)))


if __name__ == "__main__":
    main()
