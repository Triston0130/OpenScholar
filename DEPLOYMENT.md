# OpenScholar Backend Deployment on Render.com

## Quick Deploy

This backend is configured for automatic deployment on Render.com using Infrastructure-as-Code.

### 1. Connect GitHub Repository

1. Go to [Render.com Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub account
4. Select repository: `Triston0130/OpenScholar`
5. Render will automatically detect `render.yaml` and create the service

### 2. Set Environment Variables

In the Render dashboard, set these environment variables:

```bash
# Required - Get from CORE API
CORE_API_KEY=your_actual_core_api_key_here

# Optional - Leave blank if not using
ERIC_API_KEY=
DOAJ_API_KEY=

# API Configuration (defaults provided)
MAX_RESULTS_PER_API=20
REQUEST_TIMEOUT=30

# CORS Configuration (optional)
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

### 3. Deploy

- Render automatically deploys on every push to `main` branch
- Build takes ~2-3 minutes
- Service URL: `https://openscholar-api-[random].onrender.com`

## Service Configuration

The `render.yaml` file configures:

- **Runtime**: Python 3.11
- **Plan**: Starter (free tier)
- **Region**: Oregon (us-west-2)
- **Auto-scaling**: 1-3 instances
- **Health checks**: `/` endpoint
- **Auto-deploy**: On git push

## API Endpoints

Once deployed, your API will be available at:

```
https://your-service-url.onrender.com/
```

### Available endpoints:
- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /search` - Search papers
- `POST /export` - Export papers

## Frontend Integration

Update your React frontend's API base URL to use the Render deployment:

```typescript
// In src/utils/api.ts
const API_BASE_URL = 'https://your-service-url.onrender.com';
```

## Monitoring

- View logs in Render dashboard
- Health check at `/health` shows service status
- Auto-restart on failures
- Metrics available in dashboard

## Troubleshooting

### Common Issues:

1. **Build fails**: Check `requirements.txt` for compatibility
2. **Service unhealthy**: Verify environment variables are set
3. **CORS errors**: Add your frontend domain to `ALLOWED_ORIGINS`
4. **API key errors**: Ensure `CORE_API_KEY` is valid

### Debug commands:
```bash
# Check service status
curl https://your-service-url.onrender.com/health

# Test search endpoint
curl -X POST https://your-service-url.onrender.com/search \
  -H "Content-Type: application/json" \
  -d '{"query": "education research", "year_start": 2020, "year_end": 2024}'
```

## Cost

- **Starter Plan**: Free tier with limitations
- **Upgrade**: Professional plan for production use
- **Auto-scaling**: Only pay for active instances

## Security

- All environment variables encrypted
- HTTPS enabled by default
- CORS configured for known domains
- Request rate limiting in place