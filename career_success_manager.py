"""
Gerenciador central dos 3 times:
1) RH Specialist (busca e filtro de vagas)
2) Submission Team (auto-submissao backend)
3) Career Coach (insights estrategicos de carreira)
"""

from datetime import datetime

from rh_specialist import run_agent
from submission_engine import SubmissionEngine
from telegram_notifier import TelegramNotifier


class CareerSuccessManager:
    def __init__(self, max_auto_apply: int = 3):
        self.max_auto_apply = max_auto_apply
        self.submission_engine = SubmissionEngine()
        self.notifier = TelegramNotifier()

    def _run_submission_team(self, jobs: list) -> list:
        submitted = []
        for job in jobs[: self.max_auto_apply]:
            company = job.get("company", "Empresa")
            role = job.get("title", "Cargo")
            endpoint = job.get("url") or "https://careers.example.com"
            result = self.submission_engine.execute_backend_submission(company, role, endpoint)
            submitted.append(result)
        return submitted

    def _build_coach_insights(self, report: dict, submitted_count: int) -> list:
        insights = []
        total_new = report.get("total_new", 0)
        total_matched = report.get("total_matched", 0)
        source_stats = report.get("source_stats", {})

        if total_new == 0:
            insights.append("Hoje o foco ideal e ajustar palavras-chave para ampliar novas vagas qualificadas.")
        else:
            insights.append("Priorize as vagas novas com maior match e resposta rapida em ate 24h.")

        if total_matched > 0 and total_new == 0:
            insights.append("Ha vagas aderentes, mas sem novidades: intensifique canais Brasil e filtros por senioridade.")

        best_source = None
        best_accepted = -1
        for source_info in source_stats.values():
            accepted = source_info.get("accepted", 0)
            if accepted > best_accepted:
                best_accepted = accepted
                best_source = source_info.get("label", "Fonte")

        if best_source and best_accepted > 0:
            insights.append(f"Fonte mais produtiva do ciclo: {best_source} ({best_accepted} vagas aderentes).")

        insights.append(f"Submissoes automaticas realizadas neste ciclo: {submitted_count}.")
        return insights

    def run_full_cycle(
        self,
        session_label: str = "Operacao 3 Times",
        notify_telegram: bool = True,
        include_linkedin: bool | None = None,
        location_scope: str = "global",
    ) -> dict:
        started_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("\n" + "=" * 60)
        print(f"GERENTE DE CARREIRA INICIADO - {session_label}")
        print(f"Horario: {started_at}")
        print("=" * 60 + "\n")

        rh_report = run_agent(
            session_label=f"{session_label} | RH Specialist",
            notify_telegram=notify_telegram,
            include_linkedin=include_linkedin,
            location_scope=location_scope,
        )
        new_jobs = rh_report.get("new_jobs", [])

        print("\n[Team 2/3] Submission Team em execucao...")
        submitted = self._run_submission_team(new_jobs)

        print("\n[Team 3/3] Career Coach gerando recomendacoes...")
        insights = self._build_coach_insights(rh_report, len(submitted))

        manager_report = {
            "session_label": session_label,
            "started_at": started_at,
            "rh": rh_report,
            "submitted": submitted,
            "insights": insights,
        }

        if notify_telegram:
            self.notifier.send_management_report(manager_report)
        return manager_report


if __name__ == "__main__":
    manager = CareerSuccessManager(max_auto_apply=3)
    manager.run_full_cycle(session_label="Execucao Manual")
