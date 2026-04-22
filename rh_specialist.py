import os
import json
from datetime import datetime

class RHDoctorAgent:
    def __init__(self, candidate_name="Carlos Costato"):
        self.candidate_name = candidate_name
        self.specialties = ["IA Specialist", "Cybersecurity Governance", "Senior IT Project Manager"]
        self.target_salary_min = 20000  # Exemplo de meta ambiciosa
        self.applied_jobs = []

    def analyze_job(self, job_title, job_description):
        """
        Analisa se uma vaga tem 'Match' com o perfil de elite do Carlos.
        """
        score = 0
        keywords = ["IA", "AI", "Cybersecurity", "Governance", "Senior", "Project Manager", "Enterprise"]
        
        for word in keywords:
            if word.lower() in job_description.lower() or word.lower() in job_title.lower():
                score += 15
        
        result = {
            "title": job_title,
            "match_score": score,
            "status": "Recommended" if score > 50 else "Monitor",
            "reason": f"Forte presença de palavras-chave: {score}% de aderência técnica."
        }
        return result

    def generate_cover_letter(self, job_details):
        """
        Gera uma carta de apresentação personalizada e agressiva (estratégica).
        """
        letter = f"""
Prezada equipe de Recrutamento,

Como Senior IT Project Manager com especialização em IA pela FIAP e sólida bagagem em Cybersecurity, acompanho de perto o impacto da {job_details['company']} no mercado.

Minha trajetória envolve a gestão de governança para 7.000+ usuários e a entrega de soluções de automação que transformam dor operacional em ROI real. Estou pronto para aplicar essa expertise em {job_details['title']} para elevar os resultados da sua equipe.

Atenciosamente,
{self.candidate_name}
        """
        return letter

# Inicialização do Agente
if __name__ == "__main__":
    doctor = RHDoctorAgent()
    print(f"--- Agente Doutor em RH Iniciado para {doctor.candidate_name} ---")
    print("Monitorando vagas de IA e Cyber...")
