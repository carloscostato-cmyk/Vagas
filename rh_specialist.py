"""
RH Specialist Agent - Busca de vagas + notificacao Telegram.
"""

import json
import os
from datetime import datetime
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from telegram_notifier import TelegramNotifier
from language_specialist_agent import LanguageSpecialistAgent
from brazil_specialist_agent import BrazilSpecialistAgent


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
    "native english",
    "english is mandatory",
    "mandatory english",
    "c1 english",
    "c2 english",
    "english proficiency c1",
    "english proficiency c2",
    "bilingual mandatory",
    "ingles fluente obrigatorio",
    "ingles obrigatorio",
    "ingles e obrigatorio",
]

SOURCE_LABELS = {
    "remotive": "Remotive",
    "arbeitnow": "Arbeitnow",
    "linkedin": "LinkedIn",
    "freelance": "Freelance",
    "brasiltech": "BrasilTech",
    "gupy": "Gupy",
    "indeed": "Indeed",
    "catho": "Catho",
}

BRAZIL_LOCATION_HINTS = [
    "brasil",
    "brazil",
    "sao paulo",
    "rio de janeiro",
    "belo horizonte",
    "curitiba",
    "porto alegre",
    "recife",
    "fortaleza",
    "campinas",
    "hibrido",
    "hibrida",
    "presencial",
    "remoto brasil",
    "remote brazil",
]

APPLICATIONS_FILE = os.path.join(os.path.dirname(__file__), "applications.json")
RUN_SUMMARY_FILE = os.path.join(os.path.dirname(__file__), "run_summary.json")

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "trk",
    "tracking",
    "ref",
    "refid",
}


def linkedin_source_enabled() -> bool:
    """
    Controla se as vagas do LinkedIn entram no pipeline.
    Default: ativado.
    """
    return os.environ.get("ENABLE_LINKEDIN_SOURCE", "true").strip().lower() in ("1", "true", "yes", "on")


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


def fetch_gupy_jobs() -> list:
    jobs_found = []
    # Usar agente especialista para termos em português
    brazil_agent = BrazilSpecialistAgent()
    search_terms = brazil_agent.get_search_terms_for_source("gupy")
    
    try:
        for kw in search_terms:
            url = f"https://portal.gupy.io/job-search/term?query={quote_plus(kw)}"
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for anchor in soup.select("a[href]"):
                href = anchor.get("href", "").strip()
                title = anchor.get_text(" ", strip=True)
                if not href or not title:
                    continue
                if "/jobs/" not in href:
                    continue

                full_url = href if href.startswith("http") else f"https://portal.gupy.io{href}"
                jobs_found.append(
                    build_job(
                        title=title,
                        company="Gupy",
                        url=full_url,
                        description=f"{title} Gupy Brasil",
                        source=SOURCE_LABELS["gupy"],
                        location="Brasil",
                    )
                )
    except Exception as e:
        print(f"WARN: Gupy fetch error: {e}")

    dedup = {}
    for job in jobs_found:
        dedup[job["url"]] = job
    return list(dedup.values())


def fetch_indeed_jobs() -> list:
    jobs_found = []
    search_terms = ["gerente+de+projetos", "gerente+de+ti", "cybersecurity+manager", "ai+project+manager"]
    try:
        for term in search_terms:
            url = f"https://br.indeed.com/jobs?q={term}&l=Brasil"
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for anchor in soup.select("a[href]"):
                href = anchor.get("href", "").strip()
                title = anchor.get_text(" ", strip=True)
                if not href or not title:
                    continue
                if "/viewjob" not in href:
                    continue

                full_url = href if href.startswith("http") else f"https://br.indeed.com{href}"
                jobs_found.append(
                    build_job(
                        title=title,
                        company="Indeed",
                        url=full_url,
                        description=f"{title} Indeed Brasil",
                        source=SOURCE_LABELS["indeed"],
                        location="Brasil",
                    )
                )
    except Exception as e:
        print(f"WARN: Indeed fetch error: {e}")

    dedup = {}
    for job in jobs_found:
        dedup[job["url"]] = job
    return list(dedup.values())


def fetch_catho_jobs() -> list:
    jobs_found = []
    # Usar agente especialista para termos em português
    brazil_agent = BrazilSpecialistAgent()
    search_terms = brazil_agent.get_search_terms_for_source("catho")
    
    try:
        for term in search_terms:
            url = f"https://www.catho.com.br/vagas/{term}/"
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for anchor in soup.select("a[href]"):
                href = anchor.get("href", "").strip()
                title = anchor.get_text(" ", strip=True)
                if not href or not title:
                    continue
                if "/vagas/" not in href:
                    continue

                full_url = href if href.startswith("http") else f"https://www.catho.com.br{href}"
                jobs_found.append(
                    build_job(
                        title=title,
                        company="Catho",
                        url=full_url,
                        description=f"{title} Catho Brasil",
                        source=SOURCE_LABELS["catho"],
                        location="Brasil",
                    )
                )
    except Exception as e:
        print(f"WARN: Catho fetch error: {e}")

    dedup = {}
    for job in jobs_found:
        dedup[job["url"]] = job
    return list(dedup.values())


def calculate_match(title: str, description: str) -> int:
    score = 0
    text = f"{title} {description}".lower()
    
    # Keywords de alto peso (nível sênior/especialista)
    senior_keywords = ["senior", "project manager", "cybersecurity", "ia", "ai", "governanca", "governance", "head", "director", "manager", "gerente", "lead", "líder"]
    
    # Keywords médio peso (tecnologias específicas)
    tech_keywords = ["power platform", "power bi", "power automate", "microsoft 365", "sharepoint", "rpa", "automacao", "business intelligence", "analytics"]
    
    # Keywords baixo peso (conceitos gerais)
    general_keywords = ["transformacao digital", "digital transformation", "agile", "scrum", "kanban", "itil", "cobit", "pmbok", "sla", "kpi", "roi"]
    
    for kw in CANDIDATE["score_keywords"]:
        kw_l = kw.lower()
        if kw_l in text:
            if kw_l in senior_keywords:
                score += 15
            elif kw_l in tech_keywords:
                score += 12
            elif kw_l in general_keywords:
                score += 8
            else:
                score += 5
    
    # Bônus para vagas no Brasil
    if any(hint in text for hint in BRAZIL_LOCATION_HINTS):
        score += 10
    
    # Penalidade para vagas genéricas/junior
    junior_indicators = ["junior", "trainee", "estágio", "intern", "entry level", "0-2 years", "iniciante"]
    if any(indicator in text for indicator in junior_indicators):
        score -= 20
    
    # Penalidade para vagas muito específicas de outros países (exceto se permitir home office)
    non_brazil_indicators = ["europe", "usa", "uk", "canada", "australia", "asia", "germany", "netherlands"]
    if any(indicator in text for indicator in non_brazil_indicators) and "remote" not in text:
        score -= 15
    
    # NOVO: Aplicar agentes especialistas
    language_agent = LanguageSpecialistAgent()
    brazil_agent = BrazilSpecialistAgent()
    
    # Score do agente de idioma (prioriza português)
    language_score = language_agent.calculate_language_score(title, description)
    score += language_score
    
    # Score do agente brasileiro (prioriza mercado brasileiro)
    # Nota: company e url não disponíveis aqui, mas source pode ajudar
    brazil_score = brazil_agent.calculate_brazil_score(title, description, "", "", "")
    score += int(brazil_score * 0.3)  # Aplicar 30% do score brasileiro
    
    return min(max(score, 0), 100)


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


def normalize_job_url(url: str) -> str:
    """Normaliza URL para deduplicacao estavel entre fontes e ciclos."""
    if not is_valid_job_url(url):
        return ""

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    host = (parsed.netloc or "").lower()
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    kept_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        if key.lower() in TRACKING_QUERY_PARAMS:
            continue
        kept_query.append((key, value))

    query = urlencode(sorted(kept_query)) if kept_query else ""
    if query:
        return f"{scheme}://{host}{path}?{query}"
    return f"{scheme}://{host}{path}"


def job_dedup_key(job: dict) -> str:
    """Chave unica por vaga, priorizando URL normalizada."""
    normalized_url = normalize_job_url(str(job.get("url", "")))
    if normalized_url:
        return f"url:{normalized_url}"

    title = str(job.get("title", "")).strip().lower()
    company = str(job.get("company", "")).strip().lower()
    source = str(job.get("source", "")).strip().lower()
    return f"meta:{title}|{company}|{source}"


def deduplicate_jobs(jobs: list) -> list:
    """Remove repeticoes preservando o primeiro registro visto."""
    unique = {}
    for job in jobs:
        key = job_dedup_key(job)
        if key in unique:
            continue
        normalized = normalize_job_url(str(job.get("url", "")))
        if normalized:
            job = {**job, "url": normalized}
        unique[key] = job
    return list(unique.values())


def is_language_requirement_compatible(job: dict) -> bool:
    text = " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        str(job.get("requirements", "")),
    ]).lower()
    return not any(pattern in text for pattern in DISALLOWED_LANGUAGE_PATTERNS)


def is_location_scope_compatible(job: dict, location_scope: str) -> bool:
    """
    location_scope:
      - "global": sem filtro de localizacao
      - "brazil": aceita apenas vagas com sinais de localizacao no Brasil
    """
    if location_scope == "global":
        return True

    text = " ".join([
        str(job.get("location", "")),
        str(job.get("title", "")),
        str(job.get("description", "")),
    ]).lower()
    return any(hint in text for hint in BRAZIL_LOCATION_HINTS)


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


def filter_jobs_with_stats(raw_jobs_by_source: dict, location_scope: str = "global") -> tuple[list, dict]:
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
                    "location_scope": 0,
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

            if not is_location_scope_compatible(job, location_scope):
                stats[source_key]["discarded"]["location_scope"] += 1
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

    existing = deduplicate_jobs(existing)
    new_jobs = deduplicate_jobs(new_jobs)

    existing_keys = {job_dedup_key(app) for app in existing}
    truly_new = [j for j in new_jobs if job_dedup_key(j) not in existing_keys]
    final_apps = deduplicate_jobs(existing + truly_new)
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


def run_agent(
    session_label: str = "Ciclo Automatico",
    notify_telegram: bool = True,
    include_linkedin: bool | None = None,
    location_scope: str = "global",
) -> dict:
    print("\n" + "=" * 60)
    print(f"AGENTE DE RH INICIADO - {session_label}")
    print(f"Horario: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
    print("=" * 60 + "\n")

    notifier = TelegramNotifier()
    is_valid_telegram, validation_msg = notifier.validate_configuration()
    print(f"Telegram check: {validation_msg}")
    if not is_valid_telegram:
        print("WARN: Telegram indisponivel para este ciclo. Coleta e persistencia continuarao normalmente.")

    if linkedin_credentials_configured():
        print("INFO: Credenciais LinkedIn detectadas nos secrets do workflow.")

    try:
        print("Buscando vagas nas fontes publicas...")
        linkedin_enabled = linkedin_source_enabled() if include_linkedin is None else include_linkedin
        raw_jobs_by_source = {
            "remotive": fetch_remotive_jobs(),
            "arbeitnow": fetch_arbeitnow_jobs(),
            "linkedin": fetch_linkedin_jobs() if linkedin_enabled else [],
            "freelance": fetch_remoteok_freelance_jobs(),
            "brasiltech": fetch_brasiltech_jobs(),
            "gupy": fetch_gupy_jobs(),
            "indeed": fetch_indeed_jobs(),
            "catho": fetch_catho_jobs(),
        }
        if not linkedin_enabled:
            print("INFO: Fonte LinkedIn desativada (ENABLE_LINKEDIN_SOURCE=false).")

        total_raw = sum(len(v) for v in raw_jobs_by_source.values())
        print(f" -> {total_raw} vagas brutas coletadas")

        matched_jobs, source_stats = filter_jobs_with_stats(raw_jobs_by_source, location_scope=location_scope)
        print(f" -> {len(matched_jobs)} vagas com match suficiente")

        for source_key, info in source_stats.items():
            d = info["discarded"]
            print(
                f"    [{info['label']}] coletadas={info['collected']} aceitas={info['accepted']} "
                f"descartes(url={d['invalid_url']}, perfil={d['out_of_profile']}, idioma={d['language_requirement']}, local={d['location_scope']}, score={d['low_match']})"
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

        notification_status = "skipped"
        if notify_telegram and is_valid_telegram:
            print("Enviando relatorio ao Telegram...")
            sent = notifier.send_job_report(jobs=new_jobs, session_label=session_label)
            notification_status = "sent" if sent else "failed"
            if not sent:
                print("WARN: Falha ao enviar mensagem ao Telegram (ciclo mantido como sucesso operacional).")
        elif not notify_telegram:
            print("INFO: Relatorio Telegram desativado para este ciclo (notify_telegram=False).")
        else:
            print("INFO: Relatorio Telegram nao enviado por configuracao invalida.")

        return {
            "session_label": session_label,
            "telegram": {
                "configured": is_valid_telegram,
                "validation_message": validation_msg,
                "status": notification_status,
            },
            "total_raw": total_raw,
            "total_matched": len(matched_jobs),
            "total_saved": total_saved,
            "total_new": len(new_jobs),
            "source_stats": source_stats,
            "new_jobs": new_jobs,
            "top_jobs": matched_jobs[:5],
            "summary": summary,
        }

    except Exception as e:
        print(f"ERRO: {e}")
        if is_valid_telegram:
            notifier.send_error_alert(str(e))
        raise


if __name__ == "__main__":
    import sys

    label = sys.argv[1] if len(sys.argv) > 1 else "Manual"
    run_agent(session_label=label)
