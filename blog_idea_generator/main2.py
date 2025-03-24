from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Emotional Support Companion")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
# AI_API_URL = os.getenv("AI_API_URL", "https://chat.ivislabs.in/api")
AI_API_URL = os.getenv("AI_API_URL", "https://openwebui.com/m/swatibhalla5/luna")   
AI_API_KEY = os.getenv("AI_API_KEY", "sk-your-key-here")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma2:2b")

# In-memory storage (replace with database in production)
posts_db = []
sessions_db = {}

class PostRequest(BaseModel):
    content: str
    emotion: str = "neutral"
    session_id: str = None

class PostResponse(BaseModel):
    post_id: str
    session_id: str
    ai_response: str
    similar_posts: list
    suggestions: list

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index2.html", {"request": request})

@app.get("/share", response_class=HTMLResponse)
async def share_page(request: Request):
    return templates.TemplateResponse("share.html", {"request": request})

@app.get("/community", response_class=HTMLResponse)
async def community_page(request: Request):
    return templates.TemplateResponse("community.html", {"request": request})

@app.post("/api/posts")
async def create_post(post: PostRequest):
    try:
        # Validate or create session
        if not post.session_id or post.session_id not in sessions_db:
            post.session_id = str(uuid.uuid4())
            sessions_db[post.session_id] = {
                "created_at": datetime.now().isoformat(),
                "post_count": 0
            }
        
        # Create new post
        new_post = {
            "post_id": str(uuid.uuid4()),
            "session_id": post.session_id,
            "content": post.content,
            "emotion": post.emotion,
            "timestamp": datetime.now().isoformat(),
            "upvotes": 0
        }
        
        # Store post
        posts_db.append(new_post)
        sessions_db[post.session_id]["post_count"] += 1
        
        # Generate AI response
        ai_response = await generate_ai_response(post.content, post.emotion)
        
        # Find similar posts (excluding current session)
        similar_posts = [
            p for p in posts_db 
            if p["session_id"] != post.session_id 
            and p["emotion"] == post.emotion
        ][:3]
        
        # Generate suggestions
        suggestions = get_suggestions(post.emotion)
        
        return PostResponse(
            post_id=new_post["post_id"],
            session_id=post.session_id,
            ai_response=ai_response,
            similar_posts=similar_posts,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_ai_response(content: str, emotion: str) -> str:
    try:
        prompt = f"""The user is sharing a {emotion} experience:
        "{content}"
        
        Please respond with:
        1. Emotional validation (1 sentence)
        2. Supportive comment (1-2 sentences)
        3. A thoughtful question or reflection
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_API_URL}/chat/completions",
                headers={"Authorization": f"Bearer {AI_API_KEY}"},
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            
    except Exception:
        return "Thank you for sharing. Your feelings are important."

def get_suggestions(emotion: str) -> list:
    suggestions = {
        "happy": [
            "Consider journaling about this positive experience",
            "Share this joy with someone important to you"
        ],
        "sad": [
            "Try the 5-4-3-2-1 grounding technique",
            "A short walk might help clear your mind"
        ],
        "angry": [
            "Try deep breathing for 60 seconds",
            "Write down your thoughts to process them"
        ]
    }
    return suggestions.get(emotion, [
        "Take a moment to reflect on this experience",
        "Consider discussing this with someone you trust"
    ])

@app.get("/api/posts")
async def get_posts(emotion: str = None, limit: int = 10):
    try:
        posts = posts_db.copy()
        if emotion:
            posts = [p for p in posts if p["emotion"] == emotion]
        
        # Sort by upvotes and recent first
        posts.sort(key=lambda x: (-x["upvotes"], x["timestamp"]), reverse=True)
        
        # Anonymize before returning
        for post in posts:
            post.pop("session_id", None)
        
        return posts[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/posts/{post_id}/upvote")
async def upvote_post(post_id: str):
    try:
        for post in posts_db:
            if post["post_id"] == post_id:
                post["upvotes"] += 1
                return {"upvotes": post["upvotes"]}
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)