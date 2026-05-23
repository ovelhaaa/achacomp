from __future__ import annotations

import json
from pathlib import Path

from .config import LATEST_JSON, PUBLIC_DIR


def generate_report(latest_path: Path = LATEST_JSON, output_path: Path | None = None) -> Path:
    output_path = output_path or (PUBLIC_DIR / "index.html")
    if latest_path.exists():
        data = json.loads(latest_path.read_text(encoding="utf-8"))
    else:
        data = []
    last_update = data[0]["scan_datetime"] if data else "N/A"
    total = len(data)
    novidades = sum(1 for x in data if x.get("is_new"))
    categories = sorted({x.get("category", "") for x in data if x.get("category")})
    priorities = sorted({x.get("priority", "") for x in data if x.get("priority")})

    html = f"""<!doctype html>
<html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Radar de Componentes BR</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;padding:1rem;background:#f7f7f7}}
.card{{background:white;padding:1rem;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
.controls{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.7rem;margin:1rem 0}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{border:1px solid #ddd;padding:.4rem;vertical-align:top}}th{{background:#eee}}
.new{{font-weight:bold;color:#0a7}}a{{color:#06c}}
</style></head>
<body><div class='card'><h1>Radar de Componentes BR</h1>
<p>Última atualização: <b id='last'>{last_update}</b></p>
<p>Total de achados: <b id='total'>{total}</b> | Novidades: <b id='new'>{novidades}</b></p>
<div class='controls'>
<input id='search' placeholder='Buscar texto...'>
<select id='category'><option value=''>Todas categorias</option>{''.join(f"<option>{c}</option>" for c in categories)}</select>
<select id='priority'><option value=''>Todas prioridades</option>{''.join(f"<option>{p}</option>" for p in priorities)}</select>
<label><input type='checkbox' id='onlyNew'> somente novidades</label></div>
<div style='overflow-x:auto'><table><thead><tr><th>novidade</th><th>termo</th><th>categoria</th><th>loja</th><th>título</th><th>preço</th><th>disponibilidade</th><th>prioridade</th><th>uso em áudio</th><th>link</th></tr></thead>
<tbody id='tb'></tbody></table></div></div>
<script>
const DATA = {json.dumps(data, ensure_ascii=False).replace("</", "<\\/")};
const tb = document.getElementById('tb');
function esc(v){{
 const s=String(v ?? '');
 return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;');
}}
function render(){{
 const q=(document.getElementById('search').value||'').toLowerCase();
 const cat=document.getElementById('category').value; const pri=document.getElementById('priority').value;
 const only=document.getElementById('onlyNew').checked;
 const rows=DATA.filter(r=>{{const txt=(JSON.stringify(r)||'').toLowerCase();
  return (!q||txt.includes(q))&&(!cat||r.category===cat)&&(!pri||r.priority===pri)&&(!only||r.is_new);}});
 tb.innerHTML=rows.map(r=>{{
  const link=(r.link||'').trim();
  const isSafe=/^(https?:\/\/|\/)/i.test(link);
  const linkCell=(link&&isSafe)?`<a href='${'{'}esc(link){'}'}' target='_blank' rel='noopener'>abrir</a>`:(link?esc(link):'');
  return `<tr><td class='${'{'}r.is_new?'new':''{'}'}'>${'{'}r.is_new?'novo':''{'}'}</td><td>${'{'}esc(r.term){'}'}</td><td>${'{'}esc(r.category){'}'}</td><td>${'{'}esc(r.store){'}'}</td><td>${'{'}esc(r.title){'}'}</td><td>${'{'}esc(r.price){'}'}</td><td>${'{'}esc(r.availability){'}'}</td><td>${'{'}esc(r.priority){'}'}</td><td>${'{'}esc(r.audio_use){'}'}</td><td>${'{'}linkCell{'}'}</td></tr>`;
 }}).join('');
}}
['search','category','priority','onlyNew'].forEach(id=>document.getElementById(id).addEventListener('input',render));
render();
</script></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
