"""
Módulo de notificação via Telegram Bot.
Responsável por enviar relatórios e alertas de vagas ao Carlos Costato.
"""

import os
import requests
from datetime import datetime

# URL pública do dashboard ao vivo (GitHub Pages)
DASHBOARD_URL = "https://carloscostato-cmyk.github.io/Vagas/"
PORTFOLIO_URL = "https://carloscostato-cmyk.github.io/Costato/"


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id   = os.environ.get("TELEGRAM_CHAT_ID")
        self.api_url   = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def _send(self, message: str, parse_mode: str = "HTML") -> bool:
        """Envia uma mensagem via Telegram Bot API."""
        if not self.bot_token or not self.chat_id:
            print("ERRO: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID nao configurados.")
            print("   Acesse: GitHub repo -> Settings -> Secrets and variables -> Actions")
            return False

        payload = {
            "chat_id":    self.chat_id,
            "text":       message,
            "parse_mode": parse_mode,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            print("OK: Mensagem enviada ao Telegram com sucesso!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"FALHA: Erro ao enviar mensagem para o Telegram: {e}")
            return False

    def send_job_report(self, jobs: list, session_label: str = "Relatorio"):
        """Envia um relatorio formatado de vagas encontradas."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not jobs:
            message = (
                f"🤖 <b>Agente de Carreira | {session_label}</b>\n"
                f"🕐 {now} (Horario de Brasilia)\n\n"
                f"🔍 Varredura concluida.\n"
                f"📭 Nenhuma vaga nova encontrada neste ciclo.\n\n"
                f"📊 <a href=\"{DASHBOARD_URL}\">Ver Dashboard Completo</a>\n"
                f"<i>Proxima verificacao em breve...</i>"
            )
        else:
            lines = [
                f"🤖 <b>Agente de Carreira | {session_label}</b>",
                f"🕐 {now} (Horario de Brasilia)",
                "",
                f"🎯 <b>{len(jobs)} vaga(s) com match para o seu perfil:</b>",
                "",
            ]
            for i, job in enumerate(jobs[:8], 1):
                score       = job.get("match_score", 0)
                score_emoji = "🔥" if score > 60 else "⭐"
                source      = job.get("source", "Agente").capitalize()
                location    = job.get("location", "")
                url         = job.get("url", "")
                loc_str     = f"\n   📍 {location}" if location and location != "Nao informado" else ""
                url_str     = f"\n   🔗 <a href=\"{url}\">Ver Vaga Agora</a>" if url and url not in ("#", "") else ""
                lines.append(
                    f"{score_emoji} <b>{i}. {job.get('title', 'N/A')}</b>\n"
                    f"   🏢 {job.get('company', 'N/A')}\n"
                    f"   📡 {source} · 📊 Match: {score}%"
                    f"{loc_str}"
                    f"{url_str}\n"
                )
            lines += [
                "─────────────────────────",
                f"📊 <a href=\"{DASHBOARD_URL}\">Abrir Dashboard ao Vivo</a>",
                f"👤 <a href=\"{PORTFOLIO_URL}\">Ver Site Profissional</a>",
                "",
                "<i>Continue brilhando, Carlos! 🚀</i>",
            ]
            message = "\n".join(lines)

        self._send(message)

    def send_error_alert(self, error_msg: str):
        """Envia alerta de erro para o Telegram."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        message = (
            f"⚠️ <b>Agente de Carreira | ALERTA DE ERRO</b>\n"
            f"🕐 {now}\n\n"
            f"<code>{error_msg[:500]}</code>\n\n"
            f"📊 <a href=\"{DASHBOARD_URL}\">Ver Dashboard</a>\n"
            f"<i>Verifique o GitHub Actions para mais detalhes.</i>"
        )
        self._send(message)


if __name__ == "__main__":
    # Teste local (requer variaveis de ambiente configuradas)
    notifier = TelegramNotifier()
    notifier.send_job_report(
        jobs=[
            {
                "title":       "Senior IT Project Manager",
                "company":     "ACME Corp",
                "match_score": 85,
                "url":         "https://remotive.com/job/example",
                "source":      "remotive",
                "location":    "Remote",
            }
        ],
        session_label="Teste Local",
    )
