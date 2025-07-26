# OpenScholar - Immediate Action Plan

## 🚨 **URGENT FIXES (Apply Today)**

### 1. **Security: Fix CORS in Production**

Edit `app/main.py` around line 47:

```python
# BEFORE (Insecure):
allow_origins=["*"] if os.getenv("RENDER") else allowed_origins

# AFTER (Secure):
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://yourdomain.com",  # Add your actual domain
    "https://openscholar-nsc1.onrender.com"  # Your current Render domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Remove the conditional "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### 2. **Add Input Validation to Search**

Edit `app/main.py` search endpoint:

```python
@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_papers(request: SearchRequest):
    global search_service
    
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    try:
        # ADD THIS: Input validation
        if not request.query or len(request.query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        if len(request.query) > 500:
            raise HTTPException(status_code=400, detail="Query too long (max 500 characters)")
        
        # Validate year range
        if request.year_start and request.year_end:
            if request.year_start > request.year_end:
                raise HTTPException(status_code=400, detail="Start year cannot be greater than end year")
        
        # Rest of your existing code...
```

### 3. **Add Frontend Error Boundary**

Create `frontend/src/components/ErrorBoundary.tsx`:

```typescript
import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-gray-800">
                  Something went wrong
                </h3>
                <div className="mt-2 text-sm text-gray-500">
                  <p>Please refresh the page and try again.</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => window.location.reload()}
                    className="text-sm bg-red-100 text-red-800 rounded-md px-2 py-1 hover:bg-red-200"
                  >
                    Refresh Page
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

Then wrap your app in `frontend/src/App.tsx`:

```typescript
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      {/* Your existing app content */}
    </ErrorBoundary>
  );
}
```

## 🔧 **QUICK PERFORMANCE FIXES**

### 1. **Add Simple Caching**

Create `app/utils/cache.py`:

```python
from typing import Dict, Any, Optional
import time
import hashlib
import json

class SimpleCache:
    """Simple in-memory cache for search results"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, search_request) -> str:
        """Generate cache key from search request"""
        key_data = {
            "query": search_request.query,
            "year_start": search_request.year_start,
            "year_end": search_request.year_end,
            "discipline": search_request.discipline,
            "education_level": search_request.education_level
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, search_request) -> Optional[Any]:
        """Get cached result if valid"""
        key = self._generate_key(search_request)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, search_request, result: Any):
        """Cache the result"""
        key = self._generate_key(search_request)
        self.cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()

# Global cache instance
search_cache = SimpleCache()
```

### 2. **Add to Search Service**

In `app/services/search.py`:

```python
from app.utils.cache import search_cache

async def search(self, request: SearchRequest) -> Tuple[List[Paper], List[str]]:
    # Check cache first
    cached_result = search_cache.get(request)
    if cached_result:
        logger.info("Returning cached search results")
        return cached_result
    
    # Your existing search logic...
    
    # Cache the results before returning
    result = (sorted_papers, sources_queried)
    search_cache.set(request, result)
    
    return result
```

## 🎯 **APPLY THESE FIXES**

1. **Run the quick fixes script:**
   ```bash
   chmod +x quick_fixes.sh
   ./quick_fixes.sh
   ```

2. **Apply the security fixes above**

3. **Add the error boundary to your frontend**

4. **Test everything:**
   ```bash
   python test_imports.py
   ```

5. **Restart your servers and test searches**

These fixes will immediately improve security and stability! 🚀

## 📚 **Next Steps**

After applying these urgent fixes:
1. Review the full audit report for comprehensive improvements
2. Consider implementing user authentication
3. Add proper database backend
4. Set up monitoring and error tracking

Your OpenScholar platform has excellent potential - these fixes will make it production-ready! 💪
