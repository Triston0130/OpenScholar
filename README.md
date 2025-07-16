# OpenScholar

A full-stack application for searching peer-reviewed, open-access research papers in education and child development.

## 🎯 Features

- **Multi-API Search**: Searches ERIC, CORE, DOAJ, Europe PMC, and PubMed Central
- **Smart Filtering**: Year range, discipline, and education level filters
- **Export Options**: CSV, JSON, and BibTeX formats
- **Responsive UI**: Mobile-friendly React frontend
- **Production Ready**: Deployed on Render.com with auto-scaling

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally
python run.py
# API available at http://localhost:8001
```

### Frontend (React/TypeScript)

```bash
cd frontend
npm install
npm start
# App available at http://localhost:3000
```

## 🌐 Production Deployment

The backend is configured for one-click deployment on Render.com:

1. Connect your GitHub repo to Render
2. Render detects `render.yaml` and auto-configures
3. Set environment variables in dashboard
4. Deploy automatically on git push

**Live API**: `https://openscholar-api-[random].onrender.com`

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

## 📁 Project Structure

```
OpenScholar/
├── app/                    # FastAPI backend
│   ├── api_clients/       # API integrations (ERIC, CORE, etc.)
│   ├── export/            # Export services (CSV, JSON, BibTeX)
│   ├── services/          # Business logic
│   ├── models.py          # Pydantic models
│   └── main.py            # FastAPI app
├── frontend/              # React frontend
│   ├── src/components/    # React components
│   ├── src/pages/         # Page components
│   └── src/utils/         # API integration
├── render.yaml            # Render.com deployment config
├── requirements.txt       # Python dependencies
└── DEPLOYMENT.md          # Deployment guide
```

## 🔗 API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed service status
- `POST /search` - Search papers across all APIs
- `POST /export` - Export papers in various formats

### API Documentation
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Usage Example

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "language development",
    "year_start": 2020,
    "year_end": 2024,
    "discipline": "child development",
    "education_level": "early childhood"
  }'
```

## Response Format

```json
{
  "total_results": 25,
  "papers": [
    {
      "title": "Early Language Development in Children",
      "authors": ["Smith, J.", "Jones, M."],
      "abstract": "This study examines...",
      "year": "2023",
      "source": "ERIC",
      "full_text_url": "https://example.com/paper.pdf",
      "doi": "10.1234/example",
      "journal": "Journal of Child Development"
    }
  ],
  "sources_queried": ["ERIC", "CORE", "DOAJ", "Europe PMC", "PubMed Central"]
}
```

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
CORE_API_KEY=your_core_api_key_here
ERIC_API_KEY=optional
DOAJ_API_KEY=optional
MAX_RESULTS_PER_API=20
REQUEST_TIMEOUT=30
```

## 🛠 Development

### Backend Testing
```bash
python test_api.py
python test_export.py
```

### Frontend Development
```bash
cd frontend
npm start  # Development server
npm run build  # Production build
```

## 📊 Supported APIs

1. **ERIC** - Education research papers
2. **CORE** - Open access research papers  
3. **DOAJ** - Directory of Open Access Journals
4. **Europe PMC** - Biomedical and life sciences
5. **PubMed Central** - Biomedical literature

### Search Parameters

- `query` (required): Search keywords
- `year_start` (optional): Start year filter (default: 2000)
- `year_end` (optional): End year filter (default: current year)
- `discipline` (optional): "education", "psychology", "child development", "early childhood"
- `education_level` (optional): "early childhood", "k-12", "higher education"

### Export Parameters

- `papers` (required): List of Paper objects to export
- `format` (required): Export format - "csv", "json", or "bib"

## Export Examples

### Export to BibTeX
```bash
curl -X POST "http://localhost:8001/export" \
  -H "Content-Type: application/json" \
  -d '{
    "papers": [
      {
        "title": "Early Language Development in Children",
        "authors": ["Smith, J.", "Jones, M."],
        "abstract": "This study examines...",
        "year": "2023",
        "source": "ERIC",
        "full_text_url": "https://example.com/paper.pdf",
        "doi": "10.1234/example",
        "journal": "Journal of Child Development"
      }
    ],
    "format": "bib"
  }' \
  -o "export.bib"
```

### Export to CSV
```bash
curl -X POST "http://localhost:8001/export" \
  -H "Content-Type: application/json" \
  -d '{"papers": [...], "format": "csv"}' \
  -o "export.csv"
```

### Export to JSON
```bash
curl -X POST "http://localhost:8001/export" \
  -H "Content-Type: application/json" \
  -d '{"papers": [...], "format": "json"}' \
  -o "export.json"
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- GitHub Issues: Report bugs and feature requests
- Documentation: See DEPLOYMENT.md for setup help
- API Status: Check `/health` endpoint for service status

## Notes

- Only peer-reviewed papers are returned (when filterable by the API)
- Papers are deduplicated by DOI and normalized title
- Results are sorted by year (newest first)
- Export files include timestamp in filename
- BibTeX exports include proper citation keys and field escaping
- All exports include the original source attribution
