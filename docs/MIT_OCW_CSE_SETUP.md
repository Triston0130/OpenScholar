# MIT OpenCourseWare Google Custom Search Engine Setup

This guide explains how to set up Google Custom Search Engine (CSE) for enhanced MIT OpenCourseWare search functionality in OpenScholar.

## Important Note

MIT OpenCourseWare is now configured as an API-key-required source in OpenScholar. Without a Google API key:
- The source will appear grayed out in the search interface
- Basic web scraping provides very limited results (1-5 courses)
- Users must add their Google API key via the API Keys modal to enable full search

## Why Use Google CSE?

The default MIT OCW client uses web scraping, which:
- Has limited search capabilities
- Can only search through department pages
- Returns a maximum of ~5-10 results

With Google CSE, you get:
- Full-text search across all MIT OCW content
- Up to 100 results per query
- Better relevance ranking
- Faster response times
- Access to course descriptions, prerequisites, and more

## Setup Instructions

### 1. Create a Google Custom Search Engine

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure the search engine:
   - **Sites to search**: Add `ocw.mit.edu/*`
   - **Language**: English
   - **Search engine name**: MIT OpenCourseWare
4. Click "Create"
5. Copy your **Search engine ID** (looks like: `017643444788069204610:4gvhea_mvga`)

### 2. Get a Google API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Custom Search API":
   - Go to "APIs & Services" > "Library"
   - Search for "Custom Search API"
   - Click on it and press "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key
   - (Optional) Restrict the key to the Custom Search API for security

### 3. Configure OpenScholar

#### Option A: Via Frontend (Recommended)

1. In the OpenScholar search interface, click the key icon next to "MIT OCW"
2. Enter your Google API key in the modal
3. The CSE ID can be set via environment variable:
   ```bash
   export MIT_OCW_CSE_ID='your-cse-id-here'
   # or use the general CSE_ID variable:
   export GOOGLE_CSE_ID='your-cse-id-here'
   ```

#### Option B: Via Environment Variables

```bash
export GOOGLE_CSE_API_KEY='your-api-key-here'
export MIT_OCW_CSE_ID='your-cse-id-here'
```

Note: The frontend method is preferred as it allows users to manage their own API keys.

### 4. Test the Configuration

Run the test script to verify everything is working:

```bash
python test_mit_ocw_cse.py
```

## Usage

Once configured, the MIT OCW client will automatically use Google CSE. The search will:

1. First attempt to use Google CSE if configured
2. Fall back to web scraping if CSE fails or isn't configured
3. Return enhanced results with:
   - Full course titles
   - Course numbers (e.g., 18.01, 6.001)
   - Department information
   - Direct links to course pages
   - Course descriptions
   - Year information

## API Limits

Google CSE has the following limits:
- **Free tier**: 100 queries per day
- **Paid tier**: $5 per 1,000 queries (up to 10,000/day)

The client handles quota errors gracefully by falling back to web scraping.

## Advanced Configuration

### Custom Search Engine Refinements

You can improve search results by:

1. Going to your CSE control panel
2. Adding search refinements:
   - Label: "Courses"
   - Filter: `more:pagemap:metatags-og:type:course`
3. Excluding non-course pages:
   - Add patterns like `-inurl:give -inurl:search -inurl:subscribe`

### Using Multiple CSE IDs

You can create separate CSEs for different purposes:

```python
# For general MIT OCW search
export MIT_OCW_CSE_ID='xxx'

# For searching only recent courses
export MIT_OCW_RECENT_CSE_ID='yyy'

# For searching only graduate courses  
export MIT_OCW_GRAD_CSE_ID='zzz'
```

## Troubleshooting

### "Invalid API key" Error
- Verify your API key is correct
- Check that the Custom Search API is enabled in Google Cloud Console
- Ensure the API key isn't restricted to specific IPs/referrers

### "Invalid CSE ID" Error
- Double-check the CSE ID from the control panel
- Make sure you're using the Search engine ID, not the Public URL

### No Results
- Verify the CSE is configured to search `ocw.mit.edu`
- Test the search engine at programmablesearchengine.google.com first
- Check if you've hit the daily quota limit

### Quota Exceeded
- The free tier is limited to 100 searches/day
- Consider upgrading to a paid plan
- The client will automatically fall back to web scraping

## Example Results

With Google CSE enabled, searching for "machine learning" returns:

```
1. 6.034 Artificial Intelligence
   Course Number: 6.034
   URL: https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/
   
2. 6.867 Machine Learning
   Course Number: 6.867  
   URL: https://ocw.mit.edu/courses/6-867-machine-learning-fall-2006/

3. 9.520 Statistical Learning Theory and Applications
   Course Number: 9.520
   URL: https://ocw.mit.edu/courses/9-520-statistical-learning-theory-spring-2003/
```

Without CSE, the same search might return only 1-2 generic results.