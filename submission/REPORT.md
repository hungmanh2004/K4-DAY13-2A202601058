# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID: day13-k4-observability-v1
- Triệu chứng từ metrics: Latency p95 tăng vọt bất thường lên ~3620ms (vượt quá nhiều so với mức baseline thông thường khoảng 1200ms). Error rate vẫn ở mức 0%.
- Trace ID liên quan: req-fc799b83 (không có trace ID của Langfuse, sử dụng correlation_id thay thế)
- Log line/correlation ID liên quan: req-fc799b83 (Log ghi nhận request_received lúc 10:13:44.781Z và response_sent lúc 10:13:48.937Z với latency_ms=3620)
- Root cause: Component `retrieve` (RAG) xử lý quá chậm. Trong mô phỏng, logic gọi DB hoặc Vector Store bị treo hoặc gặp vấn đề hiệu suất (ở đây là đoạn code `time.sleep(2.5)` do incident `rag_slow` kích hoạt), dẫn tới span cha (run) bị kéo dài.
- Fix action: Khắc phục hiệu năng của dịch vụ RAG/Vector Store. Xóa đoạn xử lý block (sleep) hoặc mở rộng (scale) tài nguyên cho vector store để xử lý truy vấn nhanh hơn. 
- Preventive measure: Cấu hình tham số timeout giới hạn cho tác vụ RAG retrieval (ví dụ `timeout=1.0s`). Triển khai cơ chế Fallback (nếu query vector store bị timeout thì tự động bypass trả về kết quả rỗng hoặc cache). Cấu hình cảnh báo alert khi Latency (p95) của hệ thống > 2000ms để phát hiện sớm.
## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Hồ Trọng Hảo | CP3: Điều tra sự cố (Challenge Incident) | N/A | Cách kết hợp Metrics, Traces và Logs để điều tra gốc rễ sự cố (rag_slow/latency spike). |
