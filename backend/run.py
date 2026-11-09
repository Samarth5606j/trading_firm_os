import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY is not set in backend/.env!")
    else:
        print("GROQ_API_KEY loaded successfully.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)