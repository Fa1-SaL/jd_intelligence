from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_jd_parser import get_valid_llm_output

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

        data, jd, email, titles = get_valid_llm_output(raw, url=request.url)

        print("LLM finished")

        return {
            "success": True,
            "jd": jd,
            "email": email,
            "titles": titles,
            "structured_data": data
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