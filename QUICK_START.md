# Quick Start - Massive.com API Key Setup

## Your API Key is Ready!

Your Massive.com API key has been configured. Here's how to use it:

## Option 1: Use Setup Script (Recommended)

Run the setup script to make the API key permanent:

```bash
./setup_api_key.sh
source ~/.zshrc  # or ~/.bashrc depending on your shell
```

## Option 2: Manual Setup

### For Current Session Only:
```bash
export MASSIVE_API_KEY="nqUIVniktu50wf4S_d_F069PYVj8DbrF"
```

### For Permanent Setup (macOS/Linux):
Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export MASSIVE_API_KEY="nqUIVniktu50wf4S_d_F069PYVj8DbrF"
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

## Verify API Key is Set

```bash
echo $MASSIVE_API_KEY
# Should show your API key (or run the setup script)
```

## Start the Server

```bash
python3 run_server.py
```

You should see:
```
✅ Massive.com API integration: ENABLED
```

## Test the Integration

```bash
# Test daily movements endpoint
curl http://localhost:8000/api/auth/market/daily-movements

# Test big movers endpoint
curl http://localhost:8000/api/auth/market/big-movers
```

## Security Notes

- ✅ API key is stored as environment variable (not in code)
- ✅ `.env` files are in `.gitignore` (won't be committed)
- ✅ API key is never hard-coded in source files

## Troubleshooting

If you see "Massive.com API integration: UNAVAILABLE":
1. Make sure `aiohttp` is installed: `pip install aiohttp`
2. Verify API key is set: `echo $MASSIVE_API_KEY`
3. Restart your terminal or run `source ~/.zshrc`

If API calls fail:
1. Check your API key is valid at https://massive.com
2. Verify you have API credits/quota
3. Check API status: https://massive.com/status

