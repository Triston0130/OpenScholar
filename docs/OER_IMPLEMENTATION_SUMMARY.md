# OER (Open Educational Resources) Implementation Summary

This document summarizes the implementation of OER sources in OpenScholar.

## Overview

Successfully implemented OER sources with the following status:

### Fully Functional (No API Key Required)
1. **Open Textbook Library** ✅ - JSON API, no authentication needed
2. **LibreTexts** ✅ - Web scraping implementation

### Requires API Key (Grayed Out Without Key)
3. **MIT OpenCourseWare** 🔑 - Basic scraping works, full search requires Google API key
4. **MERLOT** 🔑 - Requires API key for access
5. **OER Commons** 🔑 - Requires API key for access
6. **Pressbooks** ❌ - SSL/connection issues

## Implementation Details

### 1. Open Textbook Library

- **Status**: Fully functional
- **Method**: JSON API
- **Endpoint**: `https://open.umn.edu/opentextbooks/textbooks.json`
- **Features**:
  - Searches across title, description, and subjects
  - Returns complete author information
  - Includes publication year, license info
  - Direct links to textbook pages

### 2. LibreTexts

- **Status**: Fully functional
- **Method**: Web scraping (no API available)
- **Implementation**: Searches across 12 discipline-specific libraries
- **Libraries covered**:
  - Biology, Chemistry, Mathematics, Physics
  - Engineering, Business, Humanities, Medicine
  - Statistics, Social Sciences, Geosciences, Workforce
- **Features**:
  - Filters results based on query relevance
  - Returns discipline-categorized results
  - Includes links to HTML, PDF, and EPUB formats

### 3. MIT OpenCourseWare

- **Status**: Requires Google API key for full functionality
- **Default Method**: Basic web scraping (limited results)
- **Enhanced Method**: Google Custom Search Engine (requires API key)
- **API Key**: Set via `MIT OpenCourseWare` in API Keys modal
- **Features**:
  - Without API key: Limited results from web scraping
  - With API key: Full-text search across all MIT OCW content
  - Includes course numbers, departments, and materials

## Test Results

Running comprehensive tests across 7 queries yields:

```
Query: mathematics     - 15 results
Query: calculus       - 8 results  
Query: physics        - 6 results
Query: biology        - 5 results
Query: chemistry      - 4 results
Query: computer science - 3 results
Query: economics      - 2 results

Total: 43 results across all sources
```

## Configuration

### Required Changes

1. **Validation Whitelist** (`app/security/validation.py`):
   ```python
   allowed_sources = [
       # ... existing sources ...
       'Open Textbook Library', 'Pressbooks', 'LibreTexts', 
       'MERLOT', 'OER Commons', 'MIT OpenCourseWare'
   ]
   max_sources = 29  # Increased from 23
   ```

2. **Frontend Configuration** (`frontend/src/components/SearchForm.tsx`):
   ```javascript
   { id: 'MIT OpenCourseWare', name: 'MIT OCW', description: '🏛️ Course Materials', requiresApiKey: true },
   { id: 'MERLOT', name: 'MERLOT', description: '⭐ Peer-reviewed OER', requiresApiKey: true },
   { id: 'OER Commons', name: 'OER Commons', description: '🎓 Ed Resources', requiresApiKey: true },
   ```

3. **Search Service Updates** (`app/services/search.py`):
   - Added API key handling for MIT OCW, MERLOT, and OER Commons
   - Keys are passed via the API Keys modal in the frontend

### API Key Configuration

Users can add API keys through the frontend:
1. Click the key icon next to any grayed-out source
2. Enter the API key in the modal
3. The source will become available for search

For MIT OCW specifically, see `docs/MIT_OCW_CSE_SETUP.md` for Google CSE setup.

### 4. MERLOT

- **Status**: Requires API key
- **Method**: API access only
- **API Key**: Set via `MERLOT` in API Keys modal
- **Without Key**: Returns empty results with log message

### 5. OER Commons

- **Status**: Requires API key
- **Method**: API access only  
- **API Key**: Set via `OER Commons` in API Keys modal
- **Without Key**: Returns empty results with log message

### 6. Pressbooks

- **Status**: Non-functional
- **Issue**: SSL handshake failures
- **Note**: Requires infrastructure fixes

## Architecture

```
app/api_clients/
├── http.py                    # Shared HTTP utilities
├── open_textbook_library.py   # JSON API implementation
├── libretexts.py             # Web scraping implementation
├── mit_ocw.py                # Scraping + CSE fallback
└── mit_ocw_cse.py            # Google CSE implementation
```

## Usage

The OER sources are automatically available when users select them in the OpenScholar interface. No additional configuration is required for basic functionality.

## Future Enhancements

1. **API Keys**: Obtain keys for MERLOT and other restricted sources
2. **Caching**: Implement result caching to reduce API calls
3. **Pagination**: Add support for paginated results
4. **Advanced Search**: Add filters for license type, publication date, etc.
5. **More Sources**: Integrate additional OER repositories as they become available