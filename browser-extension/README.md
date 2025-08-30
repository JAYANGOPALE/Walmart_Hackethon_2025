# Walmart Trust Score Security - Browser Extension

A Chrome/Firefox browser extension that provides enhanced security for Walmart employee portal logins using trust score validation.

## Features

- **Real-time Trust Score Calculation**: Analyzes login metadata to determine security risk
- **Geolocation Tracking**: Monitors login locations for suspicious activity
- **IP Address Analysis**: Tracks IP changes and geographic anomalies
- **User Agent Monitoring**: Detects unusual browser/device patterns
- **Time-based Security**: Analyzes login times for business hour compliance
- **Visual Security Banner**: Shows trust status and security level on login pages
- **Automatic Blocking**: Blocks suspicious logins and triggers 2FA/email verification
- **Secure API Communication**: Uses JWT tokens for secure backend communication

## Architecture

```
Browser Extension
├── manifest.json          # Extension configuration (Manifest V3)
├── content.js            # DOM injection and trust logic
├── background.js         # API communication and background tasks
├── popup.html           # Extension popup UI
├── popup.js             # Popup interaction logic
├── content.css          # Trust banner and alert styles
└── icons/               # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Installation

### Prerequisites

1. **Flask Backend**: Ensure your Flask + Supabase Trust Score Security System is running
2. **API Endpoints**: The backend must have the API endpoints from `api_endpoints.py`
3. **JWT Dependencies**: Install PyJWT for token authentication

```bash
pip install PyJWT
```

### Backend Setup

1. **Add API Endpoints**: Copy the contents of `api_endpoints.py` to your Flask app
2. **Update Dependencies**: Add JWT to your requirements
3. **Configure JWT**: Update the `JWT_SECRET_KEY` in production

### Extension Installation

#### Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. The extension will appear in your extensions list

#### Firefox

1. Open Firefox and navigate to `about:debugging`
2. Click "This Firefox" tab
3. Click "Load Temporary Add-on"
4. Select the `manifest.json` file from the `browser-extension` folder
5. The extension will be loaded temporarily

#### Production Deployment

For production deployment, you'll need to:

1. **Package the Extension**:
   ```bash
   # Create a ZIP file for Chrome Web Store
   zip -r walmart-trust-extension.zip browser-extension/
   ```

2. **Submit to Chrome Web Store**:
   - Create a developer account
   - Upload the ZIP file
   - Provide store listing details
   - Wait for review and approval

3. **Firefox Add-ons**:
   - Submit to Firefox Add-ons store
   - Follow Mozilla's submission guidelines

## Configuration

### Extension Settings

The extension can be configured through the popup interface:

- **API Base URL**: Point to your Flask backend (default: `http://localhost:5000`)
- **Auth Token**: JWT token for API authentication
- **Enable/Disable**: Toggle extension functionality

### Backend Configuration

Update your Flask app configuration:

```python
# In config.py
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-secret-key'
API_CORS_ORIGINS = ['chrome-extension://*', 'moz-extension://*']
```

### Environment Variables

```bash
# Production environment variables
export JWT_SECRET_KEY="your-secure-jwt-secret"
export FLASK_ENV="production"
export DATABASE_URL="your-database-url"
```

## Usage

### For End Users

1. **Install the Extension**: Follow installation instructions above
2. **Navigate to Login Page**: Visit any Walmart employee portal login page
3. **Trust Banner Appears**: A security banner will show at the top of the page
4. **Automatic Validation**: The extension captures metadata and validates security
5. **Security Actions**:
   - **High Trust (≥70)**: Normal login allowed
   - **Medium Trust (50-69)**: Login allowed with monitoring
   - **Low Trust (<50)**: Email verification required
   - **Suspicious Activity**: Login blocked with alert

### For Administrators

1. **Monitor Logs**: Check Flask application logs for security events
2. **Review Trust Scores**: Access the admin dashboard to view trust score analytics
3. **Configure Thresholds**: Adjust trust score thresholds in the ML model
4. **Update Extension**: Deploy new versions through browser stores

## API Endpoints

The extension communicates with these backend endpoints:

### Health Check
```
GET /api/health
Response: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### Authentication
```
POST /api/auth/token
Response: {"success": true, "token": "jwt-token", "expires_in": 86400}
```

### Trust Score Calculation
```
POST /api/trust-score
Headers: Authorization: Bearer <jwt-token>
Body: {
  "timestamp": "2024-01-01T12:00:00Z",
  "userAgent": "Mozilla/5.0...",
  "ipAddress": "192.168.1.1",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "city": "New York",
  "country": "United States"
}
Response: {
  "success": true,
  "trust_score": 75,
  "is_suspicious": false,
  "require_email_verification": false
}
```

### Login Validation
```
POST /api/validate-login
Headers: Authorization: Bearer <jwt-token>
Body: {
  "username": "employee123",
  "password": "password123",
  "metadata": {...}
}
Response: {
  "success": true,
  "trust_score": 75,
  "is_suspicious": false,
  "require_email_verification": false,
  "message": "Login validated successfully"
}
```

## Security Features

### Data Collection
- **IP Address**: For geographic analysis
- **User Agent**: For device fingerprinting
- **Geolocation**: For location-based security
- **Timestamp**: For time-based analysis
- **Screen Resolution**: For device consistency
- **Timezone**: For timezone-based validation

### Trust Score Factors
- **Geographic Distance**: Unusual location changes
- **Time Patterns**: Non-business hour logins
- **Failed Attempts**: Previous suspicious activity
- **API Rate**: Frequency of login attempts
- **Device Consistency**: Browser/device patterns

### Security Actions
- **Block Suspicious Logins**: Automatic blocking of high-risk attempts
- **Email Verification**: Required for medium-risk logins
- **Alert Notifications**: Real-time security alerts
- **Audit Logging**: Comprehensive security event logging

## Development

### Local Development

1. **Start Flask Backend**:
   ```bash
   python app.py
   ```

2. **Load Extension**:
   - Follow installation instructions above
   - Use developer mode for testing

3. **Test on Local Login Page**:
   - Navigate to `http://localhost:5000/login`
   - Check browser console for extension logs
   - Verify trust banner appears

### Debugging

1. **Extension Debugging**:
   - Open Chrome DevTools
   - Go to Extensions tab
   - Click "background page" for background script debugging
   - Use console.log in content scripts

2. **Backend Debugging**:
   - Check Flask application logs
   - Monitor API endpoint responses
   - Verify database entries

### Testing

1. **Unit Tests**:
   ```bash
   python -m pytest tests/
   ```

2. **Integration Tests**:
   - Test extension with real login pages
   - Verify API communication
   - Check security event logging

## Deployment

### Production Checklist

- [ ] Update JWT secret key
- [ ] Configure CORS for production domains
- [ ] Set up SSL certificates
- [ ] Configure database for production
- [ ] Set up monitoring and logging
- [ ] Test extension on production login pages
- [ ] Submit to browser stores

### Monitoring

1. **Application Logs**: Monitor Flask application logs
2. **Security Events**: Track security event logs
3. **Trust Score Analytics**: Monitor trust score distributions
4. **Extension Usage**: Track extension installation and usage

## Troubleshooting

### Common Issues

1. **Extension Not Loading**:
   - Check manifest.json syntax
   - Verify file permissions
   - Check browser console for errors

2. **API Connection Failed**:
   - Verify Flask backend is running
   - Check API endpoint URLs
   - Verify JWT token configuration

3. **Trust Banner Not Appearing**:
   - Check content script injection
   - Verify login page detection
   - Check browser console for errors

4. **Security Alerts Not Working**:
   - Verify alert styles are loaded
   - Check DOM manipulation permissions
   - Test on different login pages

### Debug Commands

```bash
# Check Flask backend
curl http://localhost:5000/api/health

# Test JWT token
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/trust-score

# Check extension storage
# In browser console: chrome.storage.local.get(null, console.log)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Version History

- **v1.0.0**: Initial release with basic trust score functionality
- **v1.1.0**: Added geolocation support and enhanced security features
- **v1.2.0**: Improved UI and added popup configuration
- **v1.3.0**: Added JWT authentication and production deployment support 