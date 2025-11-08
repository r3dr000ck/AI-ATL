#!/bin/bash
# Setup script for Finnhub API key
# This script helps you set the API key permanently

API_KEY="d47fd39r01qh8nncdtb0d47fd39r01qh8nncdtbg"

echo "🔑 Setting up Finnhub API Key..."
echo ""

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
    # Also check .bash_profile on macOS
    if [ -f "$HOME/.bash_profile" ]; then
        SHELL_RC="$HOME/.bash_profile"
    fi
else
    SHELL_RC="$HOME/.profile"
    SHELL_NAME="default"
fi

echo "Detected shell: $SHELL_NAME"
echo "Profile file: $SHELL_RC"
echo ""

# Check if API key already exists in the file
if grep -q "export FINNHUB_API_KEY=" "$SHELL_RC" 2>/dev/null; then
    echo "⚠️  FINNHUB_API_KEY already exists in $SHELL_RC"
    echo "Updating existing key..."
    # Use sed to update (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^export FINNHUB_API_KEY=.*|export FINNHUB_API_KEY=\"$API_KEY\"|" "$SHELL_RC"
    else
        # Linux
        sed -i "s|^export FINNHUB_API_KEY=.*|export FINNHUB_API_KEY=\"$API_KEY\"|" "$SHELL_RC"
    fi
    echo "✅ Updated FINNHUB_API_KEY in $SHELL_RC"
else
    echo "Adding FINNHUB_API_KEY to $SHELL_RC..."
    echo "" >> "$SHELL_RC"
    echo "# Finnhub API Key for market news" >> "$SHELL_RC"
    echo "export FINNHUB_API_KEY=\"$API_KEY\"" >> "$SHELL_RC"
    echo "✅ Added FINNHUB_API_KEY to $SHELL_RC"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Finnhub API Key setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Run: source $SHELL_RC"
echo "   2. Or restart your terminal"
echo "   3. Verify: echo \$FINNHUB_API_KEY"
echo ""
echo "🚀 After setting up, restart your server to use real market news!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

