import pandas as pd
import os
import re
from typing import Dict, Any, Tuple

class InfluencerUtils:
    def __init__(self):
        self.df = self.load_data()
        self.platform_map = {
            'instagram': 'ig', 'youtube': 'yt', 'facebook': 'fb', 'tiktok': 'tiktok',
            'ig': 'ig', 'insta': 'ig', 'yt': 'yt', 'fb': 'fb'
        }
        self.category_map = {
            'fitness': 'fitness', 'fit': 'fitness', 'workout': 'fitness',
            'gym': 'fitness', 'exercise': 'fitness',
            'tech': 'tech', 'technology': 'tech', 'gadgets': 'tech',
            'fashion': 'fashion', 'style': 'fashion', 'clothing': 'fashion',
            'food': 'food', 'cooking': 'food', 'cuisine': 'food', 'recipe': 'food',
            'travel': 'travel', 'tourism': 'travel', 'adventure': 'travel'
        }
    
    def load_data(self) -> pd.DataFrame:
        """Load and clean influencer data"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, "mock_influencers_100_inr.csv")
            df = pd.read_csv(csv_path)
            
            # Clean data
            str_cols = ['category', 'content_type', 'platform', 'gender', 'email', 'phone_number']
            for col in str_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.lower().str.strip()
            
            print(f"Loaded {len(df)} influencer records")
            return df
        except Exception as e:
            print(f"Data loading error: {e}")
            return pd.DataFrame()
    
    def manual_criteria_parsing(self, user_input: str) -> Dict[str, Any]:
        """Manual parsing for critical fields"""
        criteria = {}
        user_input = user_input.lower()
        
        # Gender detection
        gender_keywords = {
            'female': ['female', 'woman', 'women', 'girl', 'she', 'her'],
            'male': ['male', 'man', 'men', 'boy', 'he', 'him']
        }
        for gender, keywords in gender_keywords.items():
            if any(kw in user_input for kw in keywords):
                criteria['gender'] = gender
                break
        
        # Age extraction
        age_pattern = r'under (\d+)|over (\d+)|(\d+)\s*-\s*(\d+)|(\d+)\s*to\s*(\d+)|below (\d+)|above (\d+)'
        age_match = re.search(age_pattern, user_input)
        if age_match:
            if age_match.group(1):  # under X
                criteria['age_range'] = [18, int(age_match.group(1))]
            elif age_match.group(2):  # over X
                criteria['age_range'] = [int(age_match.group(2)), 65]
            elif age_match.group(3) and age_match.group(4):  # X-Y
                criteria['age_range'] = [int(age_match.group(3)), int(age_match.group(4))]
            elif age_match.group(5) and age_match.group(6):  # X to Y
                criteria['age_range'] = [int(age_match.group(5)), int(age_match.group(6))]
            elif age_match.group(7):  # below X
                criteria['age_range'] = [18, int(age_match.group(7))]
            elif age_match.group(8):  # above X
                criteria['age_range'] = [int(age_match.group(8)), 65]
        
        # Platform mapping
        for platform, code in self.platform_map.items():
            if platform in user_input:
                criteria['platform'] = code
                break
        
        # Category mapping
        for keyword, category in self.category_map.items():
            if keyword in user_input:
                criteria['category'] = category
                break
        
        return criteria
    
    def search(self, criteria: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        """Search influencers with criteria"""
        if self.df.empty:
            return pd.DataFrame(), "Data not loaded"
        
        results = self.df.copy()
        applied_filters = []
        
        # Apply filters
        if 'category' in criteria:
            results = results[results['category'] == criteria['category']]
            applied_filters.append(f"category: {criteria['category']}")
            
        if 'platform' in criteria:
            platform_code = self.platform_map.get(criteria['platform'].lower(), criteria['platform'])
            results = results[results['platform'] == platform_code]
            applied_filters.append(f"platform: {platform_code}")
            
        if 'gender' in criteria:
            results = results[results['gender'] == criteria['gender']]
            applied_filters.append(f"gender: {criteria['gender']}")
            
        if 'age_range' in criteria and len(criteria['age_range']) == 2:
            min_age, max_age = criteria['age_range']
            min_age = max(18, min_age)
            max_age = min(65, max_age)
            results = results[(results['age'] >= min_age) & (results['age'] <= max_age)]
            applied_filters.append(f"age: {min_age}-{max_age}")
            
        if 'min_followers' in criteria:
            results = results[results['total_followers'] >= int(criteria['min_followers'])]
            applied_filters.append(f"min followers: {criteria['min_followers']:,}")
            
        if 'max_followers' in criteria:
            results = results[results['total_followers'] <= int(criteria['max_followers'])]
            applied_filters.append(f"max followers: {criteria['max_followers']:,}")
            
        if 'min_engagement' in criteria:
            results = results[results['overall_engagement'] >= float(criteria['min_engagement'])]
            applied_filters.append(f"min engagement: {criteria['min_engagement']}%")
            
        if 'max_budget' in criteria:
            results = results[results['rates_for_charging_inr'] <= float(criteria['max_budget'])]
            applied_filters.append(f"max budget: ₹{criteria['max_budget']:,.2f}")
        
        # Sort by engagement then followers
        results = results.sort_values(by=['overall_engagement', 'total_followers'], ascending=False)
        
        return results, ", ".join(applied_filters) if applied_filters else "no filters"
    
    def format_results(self, results: pd.DataFrame, limit: int) -> list:
        """Format results for JSON response"""
        if results.empty:
            return []
        
        influencers = []
        for _, row in results.head(limit).iterrows():
            influencers.append({
                "name": row['influencer_name'],
                "category": row['category'],
                "content_type": row['content_type'],
                "platform": row['platform'],
                "followers": int(row['total_followers']),
                "engagement": float(row['overall_engagement']),
                "rate_inr": float(row['rates_for_charging_inr']),
                "age": int(row['age']),
                "gender": row['gender'],
                "contact": {
                    "email": row['email'],
                    "phone": row['phone_number']
                }
            })
        return influencers
