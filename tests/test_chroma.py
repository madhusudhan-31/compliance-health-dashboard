from services.chroma_client import ChromaClient

client = ChromaClient()

# Add sample health data
client.add_data([
    "Low oxygen levels detected in patient",
    "Chest pain indicating possible heart issue",
    "High fever and cough symptoms reported"
])

# Query similar health data
result = client.query("low oxygen symptoms")

print("\nRESULT:\n", result)