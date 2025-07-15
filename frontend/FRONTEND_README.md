# OpenScholar Frontend

A React frontend for searching and exporting peer-reviewed, open-access research papers.

## Features

- **Smart Search**: Keyword search with filters for year range, discipline, and education level
- **Clean Results**: Mobile-friendly cards showing title, authors, abstract, and metadata
- **Export Options**: Download results as CSV, JSON, or BibTeX
- **Multiple Sources**: Searches ERIC, CORE, DOAJ, Europe PMC, and PubMed Central
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- React 18 with TypeScript
- TailwindCSS for styling
- Axios for API calls
- React Hot Toast for notifications

## Getting Started

1. **Install dependencies:**
```bash
npm install
```

2. **Start development server:**
```bash
npm start
```

The app will open at `http://localhost:3000` (or `http://localhost:3001` if 3000 is busy).

3. **Ensure backend is running:**
Make sure the OpenScholar API is running at `http://localhost:8001`.

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── SearchForm.tsx   # Search form with filters
│   ├── ResultCard.tsx   # Individual paper card
│   └── ExportBar.tsx    # Export functionality
├── pages/
│   └── SearchPage.tsx   # Main search page
├── utils/
│   └── api.ts          # API integration
├── types.ts            # TypeScript types
├── App.tsx             # Root component
└── index.tsx           # Entry point
```

## Usage

1. **Search Papers**: Enter keywords and optionally filter by:
   - Year range (start/end year)
   - Discipline (education, psychology, child development, early childhood)
   - Education level (early childhood, K-12, higher education)

2. **View Results**: Papers are displayed as cards with:
   - Clickable title (if full text is available)
   - Authors and publication year
   - Source tags (ERIC, CORE, DOAJ, etc.)
   - Expandable abstract
   - DOI and full text links

3. **Export Results**: Use the export bar to download results as:
   - **BibTeX (.bib)**: For citation managers like Zotero, Mendeley
   - **CSV (.csv)**: For spreadsheets like Excel, Google Sheets
   - **JSON (.json)**: Raw structured data

## API Integration

The frontend communicates with the OpenScholar backend API:

- `POST /search`: Search for papers
- `POST /export`: Export papers in specified format

## Mobile Responsiveness

The interface adapts to different screen sizes:
- Mobile-first design
- Responsive grid layouts
- Touch-friendly buttons and links
- Optimized typography and spacing

## Error Handling

- Toast notifications for success/error states
- Graceful handling of API failures
- User-friendly error messages
- Loading indicators during operations