#!/bin/bash

# Build script for browser extension

echo "🔧 Building Walmart Trust Score Security Extension..."

# Create build directory
mkdir -p build

# Copy files to build directory
cp manifest.json build/
cp content.js build/
cp background.js build/
cp popup.html build/
cp popup.js build/
cp content.css build/
cp -r icons build/

# Create ZIP file for Chrome Web Store
if command -v zip &> /dev/null; then
    echo "Creating ZIP file for Chrome Web Store..."
    cd build
    zip -r ../walmart-trust-extension.zip .
    cd ..
    echo "✅ Extension packaged: walmart-trust-extension.zip"
else
    echo "⚠️  zip command not found. Please install zip to create distribution package."
fi

echo "✅ Build complete!"
