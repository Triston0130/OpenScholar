# TTS PDF Text Extraction Fix Summary

## Problem
The Text-to-Speech (TTS) feature was showing "Unable to extract text from PDF" for every PDF document.

## Root Cause
The PDF document reference (`pdfDocRef.current`) was sometimes null when TTS was triggered, causing the text extraction to fail immediately.

## Solution Implemented

### 1. **Enhanced PDF Document Reference Handling**
- Added retry logic to wait for PDF document to load if not immediately available
- Added proper error logging to track when PDF document is not available

### 2. **Backend Fallback Mechanism**
- Created a new backend endpoint `/api/extract-pdf-text` that uses PyPDF2 for text extraction
- If frontend extraction fails or yields no text, automatically fallback to backend extraction
- This provides redundancy and handles edge cases where PDF.js might fail

### 3. **Improved Error Handling**
- Better error messages to distinguish between different failure scenarios
- More detailed logging for debugging text extraction issues
- Page-by-page error handling to continue extraction even if some pages fail

## Technical Changes

### Frontend (`PDFViewerSmart.tsx`)
```typescript
// Added retry logic for PDF document
if (!doc) {
    console.log('[TTS] PDF document not in ref, trying to get from viewer...');
    await new Promise(resolve => setTimeout(resolve, 500));
    doc = pdfDocRef.current;
}

// Added backend fallback
const tryBackendExtraction = async () => {
    const response = await fetch('/api/extract-pdf-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            pdf_url: effectivePdfUrl,
            max_pages: 50
        }),
    });
    // Process response...
};
```

### Backend (`main.py`)
```python
@app.post("/api/extract-pdf-text", response_model=dict, tags=["PDF"])
async def extract_pdf_text(request: dict, rate_limited = Depends(rate_limit_check)):
    """Extract text content from a PDF for TTS"""
    # Uses existing pdf_extractor utility
    result = await extract_text_from_pdf_url(pdf_url, max_pages=max_pages)
    return result
```

## Benefits
1. **Reliability**: Dual extraction methods ensure text can be extracted even if one method fails
2. **Performance**: Frontend extraction is tried first for better performance, backend is fallback
3. **Error Recovery**: Better error messages help users understand issues
4. **Seamless Integration**: No changes to UI or user experience - works exactly the same from user perspective

## Testing
To test the fix:
1. Open any PDF in the viewer
2. Click the "Read Aloud" button
3. Text should extract successfully and TTS should work
4. Check browser console for extraction logs if issues occur