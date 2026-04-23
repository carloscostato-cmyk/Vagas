"""
Agente conversacional do Telegram para orquestrar os 3 times.

Comandos:
- /help: mostra comandos disponiveis
- /status: valida configuracao do bot
- /rh: executa apenas o Time 1 (RH Specialist)
- /submissions: executa Time 2 com as vagas novas da ultima busca
- /coach: executa Time 3 com base no ultimo relatorio
- /ciclo: executa operacao completa dos 3 times
- /start: mensagem de boas-vindas
"""

import os
import time
from datetime import datetime

import requests

from career_success_manager import CareerSuccessManager
from rh_specialist import run_agent
from submission_engine import SubmissionEngine
from telegram_notifier import TelegramNotifier


class TelegramCareerAgent:
    def __init__(self):
        self.notifier = TelegramNotifier()
        self.submission_engine = SubmissionEngine()
        self.manager = CareerSuccessManager(max_auto_apply=3)
        self.offset = None
        self.poll_timeout = 25
        self.last_rh_report = None
        self.last_submissions = []

    @property
    def bot_token(self) -> str:
        return self.notifier.bot_token or ""

    @property
    def chat_id(self) -> str:
        return str(self.notifier.chat_id or "")

    def _api_get(self, method: str, params: dict | None = None) -> dict:
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        response = requests.get(url, params=params or {}, timeout=40)
        response.raise_for_status()
        return response.json()

    def _send_text(self, text: str) -> bool:
        return self.notifier._send(text)

    def _send_help(self):
        self._send_text(
            "🤖 <b>Agente de Carreira - Comandos</b>\n\n"
            "/start - Inicia o agente\n"
            "/status - Verifica configuracao do bot\n"
            "/rh - Busca vagas Brasil (rapido, sem LinkedIn)\n"
            "/rhfull - Busca vagas Brasil completa (inclui LinkedIn)\n"
            "/submissions - Faz submissao automatica nas vagas novas\n"
            "/coach - Mostra insights do ciclo atual\n"
            "/ciclo - Executa ciclo Brasil completo (rapido, sem LinkedIn)\n"
            "/ciclofull - Executa ciclo Brasil completo (inclui LinkedIn)\n"
            "/help - Mostra esta ajuda"
        )

    def _same_chat(self, incoming_chat_id: str) -> bool:
        if not self.chat_id:
            return False
        return str(incoming_chat_id) == self.chat_id

    def _run_rh_team(self, include_linkedin: bool = False):
        started = datetime.now().strftime("%d/%m/%Y %H:%M")
        mode_label = "com LinkedIn" if include_linkedin else "modo rapido (sem LinkedIn)"
        self._send_text(f"🔎 <b>Busca em execucao</b>\n🕐 {started}\nIniciando coleta de vagas...")
        self._send_text(f"ℹ️ Rodando {mode_label}. Aguarde a confirmacao de conclusao.")
        report = run_agent(
            session_label="Telegram | RH Specialist",
            notify_telegram=False,
            include_linkedin=include_linkedin,
            location_scope="brazil",
        )
        self.last_rh_report = report
        jobs_to_show = report.get("new_jobs", []) or report.get("top_jobs", [])
        self.notifier.send_job_report(
            jobs=jobs_to_show,
            session_label="Busca RH",
            max_jobs=15,
        )

    def _run_submissions_team(self):
        if not self.last_rh_report:
            self._send_text("⚠️ Execute /rh antes de /submissions para gerar vagas do ciclo.")
            return

        new_jobs = self.last_rh_report.get("new_jobs", [])
        if not new_jobs:
            self.last_submissions = []
            self._send_text("📭 Sem vagas novas para submissao neste ciclo.")
            return

        self._send_text("📨 <b>Submissao em execucao</b>\nSubmetendo candidaturas automaticamente...")
        submitted = []
        for job in new_jobs[: self.manager.max_auto_apply]:
            result = self.submission_engine.execute_backend_submission(
                company=job.get("company", "Empresa"),
                role=job.get("title", "Cargo"),
                endpoint=job.get("url") or "https://careers.example.com",
            )
            submitted.append(result)

        self.last_submissions = submitted
        self._send_text(f"✅ <b>Submissao concluida</b>\nSubmissoes realizadas: {len(submitted)}")

    def _run_coach_team(self):
        if not self.last_rh_report:
            self._send_text("⚠️ Execute /rh antes de /coach para gerar contexto do ciclo.")
            return

        insights = self.manager._build_coach_insights(self.last_rh_report, len(self.last_submissions))
        if not insights:
            self._send_text("ℹ️ <b>Coach concluido</b>\nSem insights neste ciclo.")
            return

        lines = ["🧠 <b>Insights do coach</b>", "Resumo do ciclo:"]
        for insight in insights[:6]:
            lines.append(f"• {insight}")
        self._send_text("\n".join(lines))

    def _run_full_cycle(self, include_linkedin: bool = False):
        mode_label = "com LinkedIn" if include_linkedin else "modo rapido (sem LinkedIn)"
        self._send_text(f"🚀 <b>Executando ciclo completo</b>\n{mode_label}")
        report = self.manager.run_full_cycle(
            session_label="Telegram | Operacao 3 Times",
            notify_telegram=False,
            include_linkedin=include_linkedin,
            location_scope="brazil",
        )
        self.last_rh_report = report.get("rh", {})
        self.last_submissions = report.get("submitted", [])
        self.notifier.send_management_report(report, max_jobs=15)

    def _handle_text_command(self, text: str):
        command = text.strip().split()[0].lower()

        if command in ("/start", "start"):
            self._send_text(
                "👋 <b>Agente de Carreira online.</b>\n"
                "Pronto para operar com os 3 times.\nUse /help para ver os comandos."
            )
            return
        if command in ("/help", "help", "ajuda"):
            self._send_help()
            return
        if command in ("/status", "status"):
            ok, msg = self.notifier.validate_configuration()
            emoji = "✅" if ok else "❌"
            self._send_text(f"{emoji} <b>Status Telegram</b>\n{msg}")
            return
        if command in ("/rh", "rh"):
            self._run_rh_team(include_linkedin=False)
            return
        if command in ("/rhfull", "rhfull"):
            self._run_rh_team(include_linkedin=True)
            return
        if command in ("/submissions", "submissions"):
            self._run_submissions_team()
            return
        if command in ("/coach", "coach"):
            self._run_coach_team()
            return
        if command in ("/ciclo", "ciclo", "/run", "run"):
            self._run_full_cycle(include_linkedin=False)
            return
        if command in ("/ciclofull", "ciclofull"):
            self._run_full_cycle(include_linkedin=True)
            return

        self._send_text("Nao reconheci esse comando. Use /help para ver as opcoes.")

    def _process_update(self, update: dict):
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat", {})
        incoming_chat_id = str(chat.get("id", ""))
        text = str(message.get("text", "")).strip()

        if not text:
            return
        if self.chat_id and not self._same_chat(incoming_chat_id):
            return
        self._handle_text_command(text)

    def _fetch_updates(self) -> list:
        params = {
            "timeout": self.poll_timeout,
            "allowed_updates": ["message", "edited_message"],
        }
        if self.offset is not None:
            params["offset"] = self.offset
        data = self._api_get("getUpdates", params=params)
        if not data.get("ok", False):
            return []
        return data.get("result", [])

    def run_forever(self):
        ok, msg = self.notifier.validate_configuration()
        if not ok:
            print(f"ERRO: {msg}")
            return

        print("Telegram Career Agent iniciado. Aguardando comandos...")
        self._send_text("🤖 <b>Agente de Carreira conectado no Telegram.</b>\nUse /help para comandos.")

        while True:
            try:
                updates = self._fetch_updates()
                for upd in updates:
                    self.offset = int(upd["update_id"]) + 1
                    self._process_update(upd)
            except requests.exceptions.RequestException as err:
                print(f"WARN: falha de rede no polling Telegram: {err}")
                time.sleep(3)
            except Exception as err:
                print(f"WARN: erro no loop do agente Telegram: {err}")
                time.sleep(3)


if __name__ == "__main__":
    # Rodar localmente:
    # PowerShell: $env:TELEGRAM_BOT_TOKEN="..."; $env:TELEGRAM_CHAT_ID="..."; python telegram_agent.py
    agent = TelegramCareerAgent()
    agent.run_forever()
