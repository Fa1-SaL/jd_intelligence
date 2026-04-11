import os
import json
import re
import time
from pathlib import Path
from typing import Tuple, Any, Dict, List
from openai import OpenAI
from dotenv import load_dotenv

# Explicitly load .env from the project root (one level above this file's backend/ folder)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

client = OpenAI(api_key=api_key)

CLIENT_DESCRIPTIONS = {
    "Mercor": "Mercor partners with leading AI labs and enterprises to train frontier AI models, offering competitive pay, collaboration with top researchers, and the opportunity to shape next generation AI systems using deep domain expertise.",
    "Micro1": "Micro1 partners with AI labs and enterprises to train and improve foundational models and AI agents, offering advanced evaluation systems, reinforcement learning environments, and contextual monitoring tools to enhance LLM performance and real-world AI deployment."
}

# 1. Define OUTPUT_SCHEMA
OUTPUT_SCHEMA = {
    "role": "",
    "type": "",
    "pay": "",
    "location": "",
    "commitment": "",
    "role_responsibilities": [],
    "requirements": [],
    "role_overview": "",
    "who_this_is_for": "",
    "client": "",
    "client_desc": "",
    "link": "",
    "suggested_titles": [],
    "subject": "",
    "linkedin_title": "",
    "skills": [],
    "job_functions": [],
    "industries": []
}

# 2. generate_llm_output
def generate_llm_output(raw_jd: str, client_name: str = "mercor") -> str:
    """Takes a raw JD, sends to LLM, returns raw JSON response text."""
    
    prompt = """
You are a structured data extractor for recruitment.

Extract ONLY the required variables from the job description.

Output strictly in JSON.
Do NOT generate formatted email or job description.

Expected JSON structure:

{
  "role": "",
  "type": "",
  "pay": "",
  "location": "",
  "commitment": "",
  "role_responsibilities": [],
  "requirements": [],
  "role_overview": "",
  "who_this_is_for": "",
  "client": "{CLIENT_NAME}",
  "client_desc": "short company description",
  "link": "application/referral link if available",
  "suggested_titles": [],
  "subject": "",
  "linkedin_title": "",
  "skills": [],
  "job_functions": ["", "", ""],
  "industries": ["", "", ""]
}

Rules:
- responsibilities and requirements must be lists of bullet points
- keep text concise
- no extra keys
- no markdown
- no explanation outside JSON
- role must be a market-standard job title (no vague terms like "expert")

RESPONSIBILITIES RULES:
- Extract ALL meaningful actions from the JD (even if implicit)
- Expand short responsibilities into clear, complete bullet points
- Combine scattered lines into structured responsibilities
- Target 4–6 bullets when sufficient information exists
- Each bullet must:
  - start with an action verb
  - be specific and complete
  - reflect real work being done

Example Responsibilities:
Input: "create deliverables", "review peer work"
Output:
- Create structured deliverables based on domain-specific tasks and requirements
- Review peer-developed work to ensure quality and alignment with project standards
- Identify issues in outputs and suggest improvements
- Maintain consistency and accuracy across all deliverables

REQUIREMENTS RULES:
- Extract qualifications fully, not partially
- Expand incomplete lines into proper sentences
- Convert "X years" into: "Candidates should have strong relevant experience in the domain"
- Target 4–6 bullets when possible
- Each bullet must:
  - be complete
  - grammatically correct
  - recruiter-friendly

IMPORTANT:
- Do NOT leave bullets short or incomplete
- Do NOT output fragments like: "4+ years experience"
- Always expand into full professional sentences

ROLE OVERVIEW RULES:
- must be 40–70 words
- explain what the candidate will actually do
- include impact of the work
- avoid generic phrasing
- must feel like a real job pitch

Bad: "Assess AI responses"
Good: "Evaluate and improve AI-generated outputs by identifying inaccuracies, refining reasoning, and ensuring domain-specific correctness in high-stakes applications such as finance, healthcare, and legal systems."

WHO_THIS_IS_FOR RULES:
- must be 40–70 words
- clearly define target candidate
- include: domain (finance, legal, etc.), experience level, type of work they’ve done
- avoid vague phrases like "strong skills"

Bad: "Candidates with expertise in finance"
Good: "Professionals with hands-on experience in finance, accounting, law, or healthcare who have worked in analytical, advisory, or compliance roles and are comfortable evaluating complex outputs for accuracy and reasoning."

SUGGESTED TITLES STRICT RULES:
Generate exactly 5 job titles, ranked from best to worst (top = most optimal) inside the JSON list.
1. Titles must be SHORT (4–7 words max before brackets).
2. Use brackets for precision (format: Primary Title (Qualifier 1 & Qualifier 2)).
3. The first 1–2 words must be the strongest keyword for search visibility.
4. Avoid vague words like: Generalist, Operations, Executive.
5. Avoid over-senior or misleading titles (e.g., Engineer, Scientist, Manager unless explicitly required).
6. Do NOT include "AI" in the title unless explicitly instructed.
7. Do NOT overstuff brackets (max 2 qualifiers).
8. Titles must clearly signal the actual work being done (annotation, review, quality, analysis, etc.).
9. Avoid overly generic titles like "Analyst" unless paired with a clear qualifier.
10. Optimize for: high click-through rate, correct candidate targeting, minimal irrelevant applicants.

BRACKETS USAGE (IMPORTANT):
- Brackets are OPTIONAL, not mandatory.
- Use brackets ONLY when they improve clarity or precision.
- Do NOT use brackets if the base title is already clear.

ADDITIONAL TITLE GUIDANCE:
- Assume this is for LinkedIn job posting optimization.
- Prioritize titles that balance reach and relevance.
- Penalize titles that attract the wrong talent pool.
- Prefer "Annotation", "Review", "Quality", "Data" when applicable.
- Before finalizing, internally evaluate each title: Does it attract the right candidate? Does it avoid misleading signals? Is it concise and searchable? Reject weak titles and only output high-quality options.

TITLE EXAMPLES:
Good:
"Response Evaluator (Finance & Compliance)"
"Quality Reviewer (Legal & Accuracy)"
"Content Analyst (Healthcare & Validation)"
"Data Annotator (Finance & Reasoning)"
"Output Reviewer (Domain & Quality)"
"Sports Expert (Football)"

Bad:
"AI Expert"
"Senior AI Evaluator"
"Generalist Analyst"

SUBJECT RULES:
Format: {role} | $X/hr Remote | {CLIENT_NAME} x AI Labs
Remove pay if missing
Do not mention Remote if role is not remote

SKILLS RULES:
- Return EXACTLY 4-5 skills.
- Skills must be BROAD, SEARCHABLE, industry-standard terms that recruiters type into LinkedIn.
- Each skill must be 1-3 words MAX.
- NO soft skills (e.g., communication, teamwork).
- NO niche or descriptive phrases (e.g., "STEM problem-solving", "AI-driven analysis").
- NO verbs or verb phrases.
- Do NOT repeat the role title.
Good examples: Python, SQL, Data Analysis, Machine Learning, Financial Modeling, Project Management, UX Design
Bad examples: Bilingual Communication, AI-Driven Analysis, STEM Problem-Solving

JOB FUNCTIONS RULES:
Select EXACTLY 3 from this EXACT list — copy the values verbatim, no modifications:
Accounting & Auditing, Administrative, Advertising, Analytics, Customer Service, Design, Education, Engineering, Finance, General Business, Health care provider, Human Resources, IT, Legal, Manufacturing, Marketing, Product Management, Project Management, Public Relations, Research, Sales, Strategy/Planning, Training, Consulting, Writing/Editing, Art/Creative
DO NOT invent new values. DO NOT rephrase. Choose based on role responsibilities, not just the job title.

INDUSTRIES RULES:
Select EXACTLY 3 from this EXACT list — copy the values verbatim, no modifications:
Accommodation and Food Services, Administrative and Support Services, Construction, Consumer Services, Education, Entertainment Providers, Farming, Ranching, Forestry, Financial Services, Government Administration, Holding Companies, Hospitals and Health Care, Manufacturing, Oil, Gas, and Mining, Professional Services, Real Estate and Equipment Rental Services, Retail, Technology, Information and Media, Transportation, Logistics, Supply Chain and Storage, Utilities, Wholesale, Research Services, Investment Management, Translation and Localization, Strategic Management Services, Information Services, Higher Education, Primary and Secondary Education, Medical Practices
DO NOT invent new values. DO NOT rephrase. Choose based on the industry context of the role.

Job Description:
""" + raw_jd

    prompt = prompt.replace("{CLIENT_NAME}", client_name.capitalize())

    _t0 = time.time()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output strict JSON only. Do not wrap in formatting blocks."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    print(f"[LLM] Response time: {time.time() - _t0:.2f}s")
    
    return response.choices[0].message.content


# 3. Normalization and Cleaning Utilities

def normalize_client(client: str) -> str:
    if not client or "default" in client.lower():
        return "Mercor"
    return client.strip()

VALID_JOB_FUNCTIONS = [
    "Accounting & Auditing", "Administrative", "Advertising", "Analytics",
    "Customer Service", "Design", "Education", "Engineering", "Finance",
    "General Business", "Health care provider", "Human Resources", "IT",
    "Legal", "Manufacturing", "Marketing", "Product Management",
    "Project Management", "Public Relations", "Research", "Sales",
    "Strategy/Planning", "Training", "Consulting", "Writing/Editing",
    "Art/Creative"
]

VALID_INDUSTRIES = [
    "Accommodation and Food Services", "Administrative and Support Services",
    "Construction", "Consumer Services", "Education", "Entertainment Providers",
    "Farming, Ranching, Forestry", "Financial Services", "Government Administration",
    "Holding Companies", "Hospitals and Health Care", "Manufacturing",
    "Oil, Gas, and Mining", "Professional Services",
    "Real Estate and Equipment Rental Services", "Retail",
    "Technology, Information and Media",
    "Transportation, Logistics, Supply Chain and Storage", "Utilities",
    "Wholesale", "Research Services", "Investment Management",
    "Strategic Management Services", "Information Services", "Higher Education",
    "Primary and Secondary Education", "Medical Practices",
    "Translation and Localization"
]

def clean_category_list(items, valid_list):
    """Validates items against valid_list (exact match). Falls back to keyword overlap if < 3 match."""
    if not isinstance(items, list): return []
    cleaned = []
    for i in items:
        i_str = str(i).strip().lower()
        for v in valid_list:
            if v.lower() == i_str:
                if v not in cleaned:
                    cleaned.append(v)
                break
    
    # Failsafe: fill remaining slots via keyword-overlap scoring
    if len(cleaned) < 3:
        scored = []
        items_combined = " ".join(str(i).lower() for i in items)
        for v in valid_list:
            if v in cleaned:
                continue
            keywords = re.split(r'[\s,/&]+', v.lower())
            score = sum(1 for k in keywords if k and k in items_combined)
            if score > 0:
                scored.append((score, v))
        scored.sort(key=lambda x: -x[0])
        for _, v in scored:
            if v not in cleaned:
                cleaned.append(v)
            if len(cleaned) >= 3:
                break
    
    return cleaned[:3]

_SKILL_VERB_PREFIXES = (
    "using ", "leveraging ", "applying ", "developing ", "building ",
    "creating ", "managing ", "driving ", "analyzing ", "designing "
)

def clean_skills(skills: list, role: str = "") -> list:
    """Post-filter LLM skills: remove niche, verbose, or role-repeating entries."""
    role_lower = role.lower()
    cleaned = []
    for s in skills:
        s = s.strip()
        if not s:
            continue
        # Drop if more than 3 words
        if len(s.split()) > 3:
            continue
        # Drop if starts with a verb phrase
        s_lower = s.lower()
        if any(s_lower.startswith(p) for p in _SKILL_VERB_PREFIXES):
            continue
        # Drop if it's basically just the role title
        if s_lower == role_lower:
            continue
        cleaned.append(s)
    return cleaned[:5]

def normalize_commitment(commitment: str) -> str:
    if not commitment:
        return ""

    text = commitment.lower()

    # PRIORITY: extract patterns tied to hours/week
    patterns = [
        r'(\d+)\s*[-–to]+\s*(\d+)\s*(hours|hrs)',
        r'(\d+)\s*(hours|hrs)'
    ]

    # Try range first
    match = re.search(patterns[0], text)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return f"~{low}–{high} hrs/week"

    # Try single value
    match = re.search(patterns[1], text)
    if match:
        val = int(match.group(1))
        return f"~{val} hrs/week"

    return ""

def clean_experience_phrases(text: str) -> str:
    if not text:
        return text

    # Remove ONLY the "X years" phrase, not entire sentence
    text = re.sub(r'\b\d+\+?\s*(years?|yrs?)\b', '', text, flags=re.IGNORECASE)

    # Clean double spaces
    text = " ".join(text.split())

    return text.strip()

def normalize_role(role: str) -> str:
    if not role: return role
    # ONLY clean whitespace, do not truncate brackets or simplify items
    return " ".join(role.split())

def normalize_requirements(requirements: List[str]) -> List[str]:
    cleaned = []
    for r in requirements:
        if not r or not r.strip():
            continue
        r = clean_experience_phrases(r)
        if not r:
            continue
        cleaned.append(r[0].upper() + r[1:])
    return list(dict.fromkeys(cleaned))

def filter_requirements(requirements: List[str]) -> List[str]:
    filtered = []
    # Using regex word boundaries to prevent 'us' from matching 'business' or 'focus'
    blocked_pattern = re.compile(r'\b(us|uk|canada|europe|western|h1-b|h1b|visa|opt|citizenship)\b', re.IGNORECASE)

    for r in requirements:
        if blocked_pattern.search(r):
            continue
        filtered.append(r)
        
    if len(filtered) < 2:
        fallback = "Candidates should have strong relevant experience in the domain."
        if fallback not in filtered:
            filtered.append(fallback)
            
    return filtered

def filter_responsibilities(responsibilities: List[str]) -> List[str]:  
    filtered = []
    blocked_patterns = ["based in", "located in", "native to"]
    for r in responsibilities:
        r_lower = r.lower()
        if any(p in r_lower for p in blocked_patterns):
            continue
        filtered.append(r)
    return filtered

def normalize_text_block(text: str) -> str:
    if not text: return text
    text = text.strip()
    text = text.replace("///", "/")
    text = text.replace("//", "/")
    text = " ".join(text.split()) # collapse multiple spaces
    if text:
        text = text[0].upper() + text[1:]
    return text

def format_bullet(text: str) -> str:
    if not text: return text
    text = text.strip()
    return text[0].upper() + text[1:] if len(text) > 0 else text

def normalize_compensation(pay: str) -> str:
    if not pay:
        return pay

    pay = pay.strip()
    match = re.match(r'\$0\s*-\s*\$?(\d+)', pay)

    if match:
        max_val = match.group(1)
        if "hour" in pay.lower():
            return f"Upto ${max_val} per hour"
        elif "month" in pay.lower():
            return f"Upto ${max_val} per month"
        else:
            return f"Upto ${max_val}"

    return pay

def normalize_data(data: dict) -> dict:
    data["client"] = normalize_client(data.get("client", ""))
    data["client_desc"] = CLIENT_DESCRIPTIONS.get(data["client"], "")

    data["pay"] = normalize_compensation(data.get("pay", ""))
    data["commitment"] = normalize_commitment(data.get("commitment", ""))
    data["role"] = normalize_role(data.get("role", ""))
    
    reqs = normalize_requirements(data.get("requirements", []))
    data["requirements"] = filter_requirements(reqs)
    
    who_for = clean_experience_phrases(data.get("who_this_is_for", ""))
    data["who_this_is_for"] = normalize_text_block(who_for)

    if len(data["who_this_is_for"].split()) < 10:
        data["who_this_is_for"] = "Professionals with strong experience in content editing, proofreading, or language-focused roles who are comfortable working with structured evaluation tasks and maintaining high-quality standards."
    
    data["role_overview"] = normalize_text_block(data.get("role_overview", ""))
    
    unique_resps = []
    for resp in data.get("role_responsibilities", []):
        r_fmt = format_bullet(resp)
        if r_fmt and r_fmt not in unique_resps:
            unique_resps.append(r_fmt)
    data["role_responsibilities"] = filter_responsibilities(unique_resps)

    # Apply text artifact cleaner
    data["requirements"] = [clean_requirement_text(clean_text_artifacts(r)) for r in data["requirements"]]
    data["role_responsibilities"] = [clean_text_artifacts(r) for r in data["role_responsibilities"]]

    # Apply safety fallbacks
    if len(data["role_responsibilities"]) < 2:
        data["role_responsibilities"] = [
            "Perform tasks relevant to the role with high accuracy",
            "Follow guidelines to ensure consistent output quality"
        ]

    if len(data["requirements"]) < 2:
        data["requirements"] = [
            "Candidates should have strong relevant experience in the domain.",
            "Strong communication and analytical skills"
        ]

    data["role_responsibilities"] = [r for r in data["role_responsibilities"] if r and r.strip()]
    data["requirements"] = [r for r in data["requirements"] if r and r.strip()]

    return data


def is_remote_role(data: dict) -> bool:
    text_blob = " ".join([
        data.get("location", ""),
        data.get("role_overview", ""),
        data.get("who_this_is_for", "")
    ]).lower()
    return "remote" in text_blob

def is_geography_sentence(sentence: str) -> bool:
    patterns = [
        r'(?i)\bbased in\b',
        r'(?i)\blocated in\b',
        r'(?i)\bnative to\b',
        r'(?i)\bmust be in\b',
        r'(?i)\bonly candidates from\b'
    ]
    return any(re.search(p, sentence) for p in patterns)

def clean_text_artifacts(text: str) -> str:
    if not text: return text
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r',\s+', ', ', text)
    return text.strip()

def clean_requirement_text(text: str) -> str:
    if not text:
        return ""
    prefixes = [
        "candidates should ",
        "candidates must ",
        "the candidate should ",
        "the candidate must ",
        "you should ",
        "you must "
    ]
    t = str(text).strip()
    lower = t.lower()
    for p in prefixes:
        if lower.startswith(p):
            t = t[len(p):].strip()
            break
            
    if t:
        t = t[0].upper() + t[1:]
    return t

def remove_inline_geography(text: str) -> str:
    if not text:
        return text

    geo_terms = [
        "us", "uk", "canada", "spain", "mexico", "chile",
        "europe", "western", "germany", "france"
    ]

    words = text.split()
    cleaned_words = []

    for w in words:
        word_clean = w.lower().strip(",.")
        if word_clean in geo_terms:
            continue
        cleaned_words.append(w)

    return " ".join(cleaned_words)

def remove_geography_sentences(text: str) -> str:
    if not text:
        return text

    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned = []

    for sentence in sentences:
        if is_geography_sentence(sentence):
            continue
        cleaned.append(sentence.strip())

    result = " ".join(cleaned).strip()

    # Clean artifacts
    result = re.sub(r'\s+,', ',', result)
    result = re.sub(r',\s*,', ',', result)
    result = re.sub(r'\s+', ' ', result)

    return result

def get_fallback_titles(role: str) -> List[str]:
    return [
        f"{role} (Research & Reporting)",
        "Content Analyst (Media & Insights)",
        "Reporting Specialist (Analysis & Review)",
        "Media Reviewer (Content & Accuracy)",
        "Editorial Analyst (Research & Quality)"
    ]

def clean_titles(titles: List[str], role: str) -> List[str]:
    cleaned = []
    role_lower = role.lower()

    for t in titles:
        t_lower = t.lower()

        if len(t.split()) > 10:
            continue

        if any(bad in t_lower for bad in ["expert", "generalist"]):
            continue

        # Remove AI titles if not in role
        if "ai" in t_lower and "ai" not in role_lower:
            continue

        # Keep titles that are semantically relevant OR contain strong keywords
        if any(k in t_lower for k in ["review", "annotat", "quality", "data", "analysis"]) \
           or any(word in t_lower for word in role_lower.split()):
            if t not in cleaned:
                cleaned.append(t)
        else:
            if t not in cleaned:
                cleaned.append(t)

    if len(cleaned) < 3:
        cleaned = get_fallback_titles(role)

    return cleaned[:5]


def extract_raw_role(raw_jd: str) -> str:
    for line in raw_jd.split('\n'):
        line = line.strip()
        if line:
            return line
    return ""

def extract_pay_info(pay_str: str):
    if not pay_str:
        return 0.0, "", ""
    
    pay_str_lower = str(pay_str).lower()
    unit = ""
    if "hour" in pay_str_lower or "/hr" in pay_str_lower:
        unit = "/hr"
    elif "month" in pay_str_lower or "/mo" in pay_str_lower:
        unit = "/month"
    elif "year" in pay_str_lower or "annu" in pay_str_lower or "/yr" in pay_str_lower:
        unit = "/year"
    elif "week" in pay_str_lower or "/wk" in pay_str_lower:
        unit = "/week"
        
    matches = re.findall(r'\d+(?:\.\d+)?(?:[kKmM])?', str(pay_str).replace(',', ''))
    max_numeric = 0.0
    formatted_max = ""
    for m in matches:
        num_str = m.upper().replace('K', '').replace('M', '')
        try:
            val = float(num_str)
            numeric_val = val
            if 'K' in m.upper(): numeric_val *= 1000
            if 'M' in m.upper(): numeric_val *= 1000000
            
            if numeric_val > max_numeric:
                max_numeric = numeric_val
                if 'K' in m.upper():
                    formatted_max = str(int(val)) + "K" if val.is_integer() else str(val) + "K"
                elif 'M' in m.upper():
                    formatted_max = str(int(val)) + "M" if val.is_integer() else str(val) + "M"
                else:
                    formatted_max = str(int(val)) if val.is_integer() else str(val)
        except:
            pass
            
    return max_numeric, formatted_max, unit

def generate_subject(role: str, formatted_max: str, unit: str, is_remote: bool, client_name: str) -> str:
    client_display = "Micro1" if client_name.lower() == "micro1" else "Mercor"
    middle_parts = []
    if formatted_max:
        middle_parts.append(f"${formatted_max}{unit}")
    if is_remote:
        middle_parts.append("Remote")
    middle = " ".join(middle_parts)
    if middle:
        return f"{role} | {middle} | {client_display} x AI Labs"
    return f"{role} | {client_display} x AI Labs"

def generate_linkedin_title(role: str, numeric_max: float, formatted_max: str, unit: str, is_remote: bool) -> str:
    middle_parts = []
    if numeric_max > 0 and numeric_max <= 100:
        middle_parts.append(f"${formatted_max}{unit}")
    if is_remote:
        middle_parts.append("Remote")
    middle = " ".join(middle_parts)
    if middle:
        return f"{role} | {middle}"
    return role


def validate_schema(data: dict) -> Tuple[bool, Any]:
    required_keys = [
        "role", "type", "pay", "location", "commitment", 
        "role_responsibilities", "requirements", "role_overview", 
        "who_this_is_for", "client", "client_desc", "link", "suggested_titles"
    ]
    for k in required_keys:
        if k not in data:
            return False, f"Missing key: {k}"

    if not isinstance(data["role_responsibilities"], list): return False, "role_responsibilities must be a list"
    if not isinstance(data["requirements"], list): return False, "requirements must be a list"

    string_keys = ["role", "type", "pay", "location", "commitment", "role_overview", "who_this_is_for", "client", "client_desc", "link"]
    for k in string_keys:
        if not isinstance(data[k], str):
            return False, f"{k} must be a string"

    if not isinstance(data.get("suggested_titles"), list):
        return False, "suggested_titles must be a list"

    return True, data


# 4. Templates
def render_jd(data: dict) -> str:
    responsibilities = "\n".join([f"<li>{r}</li>" for r in data["role_responsibilities"] if r and r.strip()])
    requirements = "\n".join([f"<li>{r}</li>" for r in data["requirements"] if r and r.strip()])

    commitment = data.get("commitment", "").strip()
    commitment_line = f"<b>Commitment:</b> {commitment}<br>\n" if commitment else ""
    client_name = data.get("client", "").strip().lower()

    if client_name == "micro1":
        pay_line = f"<b>Compensation:</b> {data['pay']}<br>\n" if data.get('pay') else ""
        app_process = """<b>Application Process</b><br>
<ul>
<li>Easy Apply on LinkedIn</li>
<li>Check email for next steps</li>
<li>Participate in resume evaluation & interview stage</li>
</ul>"""
    else:
        pay_line = f"<b>Compensation:</b> {data.get('pay', '')}<br>\n"
        app_process = """<b>Application Process</b><br>
<ul>
<li>Upload resume</li>
<li>Interview</li>
<li>Submit form</li>
</ul>"""

    jd_text = f"""<b>Position:</b> {data['role']}<br>
<b>Type:</b> {data['type']}<br>
{pay_line}<b>Location:</b> {data['location']}<br>
{commitment_line}
<br>

<b>Role Responsibilities</b>
<ul>
{responsibilities}
</ul>

<b>Requirements</b>
<ul>
{requirements}
</ul>

<br>

{app_process}

<br>

#LI-CH"""
    return jd_text.strip()

def render_email(data: dict) -> str:
    client_name = data.get("client", "").strip().lower()

    if client_name == "micro1":
        boost_section = """<li>
You may also explore additional opportunities with <a href="https://refer.micro1.ai/referral/jobs?referralCode=463495f6-7cc6-49ed-8e8f-5ef2a1cc3fd7&utm_source=referral&utm_medium=share&utm_campaign=job_referral">Micro1</a>.
</li>
<li>
For regular updates, you can follow our <a href="https://whatsapp.com/channel/0029Vb6eLrf23n3gz313El2h">WhatsApp channel</a> for upcoming openings.
</li>"""
        support_email = "support@micro1.ai"
        pay_line = f"<b>Compensation:</b> {data['pay']}<br>\n" if data.get('pay') else ""
        referral_partner = ""
        app_process = """<b>Application process:</b><br>
<ul>
<li>Check email for next steps</li>
<li>Participate in resume evaluation & interview stage</li>
</ul><br>"""
    else:
        boost_items = []
        boost_items.append("""<li>
Need tips to improve your chances of selection? Check out the 
<a href="https://docs.google.com/document/d/1xYe9X4t2Bv6BEScXwwvix35Kmlc92xiulEpBDLcCZb8/edit?usp=sharing">
Interview Preparation Playbook
</a>
</li>""")
        boost_items.append("""<li>
You can strengthen your profile through the 
<a href="https://work.mercor.com/home?tab=assessments&referralCode=c88e7e37-c849-4793-a401-f58c8615e4c7">
Assessment tab
</a> in your dashboard. Completing skill based assessments can help unlock future opportunities, including roles you have not applied to or roles that may not be publicly listed.
</li>""")
        boost_items.append("""<li>
You may also explore additional opportunities with 
<a href="https://t.mercor.com/cU1Py">Mercor</a> and 
<a href="https://refer.micro1.ai/referral/jobs?referralCode=463495f6-7cc6-49ed-8e8f-5ef2a1cc3fd7&utm_source=referral&utm_medium=share&utm_campaign=job_referral">Micro1</a>, both platforms connecting skilled professionals to AI training projects.
</li>""")
        boost_items.append("""<li>
For regular updates, you can follow our 
<a href="https://whatsapp.com/channel/0029Vb6eLrf23n3gz313El2h">WhatsApp channel</a> for upcoming openings.
</li>""")
        boost_section = "\n\n".join(boost_items)
        support_email = "support@mercor.com"
        pay_line = f"<b>Compensation:</b> {data.get('pay', '')}<br>\n"
        referral_partner = f"<b>Referral Partner:</b> Crossing Hurdles<br>\n"
        app_process = """<b>Application process:</b> (~20 Min)<br>
<ul>
<li>Upload resume</li>
<li>Interview</li>
<li>Submit form</li>
</ul><br>"""

    pay_display = f" – {data['pay']}" if data.get('pay') else ""
    apply_line = f"""<b>Apply asap (reviewed on a rolling basis):</b><br>
<a href="{data['link']}">{data['role']}</a>{pay_display}<br><br>"""

    return f"""I’m from Crossing Hurdles, a global recruitment firm. We would like to refer you for an interesting opportunity that involves leveraging your expertise to train AI models.<br><br>

<b>Organization:</b> {data['client']}<br>
{referral_partner}<b>Role:</b> {data['role']}<br>
<b>Type:</b> {data['type']}<br>
{pay_line}<b>Location:</b> {data['location']}<br>
<b>Apply Here:</b> <a href="{data['link']}">{data['role']}</a><br><br>

<b>About {data['client']}:</b><br>
{data['client_desc']}<br><br>

<b>Role Overview:</b><br>
{data['role_overview']}<br><br>

<b>Who This Is For:</b><br>
{data['who_this_is_for']}<br><br>

{app_process}
{apply_line}
<b>Take Steps to Boost Your Profile:</b>
<ul>
{boost_section}
</ul>

<br>

<i>
P.S. We’re committed to addressing your queries, though responses may take longer than usual. Meanwhile, for immediate assistance, please reach out to {support_email}
</i>""".strip()


# 5. Main wrapper
def get_valid_llm_output(raw_jd: str, url: str = None, client: str = "mercor") -> dict:
    for attempt in range(3):
        start_time = time.time()
        raw_resp = generate_llm_output(raw_jd, client_name=client)
        print(f"[LLM TIME] {time.time() - start_time:.2f}s")
        
        try:
            clean_text = raw_resp.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.startswith("```"): clean_text = clean_text[3:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"[!] Invalid JSON on attempt {attempt+1}")
            
            if attempt == 2:
                fallback_titles = get_fallback_titles("Role")
                fallback_data = {
                    "role": "Role not parsed",
                    "type": "",
                    "pay": "",
                    "location": "Remote",
                    "commitment": "",
                    "role_responsibilities": [
                        "Unable to extract responsibilities from input",
                        "Please review the original job description"
                    ],
                    "requirements": [
                        "Candidates should have strong relevant experience in the domain.",
                        "Strong communication and analytical skills"
                    ],
                    "role_overview": "Unable to generate overview due to parsing failure.",
                    "who_this_is_for": "Unable to determine target candidate profile.",
                    "client": client.capitalize(),
                    "client_desc": CLIENT_DESCRIPTIONS.get(client.capitalize(), ""),
                    "link": url if url else "",
                    "suggested_titles": fallback_titles,
                    "subject": "",
                    "linkedin_title": "",
                    "skills": []
                }
        
                jd_output = render_jd(fallback_data)
                email_output = render_email(fallback_data)

                print("Final role:", fallback_data["role"])
                print("Subject:", fallback_data["subject"])
                print("LinkedIn:", fallback_data["linkedin_title"])
        
                return {
                    "jd": jd_output,
                    "email": email_output,
                    "subject": fallback_data["subject"],
                    "linkedin_title": fallback_data["linkedin_title"],
                    "skills": fallback_data["skills"],
                    "job_functions": [],
                    "industries": [],
                    "version": "v2",
                    "titles": fallback_titles,
                    "structured_data": fallback_data
                }
        
            continue

        # NORMALIZE BEFORE VALIDATION
        raw_role = extract_raw_role(raw_jd)
        if raw_role:
            data["role"] = raw_role
            
        data = normalize_data(data)
        
        # VALIDATE STRICTLY ON STRUCTURE ONLY
        is_valid, msg_or_data = validate_schema(data)
        if is_valid:
            result = msg_or_data
            
            # Policy Enforcement Separately
            is_remote = is_remote_role(result)
            if is_remote:
                result["location"] = "Remote"
                result["role_overview"] = remove_geography_sentences(result.get("role_overview", ""))
                result["who_this_is_for"] = remove_geography_sentences(result.get("who_this_is_for", ""))
                
                result["role_overview"] = remove_inline_geography(result.get("role_overview", ""))
                result["who_this_is_for"] = remove_inline_geography(result.get("who_this_is_for", ""))

            result["suggested_titles"] = clean_titles(result.get("suggested_titles", []), result.get("role", ""))

            # Client overrides
            if not result.get("client_desc"):
                result["client_desc"] = CLIENT_DESCRIPTIONS.get(result.get("client", ""), "")
                
            if result.get("client") == "Mercor":
                result["client_email"] = "support@mercor.com"
            elif result.get("client") == "Micro1":
                result["client_email"] = "support@micro1.ai"
            else:
                result["client_email"] = "support@mercor.com"

            assert isinstance(result["role_responsibilities"], list)
            assert isinstance(result["requirements"], list)
            assert len(result["role_responsibilities"]) >= 2
            assert len(result["requirements"]) >= 2

            assert result["client"] in ["Mercor", "Micro1"], f"Unexpected client: {result['client']}"

            if url:
                result["link"] = url

            jd_output = render_jd(result)
            email_output = render_email(result)

            subject = result.get("subject", "")
            linkedin_title = result.get("linkedin_title", "")
            
            # Ensure skills is a valid array of strings, post-filter niche/verbose entries
            skills = result.get("skills", [])
            if not isinstance(skills, list):
                skills = []
            skills = clean_skills([str(s).strip() for s in skills if str(s).strip()], result.get("role", ""))
            
            # Generate strict subject and linkedin_title based on verified raw data
            max_numeric, formatted_max, unit = extract_pay_info(result.get("pay", ""))
            subject = generate_subject(result["role"], formatted_max, unit, is_remote, result["client"])
            linkedin_title = generate_linkedin_title(result["role"], max_numeric, formatted_max, unit, is_remote)
            
            job_functions = clean_category_list(result.get("job_functions", []), VALID_JOB_FUNCTIONS)
            industries = clean_category_list(result.get("industries", []), VALID_INDUSTRIES)

            print("Final role:", result["role"])
            print("Subject:", subject)
            print("LinkedIn:", linkedin_title)
            
            return {
                "jd": jd_output,
                "email": email_output,
                "subject": subject,
                "linkedin_title": linkedin_title,
                "skills": skills,
                "job_functions": job_functions,
                "industries": industries,
                "version": "v2",
                "titles": result["suggested_titles"],
                "structured_data": result
            }
            
        else:
            print(f"[!] Validation failed on attempt {attempt+1}: {msg_or_data}")
            
    raise ValueError("Failed to get valid JSON from LLM after 3 attempts.")


# 6. Test block
if __name__ == "__main__":
    sample_jd = """
Audio and Video Technicians
Part-time position
Remote
Recent hire 1Recent hire 2Recent hire 3
41 hired this month

$500-$1K
one-time
Mercor logo
Posted by Mercor
mercor.com




About the Role
Mercor is seeking experienced audio and video technicians to support a leading AI lab in advancing research and infrastructure for next-generation machine learning systems. This engagement focuses on diagnosing and solving real issues in your domain. It's an opportunity to contribute your expertise to cutting-edge AI research while working independently and remotely on your own schedule.

Key Responsibilities
You’ll be asked to create deliverables regarding common requests regarding your professional domain 

You’ll be asked to review peer developed deliverables to improve AI research

Ideal Qualifications
4+ years professional experience in your respective domain

Excellent written communication with strong grammar and spelling skills

More About the Opportunity
Start Date: Immediate

Duration: ~2 weeks (with the potential for project expansion)

Commitment: ~15 hours/week required

Compensation & Contract
Task Completion Pay: Payment is based on a task completion and task quality (~$500 - $1000 per completed task, subject to change as the project evolves)

Performance Bonus: Top performers receive a weekly bonus incentive on top of their per task rate!

We consider all qualified applicants without regard to legally protected characteristics and provide reasonable accommodations upon request.
link - https://work.mercor.com/explore?listingId=list_AAABnSLJvfVX3RBDlENFN7tC
    """
    
    print("--- Running Test ---")
    try:
        res = get_valid_llm_output(sample_jd, client="mercor")
        
        print("\n=== EXTRACTED STRUCTURED DATA (JSON) ===")
        print(json.dumps(res["structured_data"], indent=2))
        
        print("\n=== RENDERED JD ===")
        print(res["jd"])
        
        print("\n=== RENDERED EMAIL ===")
        print(res["email"])
        
        print("\n=== SUGGESTED TITLES ===")
        print(json.dumps(res["titles"], indent=2))
        
    except Exception as e:
        print(f"Error during test: {e}")
