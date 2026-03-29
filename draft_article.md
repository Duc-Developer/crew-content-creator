```yaml
---
cover:
  image: "https://media2.dev.to/dynamic/image/width=1200,height=627,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fk5cbsgwwbcgzymtwix7q.png"
  alt: "Bài viết về cách làm migration Supabase RLS idempotent để tránh lỗi policy đã tồn tại khi chạy lại"
  caption: "Khi migrations phải chạy đi chạy lại ở CI, staging hoặc lúc onboard dev mới, RLS policy rất dễ trở thành điểm gây lỗi nếu không được thiết kế idempotent."
---
```

# Cách chúng tôi làm migration Supabase RLS chạy lại an toàn (idempotent) — và vì sao bạn cũng nên làm

Nếu bạn dùng Supabase (Postgres) và triển khai Row Level Security (RLS) nghiêm túc, sớm hay muộn bạn sẽ gặp một kịch bản trớ trêu: **migration chạy “ngon” ở local**, đẩy lên **staging cũng ổn**, nhưng đến lúc cần **chạy lại toàn bộ migrations** (CI dựng database mới, kiểm thử reset/rollback, hoặc đồng đội clone repo và setup từ đầu) thì… gãy.

Và cái gãy thường không nằm ở schema phức tạp, mà nằm ở những thứ “tưởng đơn giản” như **RLS policy**.

---

## Vấn đề: chạy lần đầu ổn, chạy lại thì lỗi “policy … for table …”

Trong bài gốc, dấu hiệu lỗi được nêu rất rõ: khi hệ thống cần re-apply migrations, Postgres trả về lỗi liên quan đến policy đã tồn tại, kiểu như:

```text
ERROR: policy "Users can view own stitched exports" for table "stitched_exports ...
```

Dù thông báo trong digest bị cắt, phần quan trọng nằm ở cấu trúc lỗi: **`policy "..." for table "..."`**. Điều này thường ám chỉ tình huống migration đang cố tạo một policy trùng tên / xung đột trên cùng bảng — thứ vốn không sao khi chạy lần đầu trên database “sạch”, nhưng sẽ lộ ra ngay khi bạn chạy lại trên database đã có trạng thái trước đó.

---

## Vì sao lỗi này hay xảy ra với Supabase RLS migrations?

### RLS policy là “đối tượng cấu hình” gắn vào bảng — và rất dễ trùng khi re-run

RLS trong Postgres hoạt động thông qua các **policy** gắn với từng table. Khi migration tạo policy mới, nếu bạn chạy lại migration đó trên cùng môi trường mà policy đã tồn tại, việc tạo lại sẽ dẫn tới lỗi.

Điều khó chịu là: nhiều team chỉ kiểm tra “migrations chạy được” trên một database mới tinh. Nhưng thực tế dev workflow lại liên tục tạo ra các kịch bản “không sạch 100%”:

- CI spin up môi trường rồi apply lại từ đầu (đôi khi có cache/snapshot),
- Staging reset/rollback để test,
- Preview environment tạo/huỷ liên tục,
- Dev mới clone repo, chạy reset và apply lại.

### “Idempotent” là yêu cầu của workflow, không phải “tính năng phụ”

**Idempotent** (trong bối cảnh migrations) có thể hiểu theo cách thực dụng:

> Bạn có thể chạy cùng một migration nhiều lần, và database vẫn đi đến **trạng thái đúng như mong muốn**, thay vì fail vì “đã tồn tại”.

Với RLS policy, nhu cầu này càng rõ vì lỗi thường chỉ xuất hiện ở lần chạy thứ hai — đúng lúc bạn cần pipeline ổn định nhất.

---

## Idempotent migration là gì (và nên hiểu đúng để tránh kỳ vọng sai)?

Một migration idempotent không có nghĩa là “không thay đổi gì khi chạy lại”. Nó có nghĩa:

- Nếu đối tượng đã ở đúng trạng thái, migration **không gây lỗi**,
- Nếu chưa đúng trạng thái, migration **đưa về đúng trạng thái**.

Và cũng cần nói rõ: idempotent migrations giúp bạn tránh các lỗi “đã tồn tại” khi rerun, nhưng **không tự động giải quyết mọi dạng drift** (ví dụ: policy tồn tại nhưng logic bên trong đã khác kỳ vọng).

---

## Vì sao bạn cũng nên làm: CI/CD, staging và onboarding đều cần “chạy lại được”

Bài gốc nhấn mạnh “why you should too” vì đây không phải lỗi hiếm gặp của một dự án cụ thể, mà là đặc trưng của cách đội nhóm làm việc với Supabase/Postgres.

### 1) CI cần dựng database “fresh” và apply migrations đáng tin cậy

Trong CI, một bài test thường bắt đầu bằng việc dựng một database mới và apply migrations. Nếu có bất kỳ bước nào không thể chạy lặp, bạn sẽ nhận được pipeline “flaky”: lúc pass lúc fail tuỳ trạng thái môi trường.

### 2) Kiểm thử reset/rollback sẽ “vạch mặt” migration không idempotent

Nhiều team kiểm thử rollback theo kiểu reset trạng thái rồi apply lại. Nếu migrations không được viết để chạy lại an toàn, những lần test như vậy sẽ biến thành vòng lặp debug mệt mỏi — nhất là khi lỗi chỉ đến từ một policy.

### 3) Onboarding dev mới: đừng để trải nghiệm bắt đầu dự án là… một lỗi RLS

Việc đồng đội clone repo và chạy migrations từ đầu là tình huống diễn ra thường xuyên. Nếu họ gặp lỗi kiểu “policy … for table …” ngay từ bước đầu, chi phí onboarding tăng lên ngay lập tức, và bạn mất thời gian hỗ trợ những lỗi đáng lẽ có thể tránh.

---

## Nguyên tắc viết Supabase RLS migrations theo hướng idempotent (mức “best practice”, không phụ thuộc một mẹo duy nhất)

Digest không cung cấp chi tiết tác giả dùng câu lệnh SQL nào, nên phần dưới đây được trình bày như **nguyên tắc/khung tư duy** để bạn áp dụng, thay vì khẳng định “bài gốc làm đúng theo từng dòng như sau”.

### Nguyên tắc 1: Đừng chỉ test “apply một lần” — hãy test “rerun”

Một bài test đơn giản nhưng cực hiệu quả:

- Apply toàn bộ migrations lên database mới
- Apply lại lần nữa trên cùng database (hoặc chạy lại quy trình reset/rehydrate bạn dùng trong team)

Nếu lần 2 fail, migration đó chưa đạt tiêu chí idempotent.

### Nguyên tắc 2: Xem policy như một phần của “trạng thái mong muốn”, không phải “sự kiện chạy một lần”

Hãy viết migrations với mục tiêu:

- Đảm bảo policy **tồn tại đúng tên**, đúng bảng,
- Và tránh trường hợp “tạo lại” làm fail khi rerun.

### Nguyên tắc 3: Chọn chiến lược idempotent phù hợp với mức độ bạn chấp nhận

Trong thực tế thường có nhiều cách tiếp cận (mỗi cách có trade-off). Ví dụ:

- **Cách thiên về “đưa về trạng thái mong muốn”**: đảm bảo sau migration, policy đúng như bạn định nghĩa (thường đòi hỏi logic cập nhật/replace).
- **Cách thiên về “không phá môi trường khi rerun”**: nếu đã tồn tại thì không tạo lại, để tránh lỗi.

Điểm mấu chốt: bạn cần nhất quán trong dự án về cách xử lý “policy đã tồn tại” khi chạy lại migrations.

---

## Checklist nhanh trước khi merge một migration RLS

- [ ] Migration có thể chạy lại mà không lỗi “policy … for table …”
- [ ] Bạn đã thử kịch bản CI (database mới) và kịch bản rerun (database đã apply)
- [ ] Bạn có ghi chú rõ ràng: migration kỳ vọng trạng thái gì sau khi chạy
- [ ] Nếu policy thay đổi theo thời gian, bạn có kế hoạch migration phiên bản tiếp theo để phản ánh thay đổi (thay vì trông chờ “rerun là tự cập nhật”)

---

## Kết: Với Supabase RLS, “idempotent” nên là tiêu chuẩn mặc định

Điểm rút ra từ câu chuyện trong bài gốc rất thẳng: **migration chạy được một lần chưa đủ**. Đặc biệt với **Supabase RLS policy**, lỗi kiểu:

> `ERROR: policy "..." for table "..." ...`

thường chỉ xuất hiện khi bạn cần hệ thống ổn định nhất: CI, staging reset, hoặc khi dev mới bắt đầu làm việc.

Nếu bạn coi migrations là “nguồn chân lý” cho schema và bảo mật, thì **idempotent** không phải tối ưu phụ, mà là điều kiện để workflow đội nhóm vận hành trơn tru.

---

## Nguồn gốc bài viết

Bài viết được chuyển ngữ và biên tập theo bài gốc trên DEV Community:  
https://dev.to/nareshipme/how-we-made-our-supabase-rls-migrations-idempotent-and-why-you-should-too-4d2g