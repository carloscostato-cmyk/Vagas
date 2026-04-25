## Seu Jairo (SAAS B2C) — Orientação de carreira por currículo

MVP local (sem publicar no GitHub) para candidato:

- Formulário: nome completo, LinkedIn, upload de currículo
- Análise do currículo e recomendações de profissões/áreas correlatas
- Canal de chat (futuro): Telegram / WhatsApp

### Rodar localmente (backend)

Pré-requisito: Python 3.10+.

```bash
cd SAAS/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra: `http://127.0.0.1:8000/health`

### Testes (backend)

```bash
cd SAAS/backend
pytest -q
```

