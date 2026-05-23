# AGENTS Instructions

- Manter código simples e testável.
- Não adicionar dependências pesadas sem necessidade.
- Não fazer scraping agressivo.
- Sempre rodar `pytest` antes de finalizar.
- Preservar compatibilidade com GitHub Actions.
- Manter `targets.yaml` e `stores.yaml` legíveis para usuário não técnico.
- Preferir funções pequenas.
- Não colocar segredos no repositório.
- Ao adicionar loja nova, preferir `enabled: false` se a URL de busca ou HTML não forem confiáveis.
- Não aumentar frequência de scraping.
- Não adicionar Playwright sem necessidade.
- Sempre criar fixture HTML para extratores específicos.
- Sempre manter fallback genérico.
- Não criar código para contornar CAPTCHA, login ou bloqueio explícito.
