import time
from rh_specialist import RHDoctorAgent
from submission_engine import SubmissionEngine

def start_background_hunt():
    doctor = RHDoctorAgent()
    engine = SubmissionEngine()
    
    print("--- MODO SUPER AGENTE ATIVADO (LOOP INFINITO) ---")
    print("Monitorando o mercado em busca de vagas Sênior de IA e Transformação Digital...")
    
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Iniciando novo ciclo de busca...")
        
        # Simulação de detecção e submissão automática
        # Em um cenário real, aqui entrariam as chamadas de API de busca
        new_jobs = [
            {"company": "Amazon AWS", "role": "Solutions Architect AI"},
            {"company": "Accenture", "role": "Senior Digital Strategist"}
        ]
        
        for job in new_jobs:
            print(f"> Vaga detectada: {job['role']} na {job['company']}")
            engine.execute_backend_submission(job['company'], job['role'], "https://api.careers.com")
            
        print("Ciclo concluído. Próxima busca em 4 horas...")
        time.sleep(14400) # Aguarda 4 horas (14400 segundos)

if __name__ == "__main__":
    start_background_hunt()
