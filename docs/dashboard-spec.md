# Dashboard specification

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn
dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

## Công cụ và nguồn dữ liệu

Dashboard runtime được tích hợp trong FastAPI và truy cập tại:

```text
http://127.0.0.1:8000/dashboard
```

Dashboard đọc trực tiếp từ `data/logs.jsonl`. Langfuse được dùng cho tracing và
prompt versioning, không phải nguồn chính của sáu panel dashboard. Contract
dashboard được định nghĩa trong `config/dashboard.yaml`.

## Thời gian và tiêu chuẩn trình bày

- Khoảng thời gian mặc định: 60 phút.
- Tự refresh: 30 giây.
- Mỗi panel phải hiển thị tên, đơn vị và trạng thái threshold/SLO.
- Dashboard chính gồm đúng sáu nhóm chỉ số bên dưới.
- Screenshot phải nhìn rõ tên panel, khoảng thời gian, đơn vị và threshold/SLO.

## Sáu panel bắt buộc

| Tên panel | Nguồn dữ liệu | Đơn vị | Phép tổng hợp | Threshold/SLO |
|---|---|---|---|---|
| Latency percentiles | `response_sent.latency_ms` | ms | P50, P95, P99 | P95 ≤ 3000 ms |
| Request traffic | `request_received` | requests/minute | count, rate per minute | rate ≥ 1 request/minute |
| Error rate and breakdown | `request_received`, `request_failed`, `error_type` | percent | error rate, breakdown theo loại lỗi | error rate ≤ 2% |
| Cost over time | `response_sent.cost_usd` | USD | tổng theo phút, tổng toàn cửa sổ | tổng cost ≤ 2.5 USD |
| Input and output tokens | `response_sent.tokens_in`, `response_sent.tokens_out` | tokens | tổng input và output | tổng ≤ 50.000 tokens |
| Quality proxy | `response_sent.quality_score` | score 0–1 | mean | mean ≥ 0.75 |

Các threshold/SLO trên phải giữ thống nhất với `config/dashboard.yaml` và
`config/slo.yaml`; không thay đổi contract chỉ để làm screenshot đẹp hơn.

## Kiểm tra contract

Chạy validator trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

Kết quả hợp lệ cần có:

```text
HỢP LỆ: 6/6 panel có trong dashboard contract.
```
