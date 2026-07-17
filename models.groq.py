import requests
import os
import dotenv
dotenv.load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
data = response.json()["data"]

# Agrupar por tipo de output (texto, audio, speech, etc)
grupos = {}
for m in data:
    tipo = ", ".join(m.get("output_modalities", ["?"]))
    grupos.setdefault(tipo, []).append(m)

for tipo, modelos in grupos.items():
    print(f"\n=== {tipo.upper()} ({len(modelos)}) ===")
    print(f"{'ID':<38} {'CTX':>8} {'MAX_OUT':>8}  {'PRECIO (in/out)':<20} FEATURES")
    print("-" * 100)
    for m in sorted(modelos, key=lambda x: x["id"]):
        ctx = m.get("context_window", "-")
        max_out = m.get("max_completion_tokens", "-")
        pricing = m.get("pricing")
        if pricing:
            precio = f"${float(pricing.get('prompt', 0)):.7f}/${float(pricing.get('completion', 0)):.7f}"
        else:
            precio = "gratis/N-A"
        features = ", ".join(m.get("supported_features", [])) or "-"
        print(f"{m['id']:<38} {ctx:>8} {max_out:>8}  {precio:<20} {features}")