# Alert và Runbook

Các alert dưới đây dựa trên SLI/SLO và triệu chứng mà người dùng có thể cảm nhận.
Không alert trực tiếp theo tên implementation nội bộ như `rag_slow` hoặc tên span.

## Alert 1

- **Tên:** User-visible latency is above SLO
- **Severity:** Warning
- **SLI/SLO liên quan:** `latency_p95_ms`, mục tiêu P95 ≤ 3000 ms, target 99.5%
- **Điều kiện và thời gian duy trì:** P95 latency > 3000 ms liên tục trong 10 phút.
- **Ảnh hưởng tới người dùng:** Người dùng phải chờ lâu, request có thể timeout hoặc trải nghiệm chat bị gián đoạn.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở panel Latency và xác nhận P95/P99 tăng trong cùng time range; so sánh với traffic để loại trừ việc chỉ có một request bất thường.
  2. Mở một trace chậm trong khoảng thời gian đó và xác định span chiếm phần lớn thời gian waterfall.
  3. Tìm log `response_sent` có cùng `correlation_id`, đối chiếu `latency_ms`, model, feature và session để xác nhận phạm vi ảnh hưởng.
- **Mitigation tạm thời:** Giảm concurrency của load/traffic thử nghiệm, tạm chuyển về prompt/flow ổn định gần nhất và tăng timeout chỉ khi cần giữ dịch vụ hoạt động.
- **Owner:** On-call Observability

## Alert 2

- **Tên:** Requests are failing above SLO
- **Severity:** Critical
- **SLI/SLO liên quan:** `error_rate_pct`, mục tiêu error rate ≤ 2%, target 99.0%
- **Điều kiện và thời gian duy trì:** Error rate > 2% liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng:** Người dùng nhận lỗi 5xx hoặc không nhận được câu trả lời; có thể mất khả năng sử dụng tính năng chat.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở panel Errors, kiểm tra error rate và breakdown theo `error_type`, đồng thời xác định thời điểm bắt đầu tăng.
  2. Mở một trace lỗi trong cùng khoảng thời gian để xem request fail ở span nào và lỗi có lặp lại theo feature/model hay không.
  3. Tìm log `request_failed` bằng `correlation_id`, đọc `error_type` và chi tiết đã được redact; đối chiếu với log `request_received` tương ứng.
- **Mitigation tạm thời:** Giảm hoặc dừng traffic không cần thiết, tắt feature/incident đang gây lỗi nếu đã xác định được, và chuyển traffic về cấu hình/model ổn định gần nhất.
- **Owner:** On-call API

## Alert 3

- **Tên:** Answer quality is below SLO
- **Severity:** Warning
- **SLI/SLO liên quan:** `quality_score_avg`, mục tiêu mean quality score ≥ 0.75, target 95%
- **Điều kiện và thời gian duy trì:** Mean quality score < 0.75 liên tục trong 15 phút với đủ traffic để kết luận.
- **Ảnh hưởng tới người dùng:** Câu trả lời có thể thiếu thông tin, không liên quan hoặc không đáp ứng câu hỏi dù request vẫn thành công.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở panel Quality và kiểm tra mean score, số lượng response và thời điểm score bắt đầu giảm; không kết luận từ một request đơn lẻ.
  2. Mở các trace có quality thấp, so sánh prompt label/version, retrieval result và generation output trong waterfall.
  3. Dùng `correlation_id` của trace để tìm log `response_sent`, kiểm tra `quality_score`, feature, model và `prompt_version`; xác định vấn đề có tập trung ở một phiên bản hay feature không.
- **Mitigation tạm thời:** Rollback prompt production về version đã biết ổn định, giảm phạm vi traffic vào feature bị ảnh hưởng và yêu cầu review các câu trả lời mẫu trước khi rollout lại.
- **Owner:** AI Quality
