# TTS Text Extraction Improvements

## What was fixed:

### 1. **Spatial Text Ordering**
- Previously: Text items were joined without considering their position, causing text from different columns or sections to be mixed
- Now: Text items are sorted by Y position (top to bottom) and X position (left to right) within lines

### 2. **Multi-Column Layout Detection**
- Added logic to detect and handle multi-column layouts
- Text in left column is read completely before moving to right column
- References sections are treated specially to maintain citation integrity

### 3. **Line Grouping**
- Text items within 5 pixels vertically are grouped as the same line
- Lines are properly ordered from top to bottom

### 4. **Paragraph Detection**
- Added paragraph breaks when vertical gap between lines exceeds 20 pixels
- Prevents run-on sentences from different paragraphs

### 5. **HTML Text Extraction**
- Improved HTML viewer text extraction using TreeWalker API
- Maintains document structure and reading order
- Filters out script, style, and other non-content elements
- Adds proper paragraph breaks between block elements

### 6. **Sentence Boundary Detection**
- Added comprehensive abbreviation handling (Dr., Ph.D., etc.)
- Prevents false sentence breaks at common academic abbreviations
- Improved sentence splitting regex to handle edge cases

## Testing the improvements:

1. **Test with multi-column PDF**:
   - Open a research paper with two-column layout
   - Enable TTS and verify left column is read before right column

2. **Test with references section**:
   - Navigate to bibliography/references
   - Verify citations are read in order without jumping between entries

3. **Test with complex formatting**:
   - Try PDFs with figures, tables, and captions
   - Verify reading order follows logical document flow

4. **Test with HTML viewer**:
   - Open a document in HTML viewer mode
   - Verify text extraction maintains proper structure

## Key improvements for academic papers:
- Handles "et al.", "Fig.", "Eq.", and other academic abbreviations
- Maintains citation integrity in references sections
- Respects column layouts common in research papers
- Preserves paragraph structure for better comprehension