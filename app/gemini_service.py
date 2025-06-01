import google.generativeai as genai
import re
import json
import os
import cachetools

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.cache = cachetools.TTLCache(maxsize=1000, ttl=int(os.getenv("CACHE_TTL", 300)))
    
    def extract_criteria(self, user_input: str) -> dict:
        """Extract search criteria with caching"""
        cache_key = f"criteria_{user_input.lower().strip()}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            prompt = f"""
            Extract influencer search criteria from: "{user_input}"
            Return ONLY JSON with these possible fields:
            {{
                "category": "string",
                "content_type": "string",
                "platform": "string",
                "min_followers": integer,
                "max_followers": integer,
                "min_engagement": float,
                "max_budget": float,
                "age_range": [min, max],
                "gender": "string"
            }}
            
            Special conversions:
            - "gen z" → [18, 25]
            - "millennial" → [26, 40]
            - "teen" → [13, 19]
            - "affordable" → max_budget: 7000
            - "premium" → max_budget: 20000
            
            Only include explicitly mentioned or strongly implied fields.
            """
            
            response = self.model.generate_content(prompt)
            json_str = response.text.strip()
            json_str = re.sub(r'```json|```', '', json_str).strip()
            
            criteria = json.loads(json_str) if json_str and json_str != "{}" else {}
            
            # Cache result
            self.cache[cache_key] = criteria
            return criteria
        except Exception as e:
            print(f"Gemini error: {e}")
            return {}
