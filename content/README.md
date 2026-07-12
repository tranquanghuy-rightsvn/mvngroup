# Content — dữ liệu bài viết (do GAS CMS ghi vào)

Thư mục này là "database" bài viết của site. **Không sửa tay** — Google Apps Script CMS tự commit vào đây mỗi khi editor bấm Lưu/Xoá bài.

## Cấu trúc

```
content/
  posts.json                  # index toàn bộ bài viết (metadata, không có content)
  news/
    <slug>/
      post.json               # metadata + content HTML của 1 bài
      images/
        cover.<ext>           # ảnh đại diện
        01.<ext>, 02.<ext>... # ảnh trong bài, theo thứ tự xuất hiện
```

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

- `content`: HTML của bài. Ảnh trong content có `src` là đường dẫn tương đối `news/<slug>/images/NN.<ext>`; ảnh có caption nằm trong `<figure class="image"><img><figcaption>`.
- `images`: mảng đường dẫn ảnh của bài.

## Ghi chú cho script build (CI/CD)

- Build đọc `posts.json` + từng `post.json`, generate HTML tĩnh vào `html/` (thư mục `html/` do CI/CD quản lý, CMS không đụng vào).
- Ảnh copy từ `content/news/<slug>/images/` sang vị trí tương ứng dưới `html/` sao cho đường dẫn `news/<slug>/images/NN.<ext>` trong content resolve đúng.
