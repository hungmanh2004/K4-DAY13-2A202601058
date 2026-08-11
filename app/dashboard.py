from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path("data/logs.jsonl")
WINDOW_MINUTES = 60


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _number(record: dict[str, Any], field: str) -> float | None:
    value = record.get(field)
    return float(value) if isinstance(value, (int, float)) else None


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _series(records: list[dict[str, Any]], event: str, field: str) -> list[dict[str, Any]]:
    buckets: dict[str, float] = defaultdict(float)
    for record in records:
        if record.get("event") != event:
            continue
        timestamp = _parse_timestamp(record.get("ts"))
        value = _number(record, field)
        if timestamp is not None and value is not None:
            buckets[timestamp.replace(second=0, microsecond=0).isoformat()] += value
    return [{"time": key, "value": round(value, 6)} for key, value in sorted(buckets.items())]


def _count_series(records: list[dict[str, Any]], event: str) -> list[dict[str, Any]]:
    buckets: dict[str, int] = defaultdict(int)
    for record in records:
        if record.get("event") != event:
            continue
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None:
            buckets[timestamp.replace(second=0, microsecond=0).isoformat()] += 1
    return [{"time": key, "value": value} for key, value in sorted(buckets.items())]


def dashboard_data(log_path: Path = LOG_PATH) -> dict[str, Any]:
    """Build the six dashboard panels from the shared JSONL data source."""
    records: list[dict[str, Any]] = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                timestamp = _parse_timestamp(record.get("ts"))
                if timestamp and timestamp >= datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES):
                    records.append(record)

    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [value for record in responses if (value := _number(record, "latency_ms")) is not None]
    costs = [value for record in responses if (value := _number(record, "cost_usd")) is not None]
    tokens_in = sum(value for record in responses if (value := _number(record, "tokens_in")) is not None)
    tokens_out = sum(value for record in responses if (value := _number(record, "tokens_out")) is not None)
    quality = [value for record in responses if (value := _number(record, "quality_score")) is not None]
    total_cost = sum(costs)
    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    error_breakdown = Counter(str(record.get("error_type", "unknown")) for record in failures)

    return {
        "window_minutes": WINDOW_MINUTES,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": len(records),
        "latency": {"p50": _percentile(latencies, 50), "p95": _percentile(latencies, 95), "p99": _percentile(latencies, 99), "threshold": 3000},
        "traffic": {"count": len(requests), "rate_per_minute": len(requests) / WINDOW_MINUTES, "threshold": 1, "series": _count_series(records, "request_received")},
        "errors": {"count": len(failures), "rate_pct": error_rate, "threshold": 2, "breakdown": dict(error_breakdown)},
        "cost": {"total_usd": total_cost, "threshold": 2.5, "series": _series(records, "response_sent", "cost_usd")},
        "tokens": {"input": tokens_in, "output": tokens_out, "total": tokens_in + tokens_out, "threshold": 50000},
        "quality": {"mean": (sum(quality) / len(quality)) if quality else None, "threshold": 0.75},
    }


DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 13 AI Observability</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#f6f8fb;color:#172033}.top{padding:24px 5%;background:#11253f;color:white}.top p{margin:6px 0 0;color:#cbd5e1}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px;padding:24px 5%}.panel{background:#fff;border:1px solid #dce3ed;border-radius:12px;padding:18px;box-shadow:0 2px 5px #1720330d}.metric{font-size:28px;font-weight:700;margin:10px 0}.threshold{font-size:13px;color:#526176}.ok{color:#087443}.bad{color:#b42318}.empty{color:#697586}table{width:100%;border-collapse:collapse;font-size:14px}td{padding:6px 0;border-bottom:1px solid #edf1f5}td:last-child{text-align:right;font-weight:600}.chart{width:100%;height:90px;margin-top:10px}footer{padding:0 5% 24px;color:#526176;font-size:13px}
</style></head><body>
<section class="top"><h1>Day 13 AI Observability</h1><p id="subtitle">Loading data…</p></section>
<main class="grid" id="panels"></main><footer>Source: <code>data/logs.jsonl</code> · Refresh: 30 seconds · Thresholds from <code>config/dashboard.yaml</code></footer>
<script>
const n=(v,d=2)=>v===null||v===undefined?'No data':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const status=(ok)=>`<span class="${ok?'ok':'bad'}">${ok?'Within threshold':'Threshold breached'}</span>`;
const card=(title,body)=>`<section class="panel"><h2>${title}</h2>${body}</section>`;
function sparkline(series){if(!series.length)return '<p class="empty">No time-series data yet.</p>';const v=series.map(x=>x.value),max=Math.max(...v),min=Math.min(...v),range=max-min||1;const pts=v.map((x,i)=>`${i/(v.length-1||1)*300},${80-(x-min)/range*70}`).join(' ');return `<svg class="chart" viewBox="0 0 300 90" role="img" aria-label="Metric over time"><line x1="0" y1="80" x2="300" y2="80" stroke="#cbd5e1"/><polyline points="${pts}" fill="none" stroke="#1769aa" stroke-width="3"/></svg>`}
function render(d){
 document.querySelector('#subtitle').textContent=`Last ${d.window_minutes} minutes · ${d.records} valid log records · Updated ${new Date(d.generated_at).toLocaleTimeString()}`;
 const l=d.latency, t=d.traffic, e=d.errors, c=d.cost, k=d.tokens, q=d.quality;
 const latency=l.p95==null?'<p class="empty">No response_sent latency data yet.</p>':`<table><tr><td>P50</td><td>${n(l.p50,0)} ms</td></tr><tr><td>P95</td><td>${n(l.p95,0)} ms</td></tr><tr><td>P99</td><td>${n(l.p99,0)} ms</td></tr></table><p class="threshold">P95 SLO ≤ ${l.threshold} ms · ${status(l.p95<=l.threshold)}</p>`;
 const traffic=`<div class="metric">${n(t.count,0)}</div><p>requests in the active window</p>${sparkline(t.series)}<p class="threshold">Average ${n(t.rate_per_minute)} requests/min · target ≥ ${t.threshold}/min · ${status(t.rate_per_minute>=t.threshold)}</p>`;
 const errors=`<div class="metric">${n(e.rate_pct)}%</div><p>${n(e.count,0)} failed / ${n(t.count,0)} received</p><p class="threshold">Error-rate SLO ≤ ${e.threshold}% · ${status(e.rate_pct<=e.threshold)}</p><table>${Object.entries(e.breakdown).map(([k,v])=>`<tr><td>${k}</td><td>${v}</td></tr>`).join('')||'<tr><td>No errors</td><td>0</td></tr>'}</table>`;
 const cost=`<div class="metric">$${n(c.total_usd,6)}</div><p>total cost in the active window</p>${sparkline(c.series)}<p class="threshold">Cost limit ≤ $${c.threshold} · ${status(c.total_usd<=c.threshold)}</p>`;
 const tokens=`<table><tr><td>Input tokens</td><td>${n(k.input,0)}</td></tr><tr><td>Output tokens</td><td>${n(k.output,0)}</td></tr><tr><td>Total</td><td>${n(k.total,0)}</td></tr></table><p class="threshold">Token limit ≤ ${n(k.threshold,0)} · ${status(k.total<=k.threshold)}</p>`;
 const quality=q.mean==null?'<p class="empty">No quality data yet.</p>':`<div class="metric">${n(q.mean)}</div><p>mean quality score (0–1)</p><p class="threshold">Quality SLO ≥ ${q.threshold} · ${status(q.mean>=q.threshold)}</p>`;
 document.querySelector('#panels').innerHTML=card('Latency percentiles',latency)+card('Request traffic',traffic)+card('Error rate and breakdown',errors)+card('Cost over time',cost)+card('Input and output tokens',tokens)+card('Quality proxy',quality);
}
async function load(){try{render(await (await fetch('/api/dashboard-data')).json())}catch(err){document.querySelector('#subtitle').textContent='Unable to load dashboard data: '+err}}
load();setInterval(load,30000);
</script></body></html>"""
