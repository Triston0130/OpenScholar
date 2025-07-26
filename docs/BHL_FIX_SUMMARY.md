# BHL (Biodiversity Heritage Library) Fix Summary

## Problem
BHL wasn't working even with a configured API key.

## Root Causes Found

1. **Wrong API Operation**: The client was using `PublicationSearchAdvanced` which requires additional parameters (title, author, or collection ID). This was causing 400 Bad Request errors.

2. **Demo Key Blocking**: The client was blocking the demo API key (`00000000-0000-0000-0000-000000000000`), but this key actually works for basic searches.

3. **API Key Not Passed**: The BiodiversityClient constructor wasn't accepting an API key parameter.

## Fixes Applied

### 1. Updated API Operation
Changed from:
```python
"op": "PublicationSearchAdvanced"
```
To:
```python
"op": "PublicationSearch"
```

### 2. Updated Constructor
Changed from:
```python
def __init__(self):
    self.api_key = "00000000-0000-0000-0000-000000000000"
```
To:
```python
def __init__(self, api_key: Optional[str] = None):
    self.api_key = api_key or "00000000-0000-0000-0000-000000000000"
```

### 3. Removed Demo Key Blocking
Changed from:
```python
if not self.api_key or self.api_key == "00000000-0000-0000-0000-000000000000":
    return []
```
To:
```python
if not self.api_key:
    return []
```

### 4. Fixed Parameter Bug
Fixed the `_book_to_paper` method to accept the `query` parameter.

## Result

✅ BHL now works with:
- The demo API key (returns results)
- Your configured API key (should return more/better results)
- Proper error handling

## Testing

Run this to verify BHL is working:
```bash
python3 test_bhl_simple.py
```

Or test with your API key:
```bash
python3 test_bhl_simple.py YOUR_API_KEY_HERE
```

## API Key Notes

- The demo key (`00000000-0000-0000-0000-000000000000`) provides basic access
- A real API key from https://www.biodiversitylibrary.org/api3/docs/docs.html may provide:
  - Higher rate limits
  - Access to more operations
  - Better search results

Your configured API key through the OpenScholar UI should now work properly!