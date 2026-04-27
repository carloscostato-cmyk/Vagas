"""
Módulo de notificação via Telegram Bot.
Responsável por enviar relatórios e alertas de vagas ao Carlos Costato.
"""

import os
import html
import requests
from datetime import datetime

# URL pública do dashboard ao vivo (GitHub Pages)
DASHBOARD_URL = "https://carloscostato-cmyk.github.io/Vagas/"
PORTFOLIO_URL = "https://carloscostato-cmyk.github.io/Costato/"


class TelegramNotifier:
    MAX_TELEGRAM_TEXT_LENGTH = 4096

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
        if len(message) > self.MAX_TELEGRAM_TEXT_LENGTH:
            print(
                "WARN: Mensagem acima do limite do Telegram "
                f"({len(message)} chars). Truncando para {self.MAX_TELEGRAM_TEXT_LENGTH}."
            )
            message = (
                message[: self.MAX_TELEGRAM_TEXT_LENGTH - 80]
                + "\n\n<i>[Mensagem truncada por limite do Telegram]</i>"
            )

        payload = {
            "chat_id":    self.chat_id,
            "text":       message,
            "parse_mode": parse_mode,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok", False):
                print(
                    "FALHA: Telegram rejeitou a mensagem. "
                    f'error_code={data.get("error_code")} description="{data.get("description", "sem descricao")}"'
                )
                return False
            print("OK: Mensagem enviada ao Telegram com sucesso!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"FALHA: Erro ao enviar mensagem para o Telegram: {e}")
            return False
        except ValueError:
            print("FALHA: Resposta da API Telegram nao veio em JSON valido.")
            return False

    def validate_configuration(self) -> tuple[bool, str]:
        """Valida token/chat_id no Telegram antes de enviar mensagens."""
        if not self.bot_token or not self.chat_id:
            return (
                False,
                "TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausentes nos secrets do GitHub.",
            )

        try:
            me_url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            me_resp = requests.get(me_url, timeout=10)
            me_resp.raise_for_status()
            me_data = me_resp.json()
            if not me_data.get("ok", False):
                return (
                    False,
                    f'Token invalido/rejeitado. Telegram: "{me_data.get("description", "sem descricao")}"',
                )

            chat_url = f"https://api.telegram.org/bot{self.bot_token}/getChat"
            chat_resp = requests.get(chat_url, params={"chat_id": self.chat_id}, timeout=10)
            chat_resp.raise_for_status()
            chat_data = chat_resp.json()
            if not chat_data.get("ok", False):
                return (
                    False,
                    f'Chat ID invalido/acesso negado. Telegram: "{chat_data.get("description", "sem descricao")}"',
                )

            return True, "Configuracao Telegram valida."
        except requests.exceptions.RequestException as e:
            return False, f"Falha de rede ao validar Telegram: {e}"
        except ValueError:
            return False, "Resposta invalida (nao JSON) durante validacao do Telegram."

    def send_job_report(self, jobs: list, session_label: str, max_jobs: int = 8) -> bool:
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
            for i, job in enumerate(jobs[:max_jobs], 1):
                score       = job.get("match_score", 0)
                score_emoji = "🔥" if score > 60 else "⭐"
                source      = html.escape(str(job.get("source", "Agente")).capitalize())
                location    = html.escape(str(job.get("location", "")))
                url         = html.escape(str(job.get("url", "")), quote=True)
                title       = html.escape(str(job.get("title", "N/A")))
                loc_str     = f"\n   📍 {location}" if location and location != "Nao informado" else ""
                url_str     = f"\n   🔗 <a href=\"{url}\">Ver Vaga Agora</a>" if url and url not in ("#", "") else ""
                lines.append(
                    f"{score_emoji} <b>{i}. {title}</b>\n"
                    f"   🏢 {html.escape(str(job.get('company', 'N/A')))}\n"
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

        return self._send(message)

    def send_error_alert(self, error_msg: str) -> bool:
        """Envia alerta de erro para o Telegram."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        message = (
            f"⚠️ <b>Agente de Carreira | ALERTA DE ERRO</b>\n"
            f"🕐 {now}\n\n"
            f"<code>{error_msg[:500]}</code>\n\n"
            f"📊 <a href=\"{DASHBOARD_URL}\">Ver Dashboard</a>\n"
            f"<i>Verifique o GitHub Actions para mais detalhes.</i>"
        )
        return self._send(message)

    def send_management_report(self, report: dict, max_jobs: int = 15) -> bool:
        """Envia um resumo consolidado do ciclo com vagas clicaveis."""
        rh = report.get("rh", {})
        insights = report.get("insights", [])
        submitted = report.get("submitted", [])
        jobs = rh.get("new_jobs", [])

        lines = [
            f"🧠 <b>Agente de Carreira | {report.get('session_label', 'Ciclo')}</b>",
            f"🕐 {report.get('started_at', datetime.now().strftime('%d/%m/%Y %H:%M'))}",
            "",
            "<b>Resumo do ciclo:</b>",
            f"• Vagas brutas: {rh.get('total_raw', 0)}",
            f"• Vagas aderentes: {rh.get('total_matched', 0)}",
            f"• Vagas novas: {rh.get('total_new', 0)}",
            f"• Submissoes automaticas: {len(submitted)}",
            "",
            "<b>Direcionamento:</b>",
        ]

        if insights:
            for item in insights[:4]:
                lines.append(f"• {item}")
        else:
            lines.append("• Sem insights neste ciclo.")

        if jobs:
            lines += ["", "<b>Vagas para acao agora:</b>"]
            for i, job in enumerate(jobs[:max_jobs], 1):
                score = int(job.get("match_score", 0))
                score_emoji = "🔥" if score > 60 else "⭐"
                source = html.escape(str(job.get("source", "Agente")).capitalize())
                location = html.escape(str(job.get("location", "")))
                url = html.escape(str(job.get("url", "")), quote=True)
                title = html.escape(str(job.get("title", "N/A")))
                company = html.escape(str(job.get("company", "N/A")))
                loc_str = f"\n   📍 {location}" if location else ""
                url_str = f"\n   🔗 <a href=\"{url}\">Candidatar agora</a>" if url and url not in ("#", "") else ""
                lines.append(
                    f"{score_emoji} <b>{i}. {title}</b>\n"
                    f"   🏢 {company}\n"
                    f"   📡 {source} · 📊 Match: {score}%"
                    f"{loc_str}"
                    f"{url_str}\n"
                )

        lines += ["", f"📊 <a href=\"{DASHBOARD_URL}\">Abrir Dashboard ao Vivo</a>", "<i>Ciclo concluido.</i>"]

        return self._send("\n".join(lines))


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
