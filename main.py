import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from database import create_document, get_recent_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ----- Tone & Sentiment Workflow API -----
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="User prompt for generation")
    tone: str = Field(..., description="Tone (Professional, Playful, Formal, Casual, etc.)")
    sentiment: str = Field(..., description="Sentiment (Positive, Neutral, Urgent)")
    length: str = Field("Medium", description="Short | Medium | Long")
    creativity: float = Field(0.35, ge=0.0, le=1.0)
    variants: int = Field(1, ge=1, le=5)

class GenerateResponse(BaseModel):
    id: str
    outputs: list[str]

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(payload: GenerateRequest):
    """
    Mock generation endpoint that returns stylized content matching tone/sentiment/length.
    Persists request+result to DB as a Generation document.
    """
    # Simple heuristic generation to keep backend self-contained
    tone_voice = {
        "Professional": "Polished and concise.",
        "Playful": "Light and witty.",
        "Formal": "Respectful and structured.",
        "Casual": "Friendly and direct.",
    }.get(payload.tone, "Confident and clear.")

    sentiment_hint = {
        "Positive": "Emphasize benefits and momentum.",
        "Neutral": "Stay informative and balanced.",
        "Urgent": "Use action-forward phrasing.",
    }.get(payload.sentiment, "Stay helpful.")

    length_map = {
        "Short": (18, 26),
        "Medium": (40, 60),
        "Long": (80, 120),
    }
    min_len, max_len = length_map.get(payload.length, (40, 60))

    # Make a few variants
    outputs: list[str] = []
    base = payload.prompt.strip() or "Your product or idea"
    for i in range(payload.variants):
        guide = f"{payload.tone} • {payload.sentiment} • {payload.length}. {tone_voice} {sentiment_hint}"
        core = f"{base} — crafted with ContentForge to help you move faster."
        # very lightweight pseudo-variation using creativity
        exclaim = "!" if payload.sentiment == "Urgent" or payload.creativity > 0.6 else "."
        suffix = " Take the next step today" if payload.sentiment == "Urgent" else ""
        text = f"{core} {guide}{exclaim}{suffix}"
        # Trim/expand heuristically
        if len(text.split()) < min_len:
            text = text + " " + " ".join(["Learn more.", "Discover why.", "Built for teams.", "Effortless.", "Reliable."][: max(0, min_len - len(text.split()))])
        outputs.append(text[: max_len * 2])

    # Persist to DB
    try:
        from schemas import Generation as GenerationModel
        doc = GenerationModel(
            prompt=payload.prompt,
            tone=payload.tone,
            sentiment=payload.sentiment,
            length=payload.length,
            creativity=payload.creativity,
            variants=payload.variants,
            result="\n\n".join(outputs),
        )
        inserted_id = create_document('generation', doc)
    except Exception as e:
        # If DB is not available, still return outputs
        inserted_id = "no-db"

    return {"id": inserted_id, "outputs": outputs}

# Recent generations endpoint for Library panel
class RecentItem(BaseModel):
    id: str
    prompt: str
    created_at: Optional[str] = None

@app.get("/api/recent", response_model=list[RecentItem])
async def recent_generations(limit: int = 9):
    """Return recent generation metadata for the library preview"""
    items = []
    try:
        docs = get_recent_documents('generation', limit=limit)
        for d in docs:
            items.append({
                "id": str(d.get('_id')),
                "prompt": d.get('prompt', 'Untitled'),
                "created_at": d.get('created_at').isoformat() if d.get('created_at') else None,
            })
    except Exception:
        # Fallback mocked items if DB unavailable
        items = [
            {"id": f"mock-{i}", "prompt": p, "created_at": None}
            for i, p in enumerate([
                "Product Launch Tweet",
                "Feature Update Email",
                "SEO Blog Outline",
            ], start=1)
        ]
    return items

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
