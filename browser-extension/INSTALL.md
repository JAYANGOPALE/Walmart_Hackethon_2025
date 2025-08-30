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
