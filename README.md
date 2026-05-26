# component-radar-br

Radar para varrer lojas brasileiras de eletrônica em busca de componentes úteis para áudio DIY, pedais, synths e eletrônica vintage.

## Instalação local

- Python 3.12
- `pip install -r requirements.txt`

## Uso

- Scan: `PYTHONPATH=src python -m component_radar.cli scan`
- Report: `PYTHONPATH=src python -m component_radar.cli report`
- Tudo: `PYTHONPATH=src python -m component_radar.cli all`
- Inspecionar loja: `PYTHONPATH=src python -m component_radar.cli inspect-store --store eletronica_castro --term LM308`

Arquivos gerados:
- `data/latest.csv`
- `data/latest.json`
- `data/seen.json`
- `public/index.html`

## Lojas e extratores

`stores.yaml` suporta metadados por loja (`id`, `name`, `base_url`, `search_url`, `extractor`, `enabled`, `scope`, `notes`).

- Use `extractor: generic` quando ainda não houver extrator específico.
- Lojas `enabled: false` não entram no scan padrão.
- Escopos `international` e `unknown` ficam fora da busca principal por padrão.
- O radar prioriza compra prática no Brasil (nacional/regional/marketplace BR).

### Adicionar loja nova

1. Adicione no `stores.yaml` com `enabled: false` se a busca não estiver validada.
2. Rode `inspect-store` para baixar HTML e ver candidatos de seletor.
3. Se necessário, implemente extrator específico em `src/component_radar/extractors/`.
4. Sempre mantenha fallback para `generic`.

### Lojas com JavaScript

Se depender fortemente de JS, mantenha `enabled: false` e documente `unsupported_js: true` (quando aplicável). Não forçar bypass.

### Scraping educado

- Respeite `robots.txt` e termos de uso.
- Não faça scraping agressivo.
- Evite contornar CAPTCHA/login.

## GitHub Actions

Workflow: `.github/workflows/scan-and-publish.yml`
- roda diariamente (cron UTC) e manualmente.
- executa testes, scan e report.
- commita mudanças em `data/` e `public/`.
- publica `public/` via actions oficiais de Pages.

## Histórico e eventos

O radar agora mantém histórico avançado em `data/seen.json`, detectando eventos `new`, `returned`, `missing`, `price_drop`, `price_increase` e `availability_changed`.

- Itens `missing` só são marcados quando a loja foi varrida com sucesso na execução atual.
- Queda/subida de preço só é considerada quando o parser de preço brasileiro consegue extrair valor confiável.
- Arquivos gerados: `data/summary.json`, `data/events.json` e `data/events.csv`.
- O relatório HTML (`public/index.html`) inclui cards de resumo e filtro por evento.

## Requisições HTTP e bloqueios

O radar usa headers de navegador por padrão para evitar bloqueios triviais de `python-requests` e manter compatibilidade com lojas que ignoram User-Agent genérico.

- Isso **não** deve ser usado para burlar CAPTCHA, login, Cloudflare ou bloqueios explícitos.
- O User-Agent pode ser ajustado com `COMPONENT_RADAR_USER_AGENT`.
- `stores.yaml` pode definir `referer` ou `request.headers` por loja (ex.: `Referer`).
- Quando uma resposta `200` não gera resultados, o HTML é salvo em `data/debug/no_results/` para diagnóstico de extrator.

