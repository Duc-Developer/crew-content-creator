---
cover:
  image: "https://media2.dev.to/dynamic/image/width=1200,height=627,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fk5cbsgwwbcgzymtwix7q.png"
  alt: "Bài viết về cách làm migration Supabase RLS idempotent để tránh lỗi policy đã tồn tại khi chạy lại"
  caption: "Khi migrations phải chạy đi chạy lại ở CI, staging hoặc lúc onboard dev mới, RLS policy rất dễ trở thành điểm gây lỗi nếu không được thiết kế idempotent."
---

# Cách chúng tôi làm migration Supabase RLS chạy lại an toàn (idempotent) — và vì sao bạn cũng nên làm

Nếu bạn dùng Supabase (Postgres) và triển khai Row Level Security (RLS) nghiêm túc, sớm hay muộn sẽ gặp một kịch bản “trớ trêu”: **migration chạy ngon ở local**, lên **staging cũng ổn**, nhưng đến lúc cần **chạy lại toàn bộ migrations** (CI dựng database mới, kiểm thử reset/rollback, hoặc đồng đội clone repo và setup từ đầu) thì… gãy.

Và điều gây gãy thường không nằm ở schema phức tạp, mà nằm ở thứ tưởng đơn giản: **RLS policy**.

## Vấn đề: chạy lần đầu ổn, chạy lại thì lỗi “policy … for table …”

Trong bài gốc, tác giả đưa ra dấu hiệu lỗi rất điển hình. Khi hệ thống cần re-apply migrations, Postgres trả về lỗi liên quan policy trên một bảng, kiểu như:

    ERROR: policy "Users can view own stitched exports" for table "stitched_exports ...

Thông báo trong digest bị cắt, nhưng phần quan trọng nằm ở cấu trúc lỗi: **`policy "..." for table "..."`**. Đây thường là dấu hiệu migration đang cố tạo lại một policy trùng tên (hoặc xung đột) trên cùng bảng — thứ không sao khi chạy lần đầu trên database “sạch”, nhưng sẽ lộ ra ngay khi bạn chạy lại trên database đã có trạng thái trước đó.

## Vì sao lỗi này hay xảy ra với Supabase RLS migrations?

### RLS policy là “đối tượng cấu hình” gắn vào bảng — và rất dễ trùng khi re-run

RLS trong Postgres hoạt động thông qua các **policy** gắn với từng bảng. Khi migration tạo policy mới, nếu bạn chạy lại migration đó trên môi trường mà policy đã tồn tại, việc tạo lại có thể dẫn tới lỗi.

Vấn đề là nhiều team chỉ kiểm tra “migrations chạy được” trên một database mới tinh. Trong khi workflow thực tế lại liên tục tạo ra các kịch bản “không sạch 100%”, như:

- CI spin up môi trường mới rồi apply migrations (đôi khi có cache/snapshot),
- Staging reset/rollback để test,
- Preview environment tạo/huỷ liên tục,
- Dev mới clone repo, reset DB và apply lại từ đầu.

### “Idempotent” là yêu cầu của workflow, không phải “tính năng phụ”

**Idempotent** (trong bối cảnh migration) có thể hiểu theo cách thực dụng:

> Chạy cùng một migration nhiều lần vẫn đưa database về **trạng thái đúng như mong muốn**, thay vì fail vì “đã tồn tại”.

Với RLS policy, yêu cầu này càng quan trọng vì lỗi thường chỉ xuất hiện ở lần chạy thứ hai — đúng lúc bạn cần hệ thống ổn định nhất.

## Idempotent migration là gì (và nên hiểu đúng để tránh kỳ vọng sai)?

Migration idempotent không có nghĩa là “chạy lại thì không thay đổi gì”. Nó có nghĩa:

- Nếu đối tượng đã ở trạng thái mong muốn, migration **không gây lỗi**.
- Nếu chưa đúng, migration **đưa về đúng trạng thái**.

Đồng thời, cần đặt kỳ vọng đúng: idempotent giúp bạn tránh các lỗi kiểu “đã tồn tại” khi rerun, nhưng **không tự động giải quyết mọi dạng drift** (ví dụ policy đã tồn tại nhưng logic bên trong không còn khớp kỳ vọng hiện tại).

## Vì sao bạn cũng nên làm: CI/CD, staging và onboarding đều cần “chạy lại được”

Bài gốc nhấn mạnh “and why you should too” vì đây không phải lỗi hiếm gặp của một dự án, mà là đặc trưng của cách đội nhóm làm việc với Supabase/Postgres.

### 1) CI/CD cần apply migrations đáng tin cậy

Trong CI, test thường bắt đầu bằng dựng database và apply migrations. Nếu có bất kỳ bước nào không thể chạy lặp, bạn sẽ có pipeline “flaky”: lúc pass lúc fail tuỳ trạng thái môi trường.

### 2) Kiểm thử reset/rollback sẽ “vạch mặt” migration không idempotent

Nhiều team kiểm thử rollback theo kiểu reset trạng thái rồi apply lại. Migration không idempotent biến những lần test này thành vòng lặp debug dai dẳng — đặc biệt khi lỗi xuất phát từ một policy.

### 3) Onboarding dev mới: đừng để trải nghiệm bắt đầu dự án là… lỗi RLS

Việc đồng đội clone repo và chạy migrations từ đầu là chuyện thường xuyên. Nếu họ gặp ngay lỗi kiểu “policy … for table …”, chi phí onboarding tăng lên, và bạn mất thời gian hỗ trợ những lỗi lẽ ra tránh được.

## Nguyên tắc viết Supabase RLS migrations theo hướng idempotent (mức “best practice”, không gán kỹ thuật cụ thể)

Digest không cung cấp chi tiết tác giả dùng câu lệnh SQL nào. Vì vậy, phần này được trình bày như **nguyên tắc/khung tư duy** để áp dụng, không khẳng định bài gốc thực hiện theo đúng từng câu lệnh cụ thể.

### Nguyên tắc 1: Đừng chỉ test “apply một lần” — hãy test “rerun”

Một bài test đơn giản nhưng hiệu quả:

- Apply toàn bộ migrations lên database mới.
- Chạy lại lần nữa trên cùng database (hoặc chạy lại quy trình reset/rehydrate mà team bạn đang dùng).

Nếu lần 2 fail, migration đó chưa đạt tiêu chí “chạy lại an toàn”.

### Nguyên tắc 2: Xem policy như “trạng thái mong muốn”, không phải “sự kiện chạy một lần”

Với RLS, mục tiêu của migration nên là: đảm bảo policy **không gây xung đột khi chạy lại**, và sau khi chạy xong, database phản ánh đúng trạng thái bảo mật bạn đặt ra.

### Nguyên tắc 3: Thống nhất cách xử lý khi policy đã tồn tại

Trong thực tế có nhiều chiến lược để đạt idempotency, và mỗi cách có trade-off. Dù chọn cách nào, điều quan trọng là team phải thống nhất: khi chạy lại migrations mà policy đã tồn tại, hệ thống nên cư xử ra sao để không làm CI/staging/onboarding “toang”.

## Checklist nhanh trước khi merge một migration RLS

- [ ] Migration chạy lại không lỗi kiểu “policy … for table …”
- [ ] Bạn đã thử kịch bản CI (database mới) và kịch bản rerun (database đã apply)
- [ ] Migration mô tả rõ “trạng thái mong muốn” sau khi chạy
- [ ] Nếu policy thay đổi theo thời gian, có kế hoạch migration phiên bản tiếp theo để phản ánh thay đổi (không trông chờ “chạy lại sẽ tự cập nhật”)

## Kết: Với Supabase RLS, “idempotent” nên là tiêu chuẩn mặc định

Điểm rút ra từ câu chuyện trong bài gốc rất thẳng: **migration chạy được một lần là chưa đủ**. Đặc biệt với **Supabase RLS policy**, lỗi kiểu:

`ERROR: policy "..." for table "..." ...`

thường chỉ xuất hiện đúng lúc bạn cần sự ổn định nhất: CI, staging reset, hoặc khi dev mới bắt đầu làm việc.

Nếu bạn coi migrations là “nguồn chân lý” cho schema và bảo mật, thì **idempotent** không phải tối ưu phụ, mà là điều kiện để workflow đội nhóm vận hành trơn tru.

---

## Nguồn gốc bài viết

Bài viết được chuyển ngữ và biên tập theo bài gốc trên DEV Community:  
https://dev.to/nareshipme/how-we-made-our-supabase-rls-migrations-idempotent-and-why-you-should-too-4d2g