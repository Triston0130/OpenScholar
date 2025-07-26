# OER API Key UI Guide

This guide shows how the API key configuration UI works for OER sources in OpenScholar.

## Visual Guide

### Sources Without API Keys (Default State)

```
Books & OER
□ DOAB - Open Access Books
□ Open Textbook - 📚 CC Textbooks
□ Pressbooks - 📖 OER Networks
□ LibreTexts - 📗 OER Textbooks
□ MERLOT - ⭐ Peer-reviewed OER                    ⋮
□ OER Commons - 🎓 Ed Resources                    ⋮
□ MIT OCW - 🏛️ Course Materials                   ⋮
```

Sources requiring API keys show:
- Grayed out text
- Disabled checkbox
- Three dots menu (⋮) on the right

### After Clicking Three Dots

A modal appears with:

```
┌─────────────────────────────────────────────────┐
│ Configure MIT OpenCourseWare                  X │
├─────────────────────────────────────────────────┤
│ Full-text search of MIT course materials using  │
│ Google Custom Search Engine                      │
│                                                  │
│ [Get API key ↗]                                 │
│                                                  │
│ API Key: [____________________________] 👁      │
│                                                  │
│ ℹ️ Your API key is stored locally in your       │
│    browser and never sent to our servers.       │
│                                                  │
│ [Cancel]                           [Save API Key]│
└─────────────────────────────────────────────────┘
```

### Sources With API Keys Configured

```
Books & OER
☑ MIT OCW - 🏛️ Course Materials                   ✓
```

After configuration:
- Source text is no longer grayed out
- Checkbox is enabled and can be selected
- Three dots (⋮) change to green shield (✓)
- Source is automatically included in searches

## How It Works

1. **Initial State**: OER sources requiring API keys are grayed out and show three dots
2. **Configuration**: Click three dots → Modal opens → Enter API key → Save
3. **Configured State**: Green shield icon appears, source is enabled
4. **Storage**: API keys are stored in browser localStorage (never sent to server)

## API Key Sources

The following OER sources require API keys:

| Source | API Key Type | Setup Guide |
|--------|--------------|-------------|
| MIT OpenCourseWare | Google API Key | `/mit-ocw-setup.html` |
| MERLOT | MERLOT API Key | [MERLOT API Docs](https://info.merlot.org/merlothelp/topic.htm#t=MERLOT_REST_APIs.htm) |
| OER Commons | OER Commons API Key | [OER Commons API](https://www.oercommons.org/api-docs) |

## Backend Behavior

When API keys are not configured:
- **MIT OCW**: Falls back to basic web scraping (1-5 results)
- **MERLOT**: Returns empty results
- **OER Commons**: Returns empty results

When API keys are configured:
- Full API access is enabled
- Sources participate in multi-source searches
- Results are included in the unified search results

## Implementation Details

### Frontend Files
- `SearchForm.tsx`: Renders sources with three dots/shield icons
- `ApiKeyModal.tsx`: Handles API key configuration
- `apiKeys.ts`: Manages localStorage for API keys

### Backend Files
- `mit_ocw.py`: Checks for API key, falls back to scraping
- `merlot.py`: Requires API key, returns empty without
- `oer_commons.py`: Requires API key, returns empty without
- `search.py`: Passes API keys from frontend to clients