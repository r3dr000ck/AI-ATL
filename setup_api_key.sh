#!/bin/bash
# Setup script for Massive.com API key
# This script helps you set the API key permanently

API_KEY="nqUIVniktu50wf4S_d_F069PYVj8DbrF"

echo "🔑 Setting up Massive.com API Key..."
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
if grep -q "MASSIVE_API_KEY" "$SHELL_RC" 2>/dev/null; then
    echo "⚠️  MASSIVE_API_KEY already exists in $SHELL_RC"
    echo "   Updating existing entry..."
    # Remove old entry
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' '/export MASSIVE_API_KEY=/d' "$SHELL_RC"
    else
        # Linux
        sed -i '/export MASSIVE_API_KEY=/d' "$SHELL_RC"
    fi
fi

# Add API key to shell profile
echo "" >> "$SHELL_RC"
echo "# Massive.com API Key" >> "$SHELL_RC"
echo "export MASSIVE_API_KEY=\"$API_KEY\"" >> "$SHELL_RC"

echo "✅ API key has been added to $SHELL_RC"
echo ""
echo "To use it in the current session, run:"
echo "  source $SHELL_RC"
echo ""
echo "Or open a new terminal window."
echo ""
echo "To verify, run:"
echo "  echo \$MASSIVE_API_KEY"

