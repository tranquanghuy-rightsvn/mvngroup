# MVN Group — Website + CMS pipeline

Repo backend của mvngroup.vn: chứa dữ liệu bài viết/dự án (do GAS CMS ghi), site tĩnh (`html/`), template và CI build.

## Kiến trúc

```
GAS CMS (Google Apps Script + Sheets + Drive tạm)
   │  commit qua GitHub Contents API
   ▼
repo này: data/ (nguồn dữ liệu) ──► GitHub Actions build ──► html/ ──► Vercel deploy
```

| Đường dẫn | Ai ghi | Nội dung |
|---|---|---|
| `data/posts.json`, `data/news/<slug>/post.json` | CMS | Bài viết (metadata + content) |
| `data/projects.json`, `data/our-projects/<slug>/project.json` | CMS | Dự án |
| `data/legacy-posts.json`, `data/legacy-projects.json` | scaffold (1 lần) | Metadata bài/dự án tĩnh có sẵn — GAS không đụng |
| `html/news|our-projects/<slug>/images/*` | CMS | Ảnh, ghi thẳng vào site |
| `html/**/index.html` (bài viết, dự án, listing), sitemap, trang chủ (2 vùng) | CI | Build từ `templates/` + `data/` |
| `templates/*.html` | **sửa tay** | Source of truth của design (đừng sửa thẳng html/ của trang build) |
| `scripts/build.py` | sửa tay | Builder (stdlib Python, chạy local được) |
| `scripts/scaffold_templates.py` | công cụ | Sinh lại template từ trang có sẵn (`--force` mới ghi đè) |

- CI trigger **chỉ** ở `data/posts.json` / `data/projects.json` — luôn là commit chốt của mỗi thao tác Lưu/Xoá → không build trạng thái dở dang, 1 thao tác = 1 run.
- Trang chủ không có template — build "vá tại chỗ" 4 vùng: grid LATEST NEWS, 2 khối search overlay, dải `projects__scroller` (6 dự án mới nhất). Khi redesign trang chủ phải giữ các mốc neo đó.

## Ghi chú quota deploy (chốt 2026-07-12: TẠM GIỮ NGUYÊN, chưa làm gì)

**Hiện trạng:** mỗi file CMS ghi = 1 commit = 1 push = 1 deploy Vercel. Lưu dự án K ảnh ≈ K+3 deploy.

**Giới hạn Vercel Hobby (tính theo ACCOUNT, các project chia chung):**
- 100 deploy/ngày cho cả account — nhiều site chung account (mvngroup, coinguonvn, meovat360, trithucworld...) chia nhau hồ này; chạm trần là mọi project ngừng deploy tới hết ngày.
- Bandwidth 100GB/tháng cả account; Hobby chỉ cho dùng phi thương mại (site doanh nghiệp đang ở vùng xám).

**Các phương án đã bàn (chưa chọn):**
1. **0đ, vá tại chỗ:** CI ghi thêm `html/.build-stamp` (để luôn có commit build) + Vercel "Ignored Build Step" chỉ deploy commit `CI: build*` (mở rộng thêm tag `[deploy]` cho push tay). Rủi ro đã biết: bản deploy bị skip vẫn tạo record Canceled — CHƯA RÕ có tính vào quota 100/ngày không, cần theo dõi thực tế.
2. **0đ, sạch dài hạn:** chuyển mvngroup sang **Cloudflare Pages** — build watch paths trỏ vào file stamp (push bị lọc KHÔNG tính quota, chắc chắn hơn Vercel), hoặc deploy trực tiếp từ Actions bằng wrangler; bandwidth không giới hạn. Chi phí migrate: chuyển 4 rule redirect trong `html/vercel.json` sang file `_redirects`, trỏ lại DNS.
3. **Trả phí:** Vercel Pro $20/tháng/seat — ~6.000 deploy/ngày, 1TB bandwidth, hợp lệ thương mại, cả account hưởng. "Mua sự yên tâm".
4. **Tối ưu gốc (độc lập với 1-3):** GAS chuyển từ Contents API sang **Git Data API (trees)** → 1 thao tác = 1 commit atomic, upload blob song song. Trade-off: code phức tạp hơn nhiều + phải xử lý retry khi ref bị đua (CI push cùng lúc) + tự quản lý xoá file trong tree.

**Khuyến nghị đang treo:** nếu viết nhiều → phương án 2 (Cloudflare) hoặc 3 (Pro); nhịp hiện tại thì chưa cần đổi gì.

## Mô hình kinh doanh nhiều khách hàng (ghi chú 2026-07-13 — định hướng, chưa triển khai)

Mục tiêu: nhân bản mô hình này cho nhiều KH, **mọi hạ tầng đứng tên mình**, thu phí vận hành/năm (managed service).

### Stack chuẩn cho mỗi khách (chi phí biến đổi ≈ 0đ/khách)

| Mảnh | Cách làm | Lý do / quota |
|---|---|---|
| GitHub | 1 account của mình + **mỗi KH 1 organization free** (mình sở hữu) | Org free không giới hạn, hợp lệ ToS (KHÔNG lập nhiều account cá nhân — vi phạm, rủi ro khoá dây chuyền). Mỗi org có 2.000 phút Actions/tháng riêng → repo private thoải mái (~2-4k build/tháng/KH). Repo public = Actions không giới hạn nhưng lộ source/design — hỏi KH trước. |
| Hosting | **Cloudflare Pages**, 1 account của mình, mỗi KH 1 project | Free cho phép thương mại + bandwidth KHÔNG giới hạn (khoá rủi ro lớn nhất của phí cố định/năm). Deploy bằng wrangler từ Actions → không ăn quota build. Giới hạn ~100 project/account → gần đủ 100 KH thì mở account pháp nhân thứ hai. Cần chuyển vercel.json → `_redirects` khi migrate. |
| Google (GAS/Sheets/Drive) | Bắt đầu: 1 account của mình cho mọi KH (mỗi KH 1 GAS project + 1 spreadsheet) | OTP chỉ gửi lúc login (token 30 ngày) → ~1-2 mail/editor/tháng, quota 100/ngày đủ cho ~50 KH. Nút thắt thật: **Drive 15GB chứa ảnh mọi KH** → Google One 100GB (~50k/th) hoặc Workspace ($7/th, 1.500 mail/ngày + mail domain riêng). Đây là chi phí hạ tầng duy nhất. |
| GitHub Pages / Vercel Hobby | ❌ Loại cho kinh doanh | Pages cấm hosting thương mại + giới hạn 1GB; Vercel Hobby phi thương mại. Vercel Pro ($20/th) là phương án trả phí thay CF nếu muốn DX. |

### Hai việc bắt buộc khi mọi trứng trong giỏ của mình

1. **Chống single point of failure**: 1 account bị khoá = mọi KH sập. Bắt buộc 2FA mọi account + **backup tự động** (mirror toàn bộ repo git + export spreadsheet định kỳ về nơi thứ hai). Có backup thì kịch bản xấu nhất = vài giờ dựng lại trên account mới.
2. **Chuẩn hoá khuôn onboarding KH mới** (~1-2h/KH): template repo (data/ + templates/ + scripts/ + workflow) → tạo org → clone → đổi design template → clasp push GAS mới → điền Script Properties (GITHUB_TOKEN/REPO/BRANCH) → tạo CF Pages project → trỏ domain KH. Script hoá được phần lớn.

### Kinh tế

Chi phí biến đổi ≈ 0đ/KH; cố định ~50-150k/tháng (Google One/Workspace dùng chung). Phí vận hành/năm thu của KH ≈ biên ròng — giá trị bán là CMS + cập nhật + monitoring + backup + support, không phải giá hạ tầng.

### Việc treo khi bắt đầu KH đầu tiên

- [ ] Migrate mvngroup sang Cloudflare Pages làm bản khuôn (wrangler trong workflow + `_redirects`)
- [ ] Script mirror backup repos + spreadsheets
- [ ] Checklist/script onboarding KH mới
