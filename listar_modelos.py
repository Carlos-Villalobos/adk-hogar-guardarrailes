"""Lista los modelos que tu GOOGLE_API_KEY puede usar con generateContent."""
from google import genai

with genai.Client() as cliente:
    for m in cliente.models.list():
        if "generateContent" in (m.supported_actions or []):
            print(m.name.removeprefix("models/"))
