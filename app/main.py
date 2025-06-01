import os
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .influencer_utils import InfluencerUtils
from .gemini_service import GeminiService

# Initialize logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Influencer Search API",
    description="AI-powered influencer search using natural language",
    version="1.2",
    docs_url="/docs",
    redoc_url=None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
utils = InfluencerUtils()
gemini = GeminiService()

@app.on_event("startup")
async def startup_event():
    logger.info("Influencer Search API starting up")
    logger.info(f"Loaded {len(utils.df)} influencers")
    logger.info("Service ready")

@app.get("/")
def read_root():
    return {
        "service": "Influencer Search API",
        "status": "active",
        "endpoints": {
            "POST /search": "Search influencers with natural language",
            "GET /stats": "Get dataset statistics"
        }
    }

@app.get("/stats")
def get_stats():
    if utils.df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    return {
        "total_influencers": len(utils.df),
        "gender_distribution": utils.df['gender'].value_counts().to_dict(),
        "platform_distribution": utils.df['platform'].value_counts().to_dict(),
        "category_distribution": utils.df['category'].value_counts().to_dict(),
        "follower_stats": {
            "min": int(utils.df['total_followers'].min()),
            "max": int(utils.df['total_followers'].max()),
            "mean": int(utils.df['total_followers'].mean())
        }
    }

@app.post("/search")
async def search_influencers(
    prompt: str = Query(..., description="Natural language search query"),
    limit: int = Query(5, description="Max results to return", ge=1, le=20)
):
    """
    Search influencers using natural language
    
    Example queries:
    - "Female fitness influencers on Instagram under 30"
    - "Tech YouTubers with 50k-200k followers"
    - "Affordable travel bloggers"
    """
    try:
        # Step 1: Manual parsing for critical fields
        manual_criteria = utils.manual_criteria_parsing(prompt)
        
        # Step 2: AI-based extraction
        ai_criteria = gemini.extract_criteria(prompt)
        
        # Merge criteria (manual takes precedence)
        criteria = {**ai_criteria, **manual_criteria}
        
        # Step 3: Search influencers
        results, filters_applied = utils.search(criteria)
        
        # Step 4: Format results
        influencers = utils.format_results(results, limit)
        
        return {
            "prompt": prompt,
            "interpreted_criteria": criteria,
            "filters_applied": filters_applied,
            "total_matches": len(results),
            "results_returned": len(influencers),
            "influencers": influencers
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search processing error")

@app.get("/health")
def health_check():
    return {"status": "ok", "influencers_loaded": len(utils.df)}
