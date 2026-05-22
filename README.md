# component-radar-br

Radar para varrer lojas brasileiras de eletrônica em busca de componentes úteis para áudio DIY, pedais, synths e eletrônica vintage.

## Instalação local

- Python 3.12
- `pip install -r requirements.txt`

## Uso

- Scan: `python -m component_radar.cli scan`
- Report: `python -m component_radar.cli report`
- Tudo: `python -m component_radar.cli all`

Arquivos gerados:
- `data/latest.csv`
- `data/latest.json`
- `data/seen.json`
- `public/index.html`

## Editar alvos

Edite `targets.yaml` por categoria e componentes. O arquivo também define `audio_use` por categoria.

## Editar lojas

Edite `stores.yaml` com `name`, `base_url` (com `{query}`) e `extractor`.

## GitHub Pages

1. Ative Pages em **Settings → Pages**.
2. Em **Build and deployment**, selecione **GitHub Actions**.
3. Rode o workflow manualmente em **Actions → scan-and-publish → Run workflow**.

## GitHub Actions

Workflow: `.github/workflows/scan-and-publish.yml`
- roda diariamente (cron UTC) e manualmente.
- executa testes, scan e report.
- commita mudanças em `data/` e `public/`.
- publica `public/` via actions oficiais de Pages.

## Segurança e boas práticas

- Respeite `robots.txt` e termos de uso das lojas.
- Não faça scraping agressivo.
- O scanner usa timeout, retry curto e intervalo entre requests.
- Frequência recomendada: 1 vez ao dia.

## Limitações

- HTML das lojas pode mudar.
- Algumas lojas bloqueiam scraping.
- Conteúdo renderizado por JavaScript pode não aparecer no `requests`.
- Extração de preço/disponibilidade ainda é genérica.

## Próximos passos

- Extratores específicos por loja para preço/estoque melhores.
- Alertas Telegram/Email para novidades de alta prioridade.
- Classificação com IA assistiva.
- Suporte opcional a Playwright para páginas JS.
