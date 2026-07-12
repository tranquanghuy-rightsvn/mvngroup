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

## Ghi chú cho script build (CI/CD)

- Build đọc `posts.json` + từng `post.json`, generate `html/news/<slug>/index.html` (+ trang index/sitemap nếu cần).
- **Không đụng vào `html/news/<slug>/images/`** — ảnh đã nằm đúng chỗ do CMS ghi.
- CMS xoá bài / đổi slug sẽ tự xoá `data/news/<slug>` và `html/news/<slug>` tương ứng (kể cả `index.html` do CI tạo — CI build lại là xong).
