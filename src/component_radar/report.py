from __future__ import annotations

import json
from pathlib import Path

from .config import EVENTS_JSON, LATEST_JSON, PUBLIC_DIR, SUMMARY_JSON


def generate_report(
    latest_path: Path = LATEST_JSON,
    output_path: Path | None = None,
    events_path: Path = EVENTS_JSON,
    summary_path: Path = SUMMARY_JSON,
) -> Path:
    output_path = output_path or (PUBLIC_DIR / "index.html")
    data = json.loads(latest_path.read_text(encoding="utf-8")) if latest_path.exists() else []
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    _ = json.loads(events_path.read_text(encoding="utf-8")) if events_path.exists() else []
    events = sorted({x.get("event", "") for x in data if x.get("event")})
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Radar</title></head><body>
<h1>Radar de Componentes BR</h1>
<div>Total: {summary.get('items_total', len(data))} | Novos: {summary.get('items_new',0)} | Voltaram: {summary.get('items_returned',0)} | Sumiram: {summary.get('items_missing',0)} | Quedas: {summary.get('items_price_drop',0)} | Quedas relevantes: {summary.get('items_price_drop_significant',0)} | Lojas com falha: {summary.get('stores_failed',0)}</div>
<label>evento <select id='event'><option value=''>todos</option>{''.join(f'<option>{e}</option>' for e in events)}</select></label>
<label><input type='checkbox' id='onlyNew'> somente novidades</label>
<table border='1'><thead><tr><th>evento</th><th>termo</th><th>loja</th><th>título</th><th>preço anterior</th><th>preço atual</th><th>variação</th><th>1a vez</th><th>última vez</th><th>vezes</th><th>link</th></tr></thead><tbody id='tb'></tbody></table>
<script>const DATA={json.dumps(data,ensure_ascii=False).replace('</','<\\/')};
function esc(v){{const s=String(v ?? ''); return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;');}}
function render(){{
 const e=document.getElementById('event').value;
 const only=document.getElementById('onlyNew').checked;
 const rows=DATA.filter(r=>(!e||r.event===e)&&(!only||r.is_new));
 document.getElementById('tb').innerHTML=rows.map(r=>{{
  const link=(r.link||'').trim();
  const isSafe=/^(https?:\/\/|\/)/i.test(link);
  const linkCell=(link&&isSafe)?`<a href='${{esc(link)}}' target='_blank' rel='noopener'>abrir</a>`:(link?esc(link):'');
  return `<tr><td>${{esc(r.event)}}</td><td>${{esc(r.term)}}</td><td>${{esc(r.store)}}</td><td>${{esc(r.title)}}</td><td>${{esc(r.previous_price_value)}}</td><td>${{esc(r.last_price_value ?? r.price)}}</td><td>${{esc(r.price_delta_percent)}}%</td><td>${{esc(r.first_seen)}}</td><td>${{esc(r.last_seen)}}</td><td>${{esc(r.times_seen)}}</td><td>${{linkCell}}</td></tr>`;
 }}).join('');
}}
['event','onlyNew'].forEach(id=>document.getElementById(id).addEventListener('input',render));render();</script></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
