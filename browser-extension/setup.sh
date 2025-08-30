#!/bin/bash

# Walmart Trust Score Security - Browser Extension Setup Script

echo "🔒 Setting up Walmart Trust Score Security Browser Extension..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manifest.json" ]; then
    print_error "Please run this script from the browser-extension directory"
    exit 1
fi

print_status "Starting browser extension setup..."

# Create icons directory if it doesn't exist
if [ ! -d "icons" ]; then
    print_status "Creating icons directory..."
    mkdir -p icons
fi

# Check if icons exist
if [ ! -f "icons/icon16.png" ] || [ ! -f "icons/icon48.png" ] || [ ! -f "icons/icon128.png" ]; then
    print_warning "Icon files are missing. Creating placeholder icons..."
    
    # Check if ImageMagick is available
    if command -v convert &> /dev/null; then
        print_status "Creating placeholder icons with ImageMagick..."
        convert -size 16x16 xc:#0071ce -fill white -gravity center -pointsize 12 -annotate +0+0 "W" icons/icon16.png
        convert -size 48x48 xc:#0071ce -fill white -gravity center -pointsize 36 -annotate +0+0 "W" icons/icon48.png
        convert -size 128x128 xc:#0071ce -fill white -gravity center -pointsize 96 -annotate +0+0 "W" icons/icon128.png
        print_success "Placeholder icons created successfully"
    else
        print_warning "ImageMagick not found. Please create icon files manually:"
        echo "  - icons/icon16.png (16x16 pixels)"
        echo "  - icons/icon48.png (48x48 pixels)"
        echo "  - icons/icon128.png (128x128 pixels)"
        echo ""
        echo "You can use any image editing software or online tools to create these icons."
    fi
else
    print_success "Icon files found"
fi

# Validate manifest.json
print_status "Validating manifest.json..."
if python3 -c "import json; json.load(open('manifest.json'))" 2>/dev/null; then
    print_success "manifest.json is valid JSON"
else
    print_error "manifest.json contains invalid JSON"
    exit 1
fi

# Check required files
required_files=("manifest.json" "content.js" "background.js" "popup.html" "popup.js" "content.css")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    print_success "All required files found"
else
    print_error "Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

# Create a simple test page for development
print_status "Creating test page for development..."
cat > test-page.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Walmart Employee Portal - Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .login-form {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #0071ce;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0056b3;
        }
        h1 {
            color: #0071ce;
            text-align: center;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <div class="login-form">
        <h1>🔒 Walmart Employee Portal</h1>
        <form action="/login" method="post">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>
EOF

print_success "Test page created: test-page.html"

# Create installation instructions
print_status "Creating installation instructions..."
cat > INSTALL.md << 'EOF'
# Quick Installation Guide

## Chrome Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this folder (`browser-extension`)
5. The extension will appear in your extensions list

## Firefox Installation

1. Open Firefox and go to `about:debugging`
2. Click "This Firefox" tab
3. Click "Load Temporary Add-on"
4. Select `manifest.json` from this folder
5. The extension will be loaded temporarily

## Testing

1. Start your Flask backend: `python app.py`
2. Open `test-page.html` in your browser
3. The trust banner should appear at the top
4. Try submitting the form to test the extension

## Configuration

1. Click the extension icon in your browser toolbar
2. Configure the API URL (default: http://localhost:5000)
3. Set your auth token if required
4. Enable/disable the extension as needed

## Troubleshooting

- Check browser console for errors
- Verify Flask backend is running
- Ensure API endpoints are accessible
- Check extension permissions in browser settings
EOF

print_success "Installation guide created: INSTALL.md"

# Create a simple build script
print_status "Creating build script..."
cat > build.sh << 'EOF'
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
EOF

chmod +x build.sh
print_success "Build script created: build.sh"

# Final status
echo ""
print_success "Browser extension setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Install the extension in your browser (see INSTALL.md)"
echo "2. Start your Flask backend: python app.py"
echo "3. Test the extension on test-page.html"
echo "4. Configure API settings in the extension popup"
echo ""
echo "🔧 Available scripts:"
echo "- ./build.sh - Package extension for distribution"
echo "- ./setup.sh - Re-run setup (this script)"
echo ""
echo "📚 Documentation:"
echo "- README.md - Complete documentation"
echo "- INSTALL.md - Quick installation guide"
echo ""

print_success "Setup completed successfully! 🎉" 