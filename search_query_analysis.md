# API Search Query Analysis

## Overview
This document analyzes how each API client in the OpenScholar application handles search queries, including query transformation, advanced features support, encoding methods, and preprocessing.

## Base Classes

### BaseAPIClient (base.py)
- Abstract base class defining the search interface
- Search method signature: `async def search(query: str, year_start: int, year_end: int, discipline: Optional[str], education_level: Optional[str], limit: int)`
- No query transformation at base level

### BASEClient (base_search.py)
- **Query Transformation**: 
  - Direct query pass-through
  - Adds year filter using Lucene syntax: `dcyear:[{year_start} TO {year_end}]`
  - Adds discipline filter: `dcsubject:{discipline}`
- **Advanced Features**: Supports Lucene query syntax (boolean operators, field searches)
- **Encoding**: No explicit encoding shown, relies on httpx client
- **Preprocessing**: None beyond filter addition

## API Clients Analysis

### 1. ArXiv API Client (arxiv.py)
- **Query Transformation**:
  - Direct query pass-through
  - Discipline mapped to category filters: `cat:{category}*` (e.g., `cat:cs*` for computer science)
  - Multiple categories joined with OR: `(cat:cs* OR cat:math*)`
  - Terms joined with AND: `query AND cat:physics*`
- **Advanced Features**: 
  - Boolean operators (AND, OR)
  - Category-based filtering
  - Wildcard support in categories (`cat:cs*`)
- **Encoding**: No explicit encoding, relies on httpx
- **Preprocessing**: Maps disciplines to arXiv category codes

### 2. Crossref API Client (crossref.py)
- **Query Transformation**:
  - Direct query pass-through for basic search
  - Discipline enhancement: `{query} AND ({discipline_terms})` where discipline_terms are predefined keyword expansions
  - Example: education → "education OR educational OR teaching OR learning OR pedagogy"
- **Advanced Features**:
  - Boolean operators (AND, OR)
  - Filter-based search using Crossref filter syntax
  - Supports comma-separated filters
- **Encoding**: No explicit encoding
- **Preprocessing**: Expands discipline into related keywords

### 3. PubMed API Client (pubmed.py)
- **Query Transformation**:
  - Builds complex queries with MeSH terms and field specifiers
  - Discipline mapping: `(education[MeSH] OR educational[Title/Abstract])`
  - Education level mapping: `(early childhood[Title/Abstract] OR preschool[Title/Abstract])`
  - Date filter: `{year_start}:{year_end}[pdat]`
  - Terms joined with AND
- **Advanced Features**:
  - MeSH term searching
  - Field-specific searches ([Title/Abstract], [MeSH])
  - Date range filtering with [pdat]
  - Boolean operators (AND, OR)
- **Encoding**: No explicit encoding
- **Preprocessing**: Maps disciplines and education levels to MeSH terms and field searches

### 4. Semantic Scholar API Client (semantic_scholar.py)
- **Query Transformation**:
  - Concatenates query with discipline and education level keywords
  - Discipline expansion: "education educational teaching learning"
  - Education level expansion: "early childhood preschool kindergarten"
  - All terms concatenated with spaces (implicit AND)
- **Advanced Features**: Limited - mainly keyword concatenation
- **Encoding**: No explicit encoding
- **Preprocessing**: Expands disciplines and education levels into related terms

### 5. Google Books API Client (google_books.py)
- **Query Transformation**:
  - Adds search operators: `(inauthor: OR intitle: OR inpublisher:)`
  - Adds subject filters: `subject:Education`
  - Concatenates discipline keywords directly
- **Advanced Features**:
  - Google Books specific operators (inauthor:, intitle:, subject:)
  - OR operators
- **Encoding**: No explicit encoding
- **Preprocessing**: Maps disciplines to Google Books subject categories

### 6. ERIC API Client (eric.py)
- **Query Transformation**:
  - Uses descriptor syntax: `descriptor:education`
  - Education level filters: `educationlevel:Early Childhood Education`
  - Terms joined with AND
  - Filter query (fq) parameters for additional filtering
- **Advanced Features**:
  - Descriptor-based searching
  - Education level filtering
  - Boolean operators (AND)
  - Solr-style filter queries
- **Encoding**: No explicit encoding
- **Preprocessing**: Maps disciplines to ERIC descriptors

### 7. PLOS API Client (plos.py)
- **Query Transformation**:
  - Uses field-specific search: `everything:"{query}"`
  - Date range: `publication_date:[{year_start}-01-01T00:00:00Z TO {year_end}-12-31T23:59:59Z]`
  - Subject filter: `subject:"{discipline}"`
  - Terms joined with AND
- **Advanced Features**:
  - Field-specific searches (everything:, subject:)
  - Date range queries with timestamps
  - Boolean operators (AND)
  - Quotes for exact phrase matching
- **Encoding**: No explicit encoding
- **Preprocessing**: Maps disciplines to PLOS subject categories

### 8. DOAJ API Client (doaj.py)
- **Query Transformation**:
  - Simple query pass-through
  - URL encoding using `urllib.parse.quote()`
- **Advanced Features**: Limited - basic keyword search
- **Encoding**: Explicit URL encoding with `urllib.parse.quote()`
- **Preprocessing**: None

## Summary of Query Handling Patterns

### Common Patterns:
1. **Direct Pass-through**: Most APIs accept the user query as-is
2. **Field Concatenation**: Discipline and education level filters are typically added using AND operators
3. **No Advanced Encoding**: Most rely on httpx client for URL encoding
4. **Limited Preprocessing**: Main preprocessing is mapping disciplines to API-specific categories

### APIs with Advanced Features:
1. **PubMed**: Most sophisticated with MeSH terms, field-specific searches
2. **PLOS**: Field-specific searches with timestamp-based date filtering
3. **ERIC**: Descriptor-based searching with Solr-style filters
4. **Crossref**: Filter-based approach with keyword expansion
5. **ArXiv**: Category-based filtering with wildcards

### APIs with Basic Search:
1. **DOAJ**: Simple keyword search with URL encoding
2. **Semantic Scholar**: Keyword concatenation only
3. **Google Books**: Uses Google-specific operators but limited boolean logic

### Query Enhancement Strategies:
1. **Keyword Expansion**: Crossref, Semantic Scholar expand disciplines into related terms
2. **Category Mapping**: ArXiv, Google Books map to predefined categories
3. **Field-Specific Search**: PubMed, PLOS, ERIC use field identifiers
4. **Date Filtering**: Varies widely - some use query syntax, others use parameters

### 9. Europe PMC API Client (europe_pmc.py)
- **Query Transformation**:
  - Adds multiple filters joined with AND
  - Open access filter: `OPEN_ACCESS:y`
  - License filter: `LICENSE:cc*` (Creative Commons)
  - PDF availability: `HAS_PDF:y`
  - Date range: `PUB_YEAR:[{year_start} TO {year_end}]`
  - Discipline expansion with OR: `(education OR pedagogy)`
- **Advanced Features**:
  - Boolean operators (AND, OR)
  - Wildcard support (cc*)
  - Field-specific filters
  - Date range queries
- **Encoding**: No explicit encoding
- **Preprocessing**: Expands disciplines and education levels into synonyms

### 10. CORE API Client (core.py)
- **Query Transformation**:
  - Simple concatenation with AND
  - Year filter: `yearPublished:[{year_start} TO {year_end}]`
  - Direct discipline/education level append
- **Advanced Features**:
  - Boolean AND operator
  - Range queries for years
  - fullText parameter filtering
- **Encoding**: No explicit encoding
- **Preprocessing**: None - direct concatenation

### 11. Internet Archive API Client (internet_archive.py)
- **Query Transformation**:
  - Complex query building with parentheses for grouping
  - Media type filter: `mediatype:(texts OR books)`
  - Collection filters: `collection:opensource OR collection:gutenberg`
  - Exclusion: `NOT collection:inlibrary`
  - Year range: `year:[{year_start} TO {year_end}]`
  - Discipline expansion: `(education OR educational OR teaching...)`
- **Advanced Features**:
  - Boolean operators (AND, OR, NOT)
  - Parenthetical grouping
  - Range queries
  - Field-specific searches
  - Collection-based filtering
- **Encoding**: No explicit encoding
- **Preprocessing**: Extensive discipline keyword expansion

## Key Findings

### 1. Query Syntax Variations
- **Lucene-style**: BASE, Internet Archive use Lucene syntax with field:value notation
- **SQL-like**: PLOS uses timestamp-based date filtering
- **MeSH/Controlled Vocabulary**: PubMed uses Medical Subject Headings
- **Simple Concatenation**: Semantic Scholar, CORE use basic string concatenation
- **API-specific**: Google Books uses unique operators (inauthor:, intitle:)

### 2. Boolean Operator Support
- **Full Support (AND, OR, NOT)**: Internet Archive, ArXiv, PubMed, Europe PMC
- **Limited Support (AND, OR)**: Crossref, PLOS, ERIC
- **AND Only**: CORE, BASE
- **No Explicit Operators**: Semantic Scholar (implicit AND), DOAJ

### 3. Advanced Features by API
- **Field-Specific Search**: PubMed ([MeSH], [Title/Abstract]), PLOS (everything:, subject:), ERIC (descriptor:)
- **Wildcards**: ArXiv (cat:cs*), Europe PMC (LICENSE:cc*)
- **Range Queries**: Most APIs support year ranges with varying syntax
- **Exclusion/NOT**: Internet Archive (NOT collection:inlibrary)

### 4. Query Preprocessing Approaches
- **No Preprocessing**: DOAJ, CORE - pass query as-is
- **Keyword Expansion**: Crossref, Semantic Scholar, Europe PMC, Internet Archive
- **Category Mapping**: ArXiv (to arXiv categories), Google Books (to subjects)
- **Controlled Vocabulary**: PubMed (MeSH terms), ERIC (descriptors)

### 5. Encoding Methods
- **Explicit URL Encoding**: Only DOAJ uses urllib.parse.quote()
- **Implicit Encoding**: All others rely on httpx client for URL encoding
- **No Special Characters Handling**: Most APIs don't preprocess special characters

### 6. Date Filtering Approaches
- **Query Syntax**: BASE (dcyear:[]), PLOS (publication_date:[]), Internet Archive (year:[])
- **Filter Parameters**: Crossref (filter parameter), ERIC (fq parameter)
- **Post-Processing**: ArXiv filters results after retrieval
- **No Direct Support**: Semantic Scholar (year parameter but limited)

## Recommendations for Unified Query Interface

1. **Standardize Boolean Operators**: Convert user queries with AND/OR/NOT to API-specific syntax
2. **Abstract Field Searches**: Map common fields (title, author, abstract) to API-specific fields
3. **Unified Date Format**: Accept standard date range and convert to API-specific formats
4. **Smart Query Enhancement**: Optionally expand queries with synonyms based on API capabilities
5. **Encoding Strategy**: Implement proper URL encoding for all APIs, not just DOAJ
6. **Query Validation**: Pre-validate queries to ensure compatibility with target API syntax

