# Google Search Setup Instructions

## Step 1: Get Google Search API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Custom Search API"
4. Go to Credentials → Create Credentials → API Key
5. Copy the API key

## Step 2: Create Custom Search Engine
1. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
2. Click "Add" to create a new search engine
3. **Sites to search**: Enter `*` (asterisk) to search the entire web
4. **Language**: Select your preferred language
5. **Search engine name**: Enter something like "OpenScholar PDF Search"
6. Click "Create"

## Step 3: Configure the Search Engine
1. After creating, click on your search engine
2. Go to "Setup" tab
3. Under "Basics":
   - Make sure "Search the entire web" is enabled
   - Turn ON "Image search" and "Safe search" 
4. Go to "Advanced" tab
5. In the "Restrict Pages using Schema.org Types" section, you can optionally add:
   - `Thing > CreativeWork > Article`
   - `Thing > CreativeWork > ScholarlyArticle`
6. Click "Update"

## Step 4: Get the Search Engine ID
1. In your Custom Search Engine control panel
2. Go to "Setup" tab
3. Copy the **Search engine ID** (it looks like: `017576662512468239146:omuauf_lfve`)

## Step 5: Configure in OpenScholar
1. In OpenScholar, click the vertical dots (⋮) next to "Google Search"
2. Enter your **API Key** in the first field
3. Enter your **Search Engine ID** in the second field
4. Click Save

## Test Configuration
- Try searching for "machine learning filetype:pdf" in Google to see if results look good
- The search engine should return PDF files from across the web
- Results will be filtered for open access content automatically

## Important Notes
- Google Custom Search has daily quotas (100 free searches/day)
- For production use, you may need to set up billing
- The search engine will only return PDF files due to our filtering
- Results are automatically checked for open access compliance

## Troubleshooting
- If no results appear, check that your search engine is set to "Search the entire web"
- Make sure both API key and Search Engine ID are correct
- Check the browser console for any error messages
- Verify your Google Cloud project has the Custom Search API enabled