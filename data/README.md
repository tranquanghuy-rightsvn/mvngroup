# Content — dữ liệu bài viết (do GAS CMS ghi vào)

Thư mục này là "database" bài viết của site. **Không sửa tay** — Google Apps Script CMS tự commit vào đây mỗi khi editor bấm Lưu/Xoá bài.

## Phân công thư mục

| Đường dẫn | Ai ghi | Nội dung |
|---|---|---|
| `data/posts.json` | CMS | Index metadata toàn bộ bài viết |
| `data/news/<slug>/post.json` | CMS | Metadata + content HTML của 1 bài |
| `html/news/<slug>/images/*` | CMS | Cover + ảnh trong bài — ghi **thẳng vào site** để không duplicate ảnh |
| `html/news/<slug>/index.html` | CI/CD | Trang bài viết, generate từ `post.json` |
| `html/` còn lại | CI/CD | Website chính |

## Format

`posts.json` — mảng metadata, sắp xếp theo `updated_at` giảm dần:

```json
[
  {
    "id": "uuid",
    "slug": "bai-viet-mau",
    "title": "Bài viết mẫu",
    "description": "Mô tả ngắn",
    "cover": "news/bai-viet-mau/images/cover.jpg",
    "created_at": "2026-07-12T00:00:00.000Z",
    "updated_at": "2026-07-12T00:00:00.000Z"
  }
]
```

`news/<slug>/post.json` — như trên, thêm 2 field:

- `content`: HTML của bài. Ảnh trong content có `src` là đường dẫn tương đối `news/<slug>/images/NN.<ext>` — trùng khớp vị trí thật của ảnh dưới `html/`, nên build không phải xử lý gì về ảnh; ảnh có caption nằm trong `<figure class="image"><img><figcaption>`.
- `images`: mảng đường dẫn ảnh của bài.

## CI/CD (đã có: `.github/workflows/build.yml`)

- Trigger khi có commit vào `data/**` (chính là các commit của GAS CMS) → chạy `scripts/build.py` → commit kết quả vào `html/` → Vercel deploy.
- `scripts/build.py` (stdlib Python, chạy local được): generate `html/news/<slug>/index.html` cho từng bài CMS, build lại trang danh sách `html/news/index.html` và `html/sitemap.xml` từ `posts.json` + `legacy-posts.json`.
- `data/legacy-posts.json`: metadata 11 bài tĩnh có sẵn (không do CMS tạo) — GAS **không** đụng file này; trang của các bài legacy giữ nguyên, chỉ được liệt kê ở trang danh sách/sitemap/related.
- **Muốn chỉnh design trang bài viết / trang danh sách: sửa trực tiếp `templates/post.html` và `templates/index.html`** (HTML đầy đủ, phần dữ liệu động là placeholder `{{...}}`), rồi để CI build lại (hoặc chạy `python3 scripts/build.py`). Đây là source of truth của design — đừng sửa thẳng file trong `html/news/` vì sẽ bị build ghi đè. `scripts/scaffold_templates.py` chỉ là công cụ bootstrap, có chốt chặn không ghi đè template trừ khi `--force`.
- Build **không đụng** `html/news/<slug>/images/` — ảnh do CMS ghi thẳng vào.
- CMS xoá bài / đổi slug sẽ tự xoá `data/news/<slug>` và `html/news/<slug>`; CI build lại danh sách là hết dấu vết.
