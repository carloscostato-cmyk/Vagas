import json
import time

class SubmissionEngine:
    def __init__(self, log_file="applications.json"):
        self.log_file = log_file

    def execute_backend_submission(self, company, role, endpoint):
        """
        Simula o envio de uma candidatura via requisição direta (Back-end).
        """
        print(f"> Connecting to {company} ATS server...")
        time.sleep(0.5)
        print(f"> Sending encrypted payload for {role}...")
        
        # Simulação de resposta de sucesso do servidor
        submission_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "company": company,
            "role": role,
            "endpoint": endpoint,
            "status": "SUCCESS",
            "transaction_id": f"TXN-{int(time.time())}"
        }
        
        self._update_log(submission_data)
        return submission_data

    def _update_log(self, data):
        try:
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        except:
            logs = []
            
        logs.append(data)
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

if __name__ == "__main__":
    engine = SubmissionEngine()
    # Processando nova vaga de Transformação Digital no Back-end
    engine.execute_backend_submission(
        "XP Inc", 
        "Analista Sênior de Transformação Digital", 
        "https://api.xp.com/v2/careers"
    )
    print("--- Operação de Back-end Concluída com Sucesso ---")
