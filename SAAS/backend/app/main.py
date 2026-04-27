from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.recommend import recommend_from_text
from app.resume_extract import extract_text, guess_kind


app = FastAPI(title="Seu Jairo - SAAS B2C (MVP local)")

security = HTTPBasic()

# Usuário e senha fixos para MVP
VALID_USERNAME = "admin"
VALID_PASSWORD = "senha123"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == VALID_USERNAME
    correct_password = credentials.password == VALID_PASSWORD
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return credentials.username

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.get("/api")
def api_root(user: str = Depends(authenticate)):
    return {"ok": True, "name": app.title, "user": user}


@app.get("/health")
def health(user: str = Depends(authenticate)):
    return {"ok": True, "user": user}


@app.post("/resume/extract")
async def resume_extract(file: UploadFile = File(...), user: str = Depends(authenticate)):
    kind = guess_kind(file.filename, file.content_type)
    data = await file.read()
    extracted = extract_text(kind, data)

    if not extracted.text:
        raise HTTPException(
            status_code=422,
            detail="Não consegui extrair texto do arquivo. Tente um PDF com texto (não escaneado) ou DOCX/TXT.",
        )

    return {
        "kind": extracted.kind,
        "chars": len(extracted.text),
        "preview": extracted.text[:600],
    }


@app.post("/recommendations")
async def recommendations(file: UploadFile = File(...), limit: int = 8, user: str = Depends(authenticate)):
    kind = guess_kind(file.filename, file.content_type)
    data = await file.read()
    extracted = extract_text(kind, data)

    recs = recommend_from_text(extracted.text, limit=limit)
    return {
        "kind": extracted.kind,
        "chars": len(extracted.text),
        "recommendations": [
            {"title": r.title, "reason": r.reason, "confidence": r.confidence} for r in recs
        ],
    }

