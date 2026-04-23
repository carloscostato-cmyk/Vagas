"""
RH Specialist Agent - Busca de vagas + notificacao Telegram.
"""

import json
import os
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from telegram_notifier import TelegramNotifier


CANDIDATE = {
    "name": "Carlos Costato",
    "keywords": [
        "Senior IT Project Manager",
        "Gerente de Projetos",
        "Head of IT",
        "IT Director",
        "Gerente de TI",
        "Cybersecurity Manager",
        "Information Security Manager",
        "AI Project Manager",
        "Gerente de Inteligencia Artificial",
        "Technology Manager",
        "Digital Transformation Lead",
        "Scrum Master Senior",
        "Agile Coach",
    ],
    "score_keywords": [
        "IA", "AI", "Artificial Intelligence", "Inteligencia Artificial", "Generative AI",
        "Cybersecurity", "Ciberseguranca", "InfoSec", "Information Security",
        "Governance", "Governanca", "Compliance", "Risk Management", "Gestao de Riscos",
        "Senior", "Project Manager", "Gestor de Projetos", "Lideranca", "Leadership",
        "Head", "Manager", "Gerente", "Enterprise", "Missao Critica",
        "Power Platform", "Power BI", "Power Automate", "Power Apps", "SharePoint",
        "Microsoft 365", "RPA", "Automacao", "Automation", "Dashboard", "BI",
        "Business Intelligence", "Analytics",
        "Transformacao Digital", "Digital Transformation", "Agile", "Scrum",
        "Kanban", "ITIL", "COBIT", "PMBOK", "SLA", "KPI", "ROI",
        "FIAP", "Estrategia", "Strategy", "Inovacao", "Innovation",
    ],
}

DISALLOWED_LANGUAGE_PATTERNS = [
    "fluent english required",
    "advanced english required",
    "business fluent english",
    "professional english required",
    "native english",
    "english is mandatory",
    "mandatory english",
    "c1 english",
    "c2 english",
    "english proficiency c1",
    "english proficiency c2",
    "bilingual mandatory",
    "must be fluent in english",
    "ingles fluente obrigatorio",
    "ingles avancado obrigatorio",
    "ingles obrigatorio",
    "ingles e obrigatorio",
]

SOURCE_LABELS = {
    "remotive": "Remotive",
    "arbeitnow": "Arbeitnow",
    "linkedin": "LinkedIn",
    "freelance": "Freelance",
    "brasiltech": "BrasilTech",
}

APPLICATIONS_FILE = os.path.join(os.path.dirname(__file__), "applications.json")
RUN_SUMMARY_FILE = os.path.join(os.path.dirname(__file__), "run_summary.json")

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_job(title: str, company: str, url: str, description: str, source: str, location: str) -> dict:
    return {
        "title": title,
        "company": company,
        "url": url,
        "description": description,
        "source": source,
        "location": location,
        "found_at": now_ts(),
    }


def linkedin_credentials_configured() -> bool:
    user = os.environ.get("LOGIN_USER_LINKEDIN", "").strip()
    pwd = os.environ.get("KEY_SENHA_LINKEDIN", "").strip()
    return bool(user and pwd)


def fetch_remotive_jobs() -> list:
    jobs_found = []
    search_terms = [
        "project manager", "it manager", "cybersecurity", "ai manager",
        "digital transformation", "scrum master", "it governance",
        "gerente de projetos", "gerente de ti", "inteligencia artificial",
        "freelance project manager", "contract it manager",
    ]

    try:
        for kw in search_terms:
            url = f"https://remotive.com/api/remote-jobs?search={quote_plus(kw)}&limit=12"
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                continue
            for job in resp.json().get("jobs", []):
                jobs_found.append(
                    build_job(
                        title=job.get("title", ""),
                        company=job.get("company_name", ""),
                        url=job.get("url", ""),
                        description=job.get("description", ""),
                        source=SOURCE_LABELS["remotive"],
                        location=job.get("candidate_required_location", "Remote"),
                    )
                )
    except Exception as e:
        print(f"WARN: Remotive fetch error: {e}")

    return jobs_found


def fetch_arbeitnow_jobs() -> list:
    jobs_found = []
    try:
        searches = ["IT+project+manager", "cybersecurity", "digital+transformation", "scrum+master"]
        for term in searches:
            url = f"https://www.arbeitnow.com/api/job-board-api?search={term}"
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                continue
            for job in resp.json().get("data", []):
                jobs_found.append(
                    build_job(
                        title=job.get("title", ""),
                        company=job.get("company_name", ""),
                        url=job.get("url", ""),
                        description=job.get("description", ""),
                        source=SOURCE_LABELS["arbeitnow"],
                        location=job.get("location", "Remote"),
                    )
                )
    except Exception as e:
        print(f"WARN: Arbeitnow fetch error: {e}")

    return jobs_found


def fetch_linkedin_jobs() -> list:
    """Busca publica no endpoint guest do LinkedIn, com paginação e deduplicacao."""
    jobs_found = []
    seen = set()

    keywords = [
        "Senior IT Project Manager",
        "Gerente de Projetos",
        "Gerente de TI",
        "Cybersecurity Manager",
        "Information Security Manager",
        "Head of IT",
        "AI Project Manager",
        "Digital Transformation Lead",
        "Scrum Master Senior",
        "Agile Coach",
        "freelance project manager",
        "contract project manager",
    ]
    locations = ["Brasil", "Sao Paulo", "Remote", "Hibrido"]

    try:
        for kw in keywords:
            for loc in locations:
                for start in (0, 25, 50):
                    url = (
                        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                        f"?keywords={quote_plus(kw)}&location={quote_plus(loc)}&start={start}"
                    )
                    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select("li")
                    if not cards:
                        continue

                    for card in cards:
                        title_el = card.select_one("h3.base-search-card__title")
                        company_el = card.select_one("h4.base-search-card__subtitle")
                        link_el = card.select_one("a.base-card__full-link")
                        location_el = card.select_one("span.job-search-card__location")

                        title = title_el.get_text(" ", strip=True) if title_el else ""
                        company = company_el.get_text(" ", strip=True) if company_el else ""
                        job_url = link_el.get("href", "").strip() if link_el else ""
                        job_loc = location_el.get_text(" ", strip=True) if location_el else loc

                        if not title or not job_url:
                            continue

                        key = f"{title.lower()}|{company.lower()}|{job_url}"
                        if key in seen:
                            continue
                        seen.add(key)

                        jobs_found.append(
                            build_job(
                                title=title,
                                company=company,
                                url=job_url,
                                description=f"{title} {company} {job_loc}",
                                source=SOURCE_LABELS["linkedin"],
                                location=job_loc,
                            )
                        )
    except Exception as e:
        print(f"WARN: LinkedIn fetch error: {e}")

    return jobs_found


def fetch_remoteok_freelance_jobs() -> list:
    jobs_found = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=REQUEST_HEADERS, timeout=20)
        if resp.status_code != 200:
            return jobs_found

        for job in resp.json():
            if not isinstance(job, dict):
                continue

            title = job.get("position", "")
            company = job.get("company", "")
            tags = " ".join(job.get("tags", []))
            desc = f"{job.get('description', '')} {tags}".lower()
            url = job.get("url", "")
            if url.startswith("/"):
                url = f"https://remoteok.com{url}"

            is_freelance = any(t in desc for t in ["freelance", "contract", "consult", "consultant"])
            if not is_freelance:
                continue

            jobs_found.append(
                build_job(
                    title=title,
                    company=company,
                    url=url,
                    description=f"{job.get('description', '')} {tags}",
                    source=SOURCE_LABELS["freelance"],
                    location=job.get("location", "Remote"),
                )
            )
    except Exception as e:
        print(f"WARN: RemoteOK fetch error: {e}")

    return jobs_found


def fetch_brasiltech_jobs() -> list:
    jobs_found = []
    search_terms = ["gerente de projetos", "gerente de ti", "seguranca da informacao", "transformacao digital"]
    try:
        for kw in search_terms:
            url = f"https://programathor.com.br/jobs?search={quote_plus(kw)}"
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for anchor in soup.select("a"):
                href = anchor.get("href", "")
                title = anchor.get_text(" ", strip=True)
                if not href or not title or "/jobs/" not in href:
                    continue
                full_url = href if href.startswith("http") else f"https://programathor.com.br{href}"
                jobs_found.append(
                    build_job(
                        title=title,
                        company="Programathor",
                        url=full_url,
                        description=f"{title} Brasil Tecnologia",
                        source=SOURCE_LABELS["brasiltech"],
                        location="Brasil",
                    )
                )
    except Exception as e:
        print(f"WARN: BrasilTech fetch error: {e}")

    dedup = {}
    for job in jobs_found:
        dedup[job["url"]] = job
    return list(dedup.values())


def calculate_match(title: str, description: str) -> int:
    score = 0
    text = f"{title} {description}".lower()
    for kw in CANDIDATE["score_keywords"]:
        kw_l = kw.lower()
        if kw_l in text:
            if kw_l in ["senior", "project manager", "cybersecurity", "ia", "ai", "governanca", "governance", "head"]:
                score += 15
            else:
                score += 8
    return min(score, 100)


def is_profile_related(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(kw.lower() in text for kw in CANDIDATE["keywords"]) or any(
        kw in text for kw in ["project manager", "gerente", "it", "cyber", "security", "ai", "transforma"]
    )


def is_valid_job_url(url: str) -> bool:
    if not url or url in ("#", ""):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def is_language_requirement_compatible(job: dict) -> bool:
    text = " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        str(job.get("requirements", "")),
    ]).lower()
    return not any(pattern in text for pattern in DISALLOWED_LANGUAGE_PATTERNS)


def load_existing_applications() -> list:
    try:
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_applications(apps: list):
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=4, ensure_ascii=False)


def save_run_summary(summary: dict):
    with open(RUN_SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)


def filter_jobs_with_stats(raw_jobs_by_source: dict) -> tuple[list, dict]:
    filtered = []
    stats = {}

    for source_key, label in SOURCE_LABELS.items():
        stats[source_key] = {
            "label": label,
            "collected": 0,
            "accepted": 0,
            "discarded": {
                "invalid_url": 0,
                "out_of_profile": 0,
                "language_requirement": 0,
                "low_match": 0,
            },
        }

    for source_key, jobs in raw_jobs_by_source.items():
        for job in jobs:
            stats[source_key]["collected"] += 1

            if not is_valid_job_url(job.get("url", "")):
                stats[source_key]["discarded"]["invalid_url"] += 1
                continue

            title = job.get("title", "")
            desc = job.get("description", "")

            if not is_profile_related(title, desc):
                stats[source_key]["discarded"]["out_of_profile"] += 1
                continue

            if not is_language_requirement_compatible(job):
                stats[source_key]["discarded"]["language_requirement"] += 1
                continue

            score = calculate_match(title, desc)
            if score < 30:
                stats[source_key]["discarded"]["low_match"] += 1
                continue

            job["match_score"] = score
            filtered.append(job)
            stats[source_key]["accepted"] += 1

    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return filtered, stats


def deduplicate_and_save(new_jobs: list) -> tuple[list, int]:
    existing = [
        app for app in load_existing_applications()
        if is_valid_job_url(app.get("url", "")) and is_language_requirement_compatible(app)
    ]
    existing_urls = {app.get("url") for app in existing}
    truly_new = [j for j in new_jobs if j.get("url") not in existing_urls]
    final_apps = existing + truly_new
    save_applications(final_apps)
    return truly_new, len(final_apps)


def build_run_summary(session_label: str, source_stats: dict, total_filtered: int, total_saved: int, total_new: int) -> dict:
    return {
        "generated_at": now_ts(),
        "session_label": session_label,
        "linkedin_credentials_configured": linkedin_credentials_configured(),
        "sources": source_stats,
        "totals": {
            "filtered": total_filtered,
            "saved": total_saved,
            "new": total_new,
        },
    }


def run_agent(session_label: str = "Ciclo Automatico"):
    print("\n" + "=" * 60)
    print(f"AGENTE DE RH INICIADO - {session_label}")
    print(f"Horario: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
    print("=" * 60 + "\n")

    notifier = TelegramNotifier()
    is_valid_telegram, validation_msg = notifier.validate_configuration()
    print(f"Telegram check: {validation_msg}")
    if not is_valid_telegram:
        raise RuntimeError(f"Configuracao Telegram invalida: {validation_msg}")

    if linkedin_credentials_configured():
        print("INFO: Credenciais LinkedIn detectadas nos secrets do workflow.")

    try:
        print("Buscando vagas nas fontes publicas...")
        raw_jobs_by_source = {
            "remotive": fetch_remotive_jobs(),
            "arbeitnow": fetch_arbeitnow_jobs(),
            "linkedin": fetch_linkedin_jobs(),
            "freelance": fetch_remoteok_freelance_jobs(),
            "brasiltech": fetch_brasiltech_jobs(),
        }

        total_raw = sum(len(v) for v in raw_jobs_by_source.values())
        print(f" -> {total_raw} vagas brutas coletadas")

        matched_jobs, source_stats = filter_jobs_with_stats(raw_jobs_by_source)
        print(f" -> {len(matched_jobs)} vagas com match suficiente")

        for source_key, info in source_stats.items():
            d = info["discarded"]
            print(
                f"    [{info['label']}] coletadas={info['collected']} aceitas={info['accepted']} "
                f"descartes(url={d['invalid_url']}, perfil={d['out_of_profile']}, idioma={d['language_requirement']}, score={d['low_match']})"
            )

        new_jobs, total_saved = deduplicate_and_save(matched_jobs)
        print(f" -> {len(new_jobs)} vagas novas. Total salvo: {total_saved}")

        summary = build_run_summary(
            session_label=session_label,
            source_stats=source_stats,
            total_filtered=len(matched_jobs),
            total_saved=total_saved,
            total_new=len(new_jobs),
        )
        save_run_summary(summary)

        print("Enviando relatorio ao Telegram...")
        sent = notifier.send_job_report(
            jobs=new_jobs if new_jobs else matched_jobs[:5],
            session_label=session_label,
        )
        if not sent:
            raise RuntimeError("Falha ao enviar mensagem ao Telegram. Verifique TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID.")

    except Exception as e:
        print(f"ERRO: {e}")
        notifier.send_error_alert(str(e))
        raise


if __name__ == "__main__":
    import sys

    label = sys.argv[1] if len(sys.argv) > 1 else "Manual"
    run_agent(session_label=label)
