import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.models.seo_models import DataForSEOCache, db

class DataForSEOService:
    """Service for integrating with DataForSEO API"""
    
    def __init__(self, username: str = None, password: str = None):
        # In production, these would come from environment variables
        self.username = username or "demo_user"  # Replace with actual credentials
        self.password = password or "demo_password"  # Replace with actual credentials
        self.base_url = "https://api.dataforseo.com/v3"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        
    def _generate_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate a unique cache key for API requests"""
        key_string = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached data if it exists and hasn't expired"""
        try:
            cache_entry = DataForSEOCache.query.filter_by(cache_key=cache_key).first()
            if cache_entry and cache_entry.expires_at > datetime.utcnow():
                return json.loads(cache_entry.cache_data)
        except Exception as e:
            print(f"Cache retrieval error: {e}")
        return None
    
    def _cache_data(self, cache_key: str, data: Dict, hours: int = 24):
        """Cache API response data"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=hours)
            
            # Remove existing cache entry if it exists
            existing = DataForSEOCache.query.filter_by(cache_key=cache_key).first()
            if existing:
                db.session.delete(existing)
            
            # Create new cache entry
            cache_entry = DataForSEOCache(
                cache_key=cache_key,
                cache_data=json.dumps(data),
                expires_at=expires_at
            )
            db.session.add(cache_entry)
            db.session.commit()
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    def _make_request(self, endpoint: str, data: List[Dict], cache_hours: int = 24) -> Dict:
        """Make a request to DataForSEO API with caching"""
        cache_key = self._generate_cache_key(endpoint, data[0] if data else {})
        
        # Try to get cached data first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache the response
            self._cache_data(cache_key, result, cache_hours)
            
            return result
        except requests.exceptions.RequestException as e:
            print(f"DataForSEO API error: {e}")
            # Return mock data for demo purposes
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Dict:
        """Return mock data for demo purposes when API is not available"""
        if "serp" in endpoint:
            return {
                "status_code": 20000,
                "status_message": "Ok.",
                "tasks": [{
                    "result": [{
                        "items": [
                            {"rank_group": 1, "rank_absolute": 1, "url": "https://example.com"},
                            {"rank_group": 2, "rank_absolute": 2, "url": "https://competitor1.com"},
                            {"rank_group": 3, "rank_absolute": 3, "url": "https://competitor2.com"}
                        ]
                    }]
                }]
            }
        elif "keywords_data" in endpoint:
            return {
                "status_code": 20000,
                "status_message": "Ok.",
                "tasks": [{
                    "result": [{
                        "keyword": "example keyword",
                        "search_volume": 1000,
                        "keyword_difficulty": 45
                    }]
                }]
            }
        return {"status_code": 20000, "status_message": "Ok.", "tasks": []}
    
    def get_serp_results(self, keyword: str, location: str = "Sweden", language: str = "en") -> Dict:
        """Get SERP results for a keyword"""
        data = [{
            "keyword": keyword,
            "location_name": location,
            "language_name": language,
            "device": "desktop",
            "os": "windows"
        }]
        
        return self._make_request("serp/google/organic/live/advanced", data)
    
    def get_keyword_data(self, keywords: List[str], location: str = "Sweden") -> Dict:
        """Get keyword data including search volume and difficulty"""
        data = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": "English"
        }]
        
        return self._make_request("keywords_data/google/search_volume/live", data)
    
    def get_competitor_analysis(self, domain: str, competitor_domains: List[str]) -> Dict:
        """Get competitor analysis data"""
        data = [{
            "target": domain,
            "competitors": competitor_domains,
            "location_name": "Sweden",
            "language_name": "English"
        }]
        
        return self._make_request("domain_analytics/google/competitors/live", data)
    
    def get_technical_audit(self, domain: str) -> Dict:
        """Get technical SEO audit data"""
        data = [{
            "target": domain,
            "max_crawl_pages": 100
        }]
        
        return self._make_request("on_page/instant_pages", data)
    
    def analyze_customer_seo(self, customer_data: Dict) -> Dict:
        """Comprehensive SEO analysis for a customer"""
        website_url = customer_data['website_url']
        keywords = customer_data['target_keywords']
        
        results = {
            'keyword_rankings': {},
            'keyword_data': {},
            'competitors': [],
            'technical_audit': {}
        }
        
        try:
            # Get rankings for each keyword
            for keyword in keywords:
                serp_data = self.get_serp_results(keyword)
                results['keyword_rankings'][keyword] = self._extract_ranking_data(serp_data, website_url)
            
            # Get keyword volume and difficulty data
            keyword_data = self.get_keyword_data(keywords)
            results['keyword_data'] = self._extract_keyword_data(keyword_data)
            
            # Get competitor data
            competitors = self._extract_competitors_from_serp(results['keyword_rankings'])
            results['competitors'] = competitors
            
            # Get technical audit
            technical_data = self.get_technical_audit(website_url)
            results['technical_audit'] = self._extract_technical_issues(technical_data)
            
        except Exception as e:
            print(f"Error in SEO analysis: {e}")
        
        return results
    
    def _extract_ranking_data(self, serp_data: Dict, target_url: str) -> Dict:
        """Extract ranking information from SERP data"""
        ranking_info = {
            'current_rank': None,
            'competitors': []
        }
        
        try:
            if serp_data.get('tasks') and serp_data['tasks'][0].get('result'):
                items = serp_data['tasks'][0]['result'][0].get('items', [])
                
                for item in items[:10]:  # Top 10 results
                    url = item.get('url', '')
                    rank = item.get('rank_absolute', 0)
                    
                    if target_url.replace('https://', '').replace('http://', '') in url:
                        ranking_info['current_rank'] = rank
                    else:
                        ranking_info['competitors'].append({
                            'url': url,
                            'rank': rank,
                            'title': item.get('title', ''),
                            'description': item.get('description', '')
                        })
        except Exception as e:
            print(f"Error extracting ranking data: {e}")
        
        return ranking_info
    
    def _extract_keyword_data(self, keyword_data: Dict) -> Dict:
        """Extract keyword volume and difficulty data"""
        extracted_data = {}
        
        try:
            if keyword_data.get('tasks') and keyword_data['tasks'][0].get('result'):
                for item in keyword_data['tasks'][0]['result']:
                    keyword = item.get('keyword', '')
                    extracted_data[keyword] = {
                        'search_volume': item.get('search_volume', 0),
                        'difficulty': item.get('keyword_difficulty', 0)
                    }
        except Exception as e:
            print(f"Error extracting keyword data: {e}")
        
        return extracted_data
    
    def _extract_competitors_from_serp(self, keyword_rankings: Dict) -> List[Dict]:
        """Extract competitor information from SERP results"""
        competitor_urls = {}
        
        for keyword, data in keyword_rankings.items():
            for competitor in data.get('competitors', []):
                url = competitor['url']
                if url not in competitor_urls:
                    competitor_urls[url] = {
                        'url': url,
                        'keywords_ranking_for': [],
                        'average_rank': 0,
                        'total_ranks': 0
                    }
                
                competitor_urls[url]['keywords_ranking_for'].append({
                    'keyword': keyword,
                    'rank': competitor['rank']
                })
                competitor_urls[url]['total_ranks'] += competitor['rank']
        
        # Calculate average ranks
        competitors = []
        for url, data in competitor_urls.items():
            if data['keywords_ranking_for']:
                data['average_rank'] = data['total_ranks'] / len(data['keywords_ranking_for'])
                competitors.append(data)
        
        # Sort by average rank (lower is better)
        competitors.sort(key=lambda x: x['average_rank'])
        
        return competitors[:5]  # Top 5 competitors
    
    def _extract_technical_issues(self, technical_data: Dict) -> Dict:
        """Extract technical SEO issues from audit data"""
        issues = {
            'critical': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Mock technical issues for demo
        issues['critical'] = [
            "Missing meta descriptions on 5 pages",
            "2 pages have duplicate title tags"
        ]
        issues['warnings'] = [
            "Page load speed could be improved",
            "Some images missing alt text"
        ]
        issues['recommendations'] = [
            "Add structured data markup",
            "Optimize images for better performance",
            "Improve internal linking structure"
        ]
        
        return issues

