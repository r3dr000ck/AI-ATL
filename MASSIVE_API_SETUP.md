# Massive.com API Integration Setup

This guide explains how to integrate real market data from [Massive.com](https://massive.com) (formerly Polygon.io) to replace the mock data in your trading platform.

## Overview

Massive.com provides institutional-grade market data APIs for stocks, options, indices, currencies, and futures. This integration allows you to display real-time and historical market data in your dashboard.

## Prerequisites

1. **Massive.com API Key**: Sign up at [https://massive.com](https://massive.com) and create an API key
2. **Python Dependencies**: Install required packages

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install aiohttp
```

### 2. Get Your API Key

1. Go to [https://massive.com](https://massive.com)
2. Sign up for an account
3. Navigate to your API keys section
4. Create a new API key
5. Copy the API key

### 3. Set Environment Variable

**On macOS/Linux:**
```bash
export MASSIVE_API_KEY="your_api_key_here"
```

**On Windows (Command Prompt):**
```cmd
set MASSIVE_API_KEY=your_api_key_here
```

**On Windows (PowerShell):**
```powershell
$env:MASSIVE_API_KEY="your_api_key_here"
```

**Permanently (add to your shell profile):**
- macOS/Linux: Add to `~/.bashrc`, `~/.zshrc`, or `~/.profile`
- Windows: Add as a system environment variable

### 4. Verify Setup

Run the server and check the startup message:
```bash
python3 run_server.py
```

You should see:
```
✅ Massive.com API integration: ENABLED
```

If you see a warning, make sure:
- The API key is set correctly
- `aiohttp` is installed
- The API key is valid

## API Endpoints Used

The integration uses the following Massive.com API endpoints:

1. **Grouped Daily Bars** (`/aggs/grouped/locale/us/market/stocks/{date}`)
   - Gets daily price data for all stocks on a given date
   - Used for daily price jumps and dips

2. **Previous Close** (`/aggs/ticker/{ticker}/prev`)
   - Gets previous day's closing price for a ticker
   - Used for calculating price changes

3. **Snapshot** (`/snapshot/locale/us/markets/stocks/tickers/{ticker}`)
   - Gets current snapshot data for a ticker
   - Used for real-time price data

## Features

### ✅ Real Market Data
- Actual stock prices from major US exchanges
- Real-time and historical data
- Volume and price change calculations

### ✅ Fallback to Mock Data
- If API is unavailable, automatically falls back to mock data
- Ensures your application always works
- No breaking changes if API is down

### ✅ Caching
- Market data is cached for 60 seconds
- Reduces API calls and improves performance
- Automatic cache invalidation

### ✅ Error Handling
- Graceful error handling
- Logs errors for debugging
- Continues working even if some tickers fail

## Testing the Integration

### Test API Connection

```python
from services.massive_api import get_massive_client

client = get_massive_client()
data = await client.get_prev_close("AAPL")
print(data)
```

### Test Endpoints

1. **Daily Movements**: `GET http://localhost:8000/api/auth/market/daily-movements`
2. **Big Movers**: `GET http://localhost:8000/api/auth/market/big-movers`

## API Rate Limits

Massive.com has rate limits based on your subscription plan:
- **Free tier**: Limited requests per minute
- **Paid tiers**: Higher rate limits

The integration includes:
- Request caching (60 seconds)
- Error handling for rate limits
- Automatic fallback to mock data if rate limited

## Troubleshooting

### API Key Not Working
- Verify the API key is correct
- Check if the API key is active in your Massive.com dashboard
- Ensure the environment variable is set correctly

### Rate Limit Errors
- Check your API usage in the Massive.com dashboard
- Increase cache duration to reduce API calls
- Consider upgrading your subscription

### No Data Returned
- Check if markets are open (API may return limited data outside trading hours)
- Verify the date format (YYYY-MM-DD)
- Check API status at https://massive.com/status

### Import Errors
- Ensure `aiohttp` is installed: `pip install aiohttp`
- Check Python version (requires Python 3.7+)
- Verify the `services/` directory exists

## Cost Considerations

Massive.com offers:
- **Free tier**: Limited but sufficient for development
- **Paid tiers**: For production use with higher limits

Check [https://massive.com/pricing](https://massive.com/pricing) for current pricing.

## Next Steps

1. **Get API Key**: Sign up at Massive.com
2. **Set Environment Variable**: Export `MASSIVE_API_KEY`
3. **Restart Server**: The server will automatically use real data
4. **Monitor Usage**: Check your API usage in the Massive.com dashboard

## Support

- **Massive.com Docs**: [https://massive.com/docs](https://massive.com/docs)
- **API Status**: [https://massive.com/status](https://massive.com/status)
- **Support**: Contact Massive.com support for API issues

## Notes

- The API uses the Polygon.io domain (api.polygon.io) as Massive.com was formerly Polygon.io
- Market data is only available during trading hours for real-time data
- Historical data is available 24/7
- Weekends and holidays may have limited data availability

