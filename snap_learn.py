import json
import cohere
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader
from fpdf import FPDF
from database import get_collection
import os
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

router = APIRouter(prefix="/snaplearn")
collection = get_collection("snaplearn")

co = cohere.Client(COHERE_API_KEY)
def llm(prompt, max_tokens=1000):
    r = co.chat(
        model="command-a-vision-07-2025",
        message=prompt,
        temperature=0.3,
        max_tokens=max_tokens
    )
    t = r.text.strip()
    if not t:
        raise HTTPException(500, "AI returned empty response")
    return t




class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "SnapLearn Quick Revision Guide", ln=True, align="C")
        self.ln(4)

def clean(t):
    return t.encode("latin-1", "replace").decode("latin-1")

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    reader = PdfReader(file.file)
    text = ""
    for p in reader.pages:
        text += p.extract_text() or ""
    if len(text.strip()) < 100:
        raise HTTPException(400, "No readable text")
    chunks = [text[i:i+900] for i in range(0, len(text), 800)]
    ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=[{"doc": file.filename}] * len(chunks)
    )
    return {
        "document": file.filename,
        "total_chunks": len(chunks),
        "chunks": [{"id": ids[i], "text": chunks[i][:60] + "..."} for i in range(len(chunks))]
    }

@router.get("/accuracy-check")
async def accuracy(query: str):
    r = collection.query(query_texts=[query], n_results=3)
    return {
        "ids": r["ids"][0],
        "text_found": r["documents"][0],
        "distance": r["distances"][0]
    }

@router.get("/revise/{chunk_id}")
async def revise(chunk_id: str):
    d = collection.get(ids=[chunk_id])
    if not d["documents"]:
        raise HTTPException(404, "Chunk not found")

    context = d["documents"][0][:1400]

    prompt = f"""
You are an academic tutor.

Return STRICT JSON only.

TASKS:
1. Extract ALL key concepts from the text.
2. Explain each concept clearly for exam revision.
3. Extract formulas if present.
4. Generate EXACTLY 10 MCQs strictly from this text.

JSON FORMAT:
{{
  "key_concepts": [
    {{
      "concept": "Concept title",
      "explanation": "Detailed explanation derived ONLY from the given text"
    }}
  ],
  "formulas": ["formula1","formula2"],
  "mcqs": [
    {{
      "question": "Question text",
      "options": ["A) option","B) option","C) option","D) option"],
      "correctAnswer": "A"
    }}
  ]
}}

RULES:
- key_concepts MUST include ALL important ideas from the text
- explanation MUST be multi-sentence, not one-line
- mcqs MUST be exactly 10
- options MUST be exactly 4
- No markdown
- No extra text outside JSON

TEXT:
{context}
"""

    raw = llm(prompt, max_tokens=1800)

    try:
        parsed = json.loads(raw)
    except Exception:
        raise HTTPException(500, f"Invalid JSON from AI:\n{raw}")

    if "key_concepts" not in parsed or not parsed["key_concepts"]:
        raise HTTPException(500, "No key concepts generated")

    mcqs = parsed.get("mcqs", [])
    if len(mcqs) < 10:
        raise HTTPException(500, f"AI returned only {len(mcqs)} MCQs")

    parsed["mcqs"] = mcqs[:10]
    return {"analysis": parsed}


@router.get("/generate-quick-pdf/{doc}")
async def generate(doc: str):
    r = collection.get(where={"doc": doc})
    if not r["documents"]:
        raise HTTPException(404)

    context = " ".join(r["documents"][:5])[:2500]

    concepts = llm(f"Extract all key concepts for last minute exam revision:\n{context}")
    formulas = llm(f"Extract all formulas or symbols:\n{context}")

    mcq_raw = llm(f"""
    Return STRICT JSON only.
    Do not include explanations.
    Do not include markdown.
    Do not include trailing commas.

    Generate EXACTLY 10 MCQs.

    JSON format:
    {{
     "q":[
      {{
       "id":1,
       "q":"question text",
       "o":["A) option","B) option","C) option","D) option"],
       "a":"A"
      }}
     ]
    }}

    TEXT:
    {context}
    """, max_tokens=1500)

    try:
        mcqs = json.loads(mcq_raw)
    except json.JSONDecodeError:
        cleaned = mcq_raw.strip()
        cleaned = cleaned[cleaned.find("{"):cleaned.rfind("}") + 1]
        try:
            mcqs = json.loads(cleaned)
        except Exception:
            raise HTTPException(500, f"Invalid MCQ JSON from AI:\n{mcq_raw}")

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, clean(concepts))

    pdf.add_page()
    pdf.multi_cell(0, 8, clean(formulas))

    pdf.add_page()
    answers = []
    for q in mcqs["q"]:
        pdf.multi_cell(0, 8, f"Q{q['id']}. {q['q']}")
        for o in q["o"]:
            pdf.cell(10)
            pdf.cell(0, 8, clean(o), ln=True)
        answers.append(f"{q['id']}:{q['a']}")

    pdf.add_page()
    pdf.multi_cell(0, 8, " ".join(answers))

    name = f"SnapLearn_{doc}.pdf"
    pdf.output(name)
    return FileResponse(name, filename=name)
