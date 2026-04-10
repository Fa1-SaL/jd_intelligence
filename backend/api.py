from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_jd_parser import get_valid_llm_output
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional

class JDRequest(BaseModel):
    raw_jd: str
    url: Optional[str] = None
    client: str = "mercor"


def clean_input(text: str) -> str:
    """
    Makes raw JD safe and consistent before sending to LLM
    """
    if not text:
        return ""

    # normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # remove weird control characters
    text = "".join(ch for ch in text if ch.isprintable() or ch == "\n")

    # collapse excessive spacing
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join([line for line in lines if line])

    return text.strip()

@app.post("/parse-jd")
def parse_jd(request: JDRequest):
    try:
        print("Received request")

        raw = clean_input(request.raw_jd)

        if not raw:
            return {
                "success": False,
                "error": "Empty JD provided"
            }

        print("Calling LLM...")

        parsed_result = get_valid_llm_output(raw, url=request.url, client=request.client)

        print("LLM finished")

        return {
            "success": True,
            **parsed_result
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/")
def health_check():
    return {"status": "running"}