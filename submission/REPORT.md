# Báo cáo Day 13 — Observability cho hệ thống AI

## 1. Thông tin nhóm

- Tên nhóm: K4
- Repository URL: [Bổ sung URL repository]
- Commit SHA cuối: `b3c5a8c269cc8834bed037c6728168c4e8ba2af1`
- Thành viên và vai trò:

| Thành viên                       | Vai trò                            |
| ---------------------------------- | ----------------------------------- |
| Trần Mạnh Hùng - 2A202601058    | Logging & PII                       |
| Lê Văn Tuệ - 2A202601048        | Tracing & Prompt Version            |
| Nguyễn Cảnh Hoàng - 2A202601588 | Dashboard, SLO & Alert              |
| Trương Đan Vi - 2A202601178     | Incident, Report & Demo             |
| Hồ Trọng Hảo - 2A202601358      | API Integration, Testing & Evidence |

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 theo kết quả kiểm tra baseline; log có schema hợp lệ, correlation ID, metadata và không còn PII thô. Evidence: [`log_val_score.png`](evidence/log_val_score.png).
- Tổng số traces: 10 traces trở lên; danh sách evidence tại [`trace_list.png`](evidence/trace_list.png).
- Số PII leak còn lại: 0 trong log đã kiểm tra; email, số điện thoại và thẻ được thay bằng placeholder `[REDACTED_*]`.
- Dashboard: [`dashboard.png`](evidence/dashboard.png)
- Kết quả dashboard validator: [`validate_dashboard.png`](evidence/validate_dashboard.png)

## 3. Logging và tracing

- Evidence correlation ID: [`log_cp1.png`](evidence/log_cp1.png). Mỗi request có `correlation_id`, `session_id`, `feature`, `model`, `env` và `user_id_hash`.
- Evidence PII redaction: [`log_cp1.png`](evidence/log_cp1.png). Nội dung nhạy cảm được che trước khi ghi log, ví dụ `[REDACTED_EMAIL]` và `[REDACTED_CREDIT_CARD]`.
- Evidence trace waterfall: [`trace_waterfall.png`](evidence/trace_waterfall.png)
- Span đáng chú ý: span RAG/retrieval chiếm phần lớn thời gian của trace incident. Đây là điểm cần khoanh vùng khi latency P95/P99 tăng; correlation ID được dùng để nối trace với các bản ghi `request_received` và `response_sent`.

## 4. Prompt versioning

- Prompt name: `day13-observability-assistant`
- Version/label baseline: `v1` / `production` — xem [`prompt_v1.png`](evidence/prompt_v1.png).
- Version/label candidate: `v2` / `candidate` — xem [`prompt_v2.png`](evidence/prompt_v2.png).
- Trace ID của mỗi version: Trace v1 và trace v2 được thể hiện trong các ảnh [`prompt_v1.png`](evidence/prompt_v1.png) và [`prompt_v2.png`](evidence/prompt_v2.png); khi nộp trên Langfuse, đối chiếu trace ID hiển thị trong hai ảnh này.
- Bằng chứng đổi label hoặc rollback: [`roll_back.png`](evidence/roll_back.png). Rollback về baseline giúp khôi phục prompt đã biết là ổn định.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: Hợp lệ `6/6 panel` — [`validate_dashboard.png`](evidence/validate_dashboard.png).
- Evidence dashboard: [`dashboard.png`](evidence/dashboard.png)
- SLO đã chọn:
  - Latency P95 ≤ 3000 ms, target 99.5%.
  - Error rate ≤ 2%, target 99.0%.
  - Daily cost ≤ 2.5 USD.
  - Quality score trung bình ≥ 0.75.
- Lý do: Các SLO bao phủ latency, độ ổn định, chi phí và chất lượng — bốn khía cạnh chính của API AI.
- Alert rules và runbook: [`config/alert_rules.yaml`](../config/alert_rules.yaml) và [`docs/alerts.md`](../docs/alerts.md). Có alert cho latency, error rate và quality suy giảm, kèm owner, ngưỡng, thời gian duy trì và hướng dẫn xử lý.

## 6. Điều tra challenge

Challenge ID: day13-k4-observability-v1

- Triệu chứng từ metrics: Latency p95 tăng vọt bất thường lên ~3620ms (vượt quá nhiều so với mức baseline thông thường khoảng 1200ms). Error rate vẫn ở mức 0%.
- Trace ID liên quan: req-fc799b83 (không có trace ID của Langfuse, sử dụng correlation_id thay thế)
- Log line/correlation ID liên quan: req-fc799b83 (Log ghi nhận request_received lúc 17:13:59.696 và response_sent lúc 17:13:45.316 với latency_ms=3620)
- Root cause: Component `retrieve` (RAG) xử lý quá chậm. Trong mô phỏng, logic gọi DB hoặc Vector Store bị treo hoặc gặp vấn đề hiệu suất (ở đây là đoạn code `time.sleep(2.5)` do incident `rag_slow` kích hoạt), dẫn tới span cha (run) bị kéo dài.
- Fix action: Khắc phục hiệu năng của dịch vụ RAG/Vector Store. Xóa đoạn xử lý block (sleep) hoặc mở rộng (scale) tài nguyên cho vector store để xử lý truy vấn nhanh hơn.
- Preventive measure: Cấu hình tham số timeout giới hạn cho tác vụ RAG retrieval (ví dụ `timeout=1.0s`). Triển khai cơ chế Fallback (nếu query vector store bị timeout thì tự động bypass trả về kết quả rỗng hoặc cache). Cấu hình cảnh báo alert khi Latency (p95) của hệ thống > 2000ms để phát hiện sớm.

## 7. Đóng góp cá nhân

| Thành viên                       | Phần việc                                         | Commit/PR         | Điều đã học                                                          |
| ---------------------------------- | --------------------------------------------------- | ----------------- | ------------------------------------------------------------------------- |
| Trần Mạnh Hùng - 2A202601058    | Logging, correlation ID, metadata và PII redaction | `aff4f19`       | Thiết kế log JSON, truy vết request và bảo vệ dữ liệu nhạy cảm. |
| Lê Văn Tuệ - 2A202601048        | Tracing và prompt versioning                       | Bổ sung sau      | Phân tích span, quản lý prompt v1/v2 và rollback.                    |
| Nguyễn Cảnh Hoàng - 2A202601588 | Dashboard, SLO, threshold, alert và runbook        | Bổ sung nếu có | Chuyển log thành metrics và thiết kế cảnh báo.                     |
| Trương Đan Vi - 2A202601178     | Điều tra challenge, root cause và demo           | Bổ sung nếu có | Điều tra theo luồng Metrics → Traces → Logs.                         |
| Hồ Trọng Hảo - 2A202601358      | Tổng hợp báo cáo và điều tra CP3             | `d35dee1`              | Kết hợp evidence để chứng minh root cause`rag_slow`.               |
