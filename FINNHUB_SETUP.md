# Finnhub API Setup Guide

This guide explains how to set up and use the Finnhub API for market news in the AI-ATL trading platform.

## Overview

The platform now integrates with [Finnhub API](https://finnhub.io/) to provide real-time market news, similar to Yahoo Finance. The Finnhub API provides institutional-grade financial data including:

- General market news
- Company-specific news
- News sentiment analysis
- Real-time stock data
- And much more

## Installation

The Finnhub Python client is already added to `requirements.txt`. Install it with:

```bash
pip install finnhub-python
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Getting Your API Key

1. Visit [https://finnhub.io/register](https://finnhub.io/register)
2. Sign up for a free account (free tier includes 60 API calls/minute)
3. Copy your API key from the dashboard

## Setting Up the API Key

### Option 1: Environment Variable (Recommended)

```bash
export FINNHUB_API_KEY="your_api_key_here"
```

### Option 2: Add to Shell Profile (Permanent)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export FINNHUB_API_KEY="your_api_key_here"
```

Then reload your shell:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Option 3: Set in Current Session

```bash
export FINNHUB_API_KEY="your_api_key_here"
python3 run_server.py
```

## Usage

Once the API key is set, the server will automatically use Finnhub for market news. The news endpoint is available at:

- `GET /api/auth/market/news?limit=20&category=general`
- `GET /market/news?limit=20&category=general`

### Parameters

- `limit` (optional): Number of news items to return (default: 20)
- `category` (optional): News category - `general`, `forex`, `crypto`, `merger` (default: `general`)

### Response Format

```json
{
  "news": [
    {
      "id": 123456,
      "headline": "Market News Headline",
      "summary": "News summary...",
      "source": "Financial Times",
      "url": "https://example.com/article",
      "image": "https://example.com/image.jpg",
      "datetime": 1234567890,
      "datetime_formatted": "2024-01-01T12:00:00",
      "category": "general",
      "related": "AAPL,MSFT,GOOGL"
    }
  ],
  "timestamp": "2024-01-01T12:00:00",
  "source": "finnhub"
}
```

## Fallback to Mock Data

If the Finnhub API is unavailable or the API key is not set, the system will automatically fall back to mock news data. This ensures the application continues to work even without API access.

## Frontend Integration

The frontend automatically fetches and displays market news on the dashboard. News articles are displayed as clickable cards with:

- Headline
- Summary
- Source
- Related tickers
- Publication time
- Link to full article

## API Rate Limits

Free tier limits:
- 60 API calls per minute
- Sufficient for typical usage

If you exceed rate limits, the system will fall back to mock data.

## Troubleshooting

### API Key Not Working

1. Verify the API key is set: `echo $FINNHUB_API_KEY`
2. Check server logs for error messages
3. Verify the API key is valid at https://finnhub.io/dashboard

### No News Showing

1. Check if API key is set
2. Check server logs for errors
3. Verify internet connection
4. Check if you've exceeded rate limits

### Import Errors

If you get import errors:

```bash
pip install finnhub-python
```

## Additional Resources

- [Finnhub API Documentation](https://finnhub.io/docs/api)
- [Finnhub Python Client GitHub](https://github.com/Finnhub-Stock-API/finnhub-python)
- [Finnhub Pricing](https://finnhub.io/pricing)

## Notes

- The Finnhub client is synchronous, so API calls are executed in a thread pool to avoid blocking the async server
- News is cached on the frontend and refreshes every 10 seconds
- The system gracefully handles API failures and falls back to mock data

