# OpenScholar AI-Powered Notes & Tags Generation

## Overview

OpenScholar now includes AI-powered functionality to automatically generate notes and tags for papers in your collections. This feature uses OpenAI's GPT models to analyze paper abstracts and metadata to create comprehensive summaries and relevant tags.

## Features

### 1. AI Processing for Collections and Folders
- Process entire collections or specific folders with AI
- Generate comprehensive notes including:
  - Main findings
  - Methodology
  - Key contributions
  - Limitations
  - Relevance to the field
- Generate up to 10 relevant tags per paper
- Support for multiple OpenAI models (GPT-3.5 Turbo, GPT-4 Turbo, GPT-4)

### 2. Smart Processing Options
- **Process Empty Only**: Option to only process papers without existing notes/tags
- **Batch Processing**: Papers are processed in batches to optimize API usage
- **Cost Estimation**: See estimated costs before processing

### 3. User-Friendly Interface
- Integrated into the existing collection menu (vertical dots ...)
- Modal dialog for configuration
- Real-time API key validation
- Progress indicator during processing
- Success/failure reporting

## How to Use

### 1. Set Up OpenAI API Key
1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. The key will be securely stored in your browser's localStorage
3. Test the key using the "Test Key" button in the AI Processing modal

### 2. Process a Collection
1. Navigate to your Collections view
2. Click the three dots (...) menu next to any collection
3. Select "🤖 Process with AI"
4. Configure your settings:
   - Enter/verify your OpenAI API key
   - Select the AI model
   - Adjust temperature (creativity level)
   - Set max response length
   - Choose whether to process only empty papers
5. Click "Start Processing"

### 3. Process a Folder
1. Select a collection and navigate to a specific folder
2. Click the three dots (...) menu next to the folder
3. Select "🤖 Process with AI"
4. Follow the same configuration steps as above

## Configuration Options

### AI Models
- **GPT-3.5 Turbo**: Fast and cost-effective (~$0.001/paper)
- **GPT-4 Turbo**: More capable for complex analysis (~$0.016/paper)
- **GPT-4**: Most capable for detailed analysis (~$0.024/paper)

### Advanced Settings
- **Temperature** (0-1): Controls creativity vs. focus
  - Lower values (0.3-0.5): More focused, factual summaries
  - Higher values (0.7-0.9): More creative, varied outputs
- **Max Tokens** (500-2000): Controls response length
  - 500-1000: Brief summaries
  - 1000-2000: Detailed analysis

## Technical Implementation

### Backend (FastAPI)
- New endpoint: `/api/ai/process-collection`
- Secure API key handling
- Batch processing with rate limiting
- Error handling and retry logic
- Cost estimation based on token usage

### Frontend (React/TypeScript)
- New component: `AIProcessingModal.tsx`
- API integration in `utils/api.ts`
- Authentication token included in requests
- Progress tracking and error handling

### Database
- Extended `collection_papers` model to support AI metadata
- New fields:
  - `ai_notes`: AI-generated notes
  - `ai_tags`: AI-generated tags
  - `ai_processed_at`: Processing timestamp
  - `ai_model_used`: Model used for generation

## Security Considerations

1. **API Key Storage**: Keys are stored in browser localStorage (not sent to backend database)
2. **Authentication**: All AI endpoints require user authentication
3. **Input Sanitization**: All AI-generated content is sanitized before storage
4. **Rate Limiting**: Batch processing prevents API abuse

## Cost Management

- Costs are estimated before processing
- Actual costs depend on paper length and model used
- Process only papers without existing notes/tags to minimize costs
- Monitor your OpenAI usage dashboard for actual billing

## Troubleshooting

### Common Issues

1. **"Invalid API Key"**: Ensure your OpenAI API key is valid and has credits
2. **"Processing Failed"**: Check your internet connection and API key limits
3. **"No Papers Processed"**: All papers may already have notes/tags
4. **Timeout Errors**: Large collections may take time - processing continues in background

### Best Practices

1. Start with a small folder to test your settings
2. Use GPT-3.5 Turbo for initial processing (most cost-effective)
3. Review and edit AI-generated content as needed
4. Keep your API key secure and don't share it

## Future Enhancements

- Support for other AI providers (Anthropic Claude, Google Gemini)
- Custom prompt templates
- Bulk editing of AI-generated content
- Integration with citation management tools
- Automatic re-processing when new papers are added

## API Reference

### POST `/api/ai/process-collection`
Process papers in a collection with AI.

Request body:
```json
{
  "collection_id": "uuid",
  "folder_id": "uuid (optional)",
  "ai_config": {
    "api_key": "sk-...",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "process_empty_only": true
}
```

Response:
```json
{
  "collection_id": "uuid",
  "processed_papers": [...],
  "total_processed": 10,
  "total_failed": 0,
  "total_cost_estimate": 0.01
}
```

### GET `/api/ai/models`
Get available AI models and pricing.

### POST `/api/ai/test-api-key`
Test if an OpenAI API key is valid.

## Support

For issues or feature requests related to AI processing, please open an issue on the OpenScholar GitHub repository with the tag "ai-features".