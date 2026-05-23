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
- Não contorne CAPTCHA/login.

## GitHub Actions

Workflow: `.github/workflows/scan-and-publish.yml`
- roda diariamente (cron UTC) e manualmente.
- executa testes, scan e report.
- commita mudanças em `data/` e `public/`.
- publica `public/` via actions oficiais de Pages.
