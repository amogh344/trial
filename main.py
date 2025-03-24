from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from textblob import TextBlob
import google.generativeai as genai

app = FastAPI()

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API Key Configuration
GEMINI_API_KEY = "AIzaSyBcGaYYOXMrr1Re91nrI-0K-aY5CB4v6UU"
genai.configure(api_key=GEMINI_API_KEY)

# Pydantic Model for Post
class UserPost(BaseModel):
    emotion: str
    content: str
    session_id: str | None = None

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
async def create_post(post: UserPost):
    try:
        content = post.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        # Sentiment analysis
        polarity = TextBlob(content).sentiment.polarity
        sentiment = "positive" if polarity > 0.3 else "neutral or negative"

        # Generate Gemini Response
        prompt = f"""
        The user feels "{post.emotion}" and shared: "{content}"
        Sentiment analysis result: {sentiment}.
        Suggest three helpful, thoughtful activities based on their mood.
        """
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        suggestions_text = response.text.strip() if response.text else "No suggestions generated."
        suggestions_list = [s.strip('- ') for s in suggestions_text.split('\n') if s.strip()]

        return JSONResponse(content={
            "ai_response": suggestions_text,
            "similar_posts": [],  # Future: connect DB here
            "suggestions": suggestions_list,
            "session_id": post.session_id or "session_" + post.emotion
        })
    except Exception as e:
        print(f"Backend Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions.")