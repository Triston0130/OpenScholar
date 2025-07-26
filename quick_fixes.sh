#!/bin/bash
# OpenScholar Quick Security & Performance Fixes
# Run this script to apply immediate improvements

echo "🔧 Applying OpenScholar Quick Fixes..."

# 1. Create a proper environment validation
cat > app/config.py << 'EOF'
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Application configuration with validation"""
    
    def __init__(self):
        self.validate_environment()
    
    @property
    def core_api_key(self) -> Optional[str]:
        return os.getenv("CORE_API_KEY")
    
    @property
    def eric_api_key(self) -> Optional[str]:
        return os.getenv("ERIC_API_KEY")
    
    @property
    def doaj_api_key(self) -> Optional[str]:
        return os.getenv("DOAJ_API_KEY")
    
    @property
    def request_timeout(self) -> int:
        return int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @property
    def max_results_per_api(self) -> int:
        return int(os.getenv("MAX_RESULTS_PER_API", "50"))
    
    @property
    def environment(self) -> str:
        return "production" if os.getenv("RENDER") else "development"
    
    def validate_environment(self):
        """Validate required environment variables"""
        if self.environment == "production":
            if not self.core_api_key:
                logger.warning("CORE_API_KEY not set - CORE searches will fail")
            
        logger.info(f"Configuration loaded for {self.environment} environment")

config = Config()
EOF

# 2. Add input validation
cat > app/utils/validation.py << 'EOF'
import re
from typing import Optional

def sanitize_search_query(query: str) -> str:
    """Sanitize search query to prevent injection"""
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    # Remove potentially harmful characters
    query = re.sub(r'[<>"\'\`\$\{\}]', '', query)
    
    # Limit length
    if len(query) > 500:
        raise ValueError("Query too long (max 500 characters)")
    
    return query.strip()

def validate_year_range(year_start: Optional[int], year_end: Optional[int]) -> tuple:
    """Validate year range"""
    current_year = 2025
    
    if year_start is None:
        year_start = 1900
    if year_end is None:
        year_end = current_year
    
    if not (1900 <= year_start <= current_year):
        raise ValueError("Start year must be between 1900 and current year")
    
    if not (1900 <= year_end <= current_year):
        raise ValueError("End year must be between 1900 and current year")
    
    if year_start > year_end:
        raise ValueError("Start year cannot be greater than end year")
    
    return year_start, year_end
EOF

# 3. Add rate limiting utility
cat > app/utils/rate_limiting.py << 'EOF'
import asyncio
import time
from typing import Dict, Optional

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self):
        self.last_calls: Dict[str, float] = {}
        self.min_intervals = {
            "semantic_scholar": 1.0,  # 1 second between calls
            "core": 0.5,              # 0.5 seconds between calls
            "doaj": 0.5,              # 0.5 seconds between calls
            "default": 0.2            # Default 200ms between calls
        }
    
    async def wait_if_needed(self, api_name: str):
        """Wait if necessary to respect rate limits"""
        interval = self.min_intervals.get(api_name, self.min_intervals["default"])
        
        if api_name in self.last_calls:
            time_since_last = time.time() - self.last_calls[api_name]
            if time_since_last < interval:
                wait_time = interval - time_since_last
                await asyncio.sleep(wait_time)
        
        self.last_calls[api_name] = time.time()

# Global rate limiter instance
rate_limiter = RateLimiter()
EOF

echo "✅ Security and performance fixes applied!"
echo ""
echo "📝 NEXT STEPS:"
echo "1. Update your main.py to use the new config system"
echo "2. Add input validation to your search endpoints"
echo "3. Update API clients to use rate limiting"
echo "4. Test the changes with: python test_imports.py"
echo ""
echo "🔍 See the full audit report for comprehensive improvements!"
