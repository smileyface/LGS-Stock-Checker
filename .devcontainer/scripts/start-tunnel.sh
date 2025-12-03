#!/bin/bash

# Define the tunnel name - Change this if you want a different name on your Chromebook
TUNNEL_NAME="lgs-stock-container"

echo "--------------------------------------------------"
echo "   Setting up Direct Container Tunnel: $TUNNEL_NAME"
echo "--------------------------------------------------"

# Download the specific CLI for Linux x64
if [ ! -f "./code-cli" ]; then
    echo "Downloading VS Code CLI..."
    curl -Lk 'https://update.code.visualstudio.com/latest/cli-linux-x64/stable' --output vscode_cli.tar.gz
    
    echo "Extracting CLI..."
    tar -xf vscode_cli.tar.gz
    rm vscode_cli.tar.gz
    chmod +x code
    mv code code-cli
fi

echo ""
echo "Starting Tunnel..."
echo "1. If this is your first time, you will be asked to authenticate via GitHub."
echo "2. On your Chromebook, look for the machine named '$TUNNEL_NAME' in the Remote Tunnels list."
echo "--------------------------------------------------"

# Run the tunnel
./code-cli tunnel --name "$TUNNEL_NAME"