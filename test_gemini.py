from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
print("API key loaded:", bool(os.getenv("GEMINI_API_KEY")))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
print("Client created, sending request...")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Say hello in one line"
)
print("Response received:")
print(response.text)