import os
import sys

from dotenv import load_dotenv
from google import genai

# Add src to path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import config


def test_gemini_connection():
    print(f"Testing connection with model: {config.DEFAULT_MODEL}")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    try:
        client = genai.Client(api_key=api_key)

        print("Sending test prompt...")
        response = client.models.generate_content(
            model=config.DEFAULT_MODEL,
            contents="Hello, are you Gemini 3.0? Please confirm your version."
        )

        print("\n--- Response received ---")
        print(response.text)
        print("-------------------------")
        print("\nSUCCESS: Connection established and content generated.")

    except Exception as e:
        print("\nERROR: Failed to connect or generate content.")
        print(f"Error details: {str(e)}")

        if "429" in str(e):
            print("\nDiagnosis: Rate limit exceeded (Quota exceeded).")
        elif "404" in str(e):
            print(f"\nDiagnosis: Model '{config.DEFAULT_MODEL}' not found. It might not be available to your API key yet.")
        elif "403" in str(e):
            print("\nDiagnosis: Permission denied. Check API key restrictions.")

def list_available_models():
    print("Listing available models...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return

    try:
        client = genai.Client(api_key=api_key)
        # List models that support generateContent
        for m in client.models.list():
            print(f"Model: {m.name}")

    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    load_dotenv()
    test_gemini_connection()
    # list_available_models()
