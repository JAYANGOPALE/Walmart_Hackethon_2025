// Walmart Trust Score Security - Content Script
// Injects into login pages to capture metadata and validate trust scores

class TrustScoreSecurity {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000';
        this.isLoginPage = this.detectLoginPage();
        this.trustBanner = null;
        this.loginForm = null;
        this.init();
    }

    init() {
        try {
            if (this.isLoginPage) {
                console.log('Walmart Trust Security: Login page detected, initializing...');
                this.setupTrustBanner();
                this.interceptLoginForm();
                this.captureMetadata();
            } else {
                console.log('Walmart Trust Security: Not a login page, skipping initialization');
            }
        } catch (error) {
            console.error('Walmart Trust Security: Initialization error:', error);
        }
    }

    detectLoginPage() {
        // Detect if this is a login page
        const url = window.location.href;
        const hasLoginForm = document.querySelector('form[action*="login"], form input[type="password"]');
        const isLoginUrl = url.includes('/login') || url.includes('login') || url.includes('signin');
        
        return hasLoginForm || isLoginUrl;
    }

    async captureMetadata() {
        try {
            const metadata = {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform,
                screenResolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                referrer: document.referrer,
                url: window.location.href
            };

            // Get geolocation if available
            if (navigator.geolocation) {
                try {
                    const position = await this.getCurrentPosition();
                    metadata.latitude = position.coords.latitude;
                    metadata.longitude = position.coords.longitude;
                } catch (error) {
                    console.log('Geolocation not available:', error);
                }
            }

            // Get IP address via external service
            try {
                const ipResponse = await fetch('https://ipapi.co/json/');
                const ipData = await ipResponse.json();
                metadata.ipAddress = ipData.ip;
                metadata.city = ipData.city;
                metadata.country = ipData.country_name;
                metadata.region = ipData.region;
                metadata.isp = ipData.org;
            } catch (error) {
                console.log('IP detection failed:', error);
            }

            // Store metadata for later use
            try {
                chrome.storage.local.set({ 'loginMetadata': metadata });
                console.log('Walmart Trust Security: Metadata stored successfully');
            } catch (error) {
                console.error('Walmart Trust Security: Failed to store metadata:', error);
            }
            
            return metadata;
        } catch (error) {
            console.error('Error capturing metadata:', error);
            return null;
        }
    }

    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            });
        });
    }

    setupTrustBanner() {
        // Create trust status banner
        this.trustBanner = document.createElement('div');
        this.trustBanner.id = 'walmart-trust-banner';
        this.trustBanner.innerHTML = `
            <div class="trust-banner-content">
                <div class="trust-status">
                    <span class="status-icon">🔒</span>
                    <span class="status-text">Validating security...</span>
                </div>
                <div class="trust-details">
                    <div class="detail-item">
                        <span class="label">Location:</span>
                        <span class="value" id="location-value">Detecting...</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Trust Score:</span>
                        <span class="value" id="trust-score">Calculating...</span>
                    </div>
                </div>
            </div>
        `;

        // Insert banner at the top of the page
        document.body.insertBefore(this.trustBanner, document.body.firstChild);
        
        // Apply styles
        this.applyBannerStyles();
    }

    applyBannerStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #walmart-trust-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 12px 20px;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                border-bottom: 3px solid #ffc107;
            }
            
            .trust-banner-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .trust-status {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-icon {
                font-size: 18px;
            }
            
            .status-text {
                font-weight: 500;
                font-size: 14px;
            }
            
            .trust-details {
                display: flex;
                gap: 20px;
            }
            
            .detail-item {
                display: flex;
                gap: 5px;
                font-size: 12px;
            }
            
            .label {
                opacity: 0.8;
            }
            
            .value {
                font-weight: 500;
            }
            
            .trust-score-high {
                color: #4caf50;
            }
            
            .trust-score-medium {
                color: #ff9800;
            }
            
            .trust-score-low {
                color: #f44336;
            }
            
            .trust-banner-warning {
                background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
                border-bottom-color: #ff5722;
            }
            
            .trust-banner-success {
                background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%);
                border-bottom-color: #8bc34a;
            }
        `;
        document.head.appendChild(style);
    }

    interceptLoginForm() {
        // Find login form
        this.loginForm = document.querySelector('form[action*="login"], form input[type="password"]');
        
        if (this.loginForm) {
            // Add event listener to form submission
            this.loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLoginAttempt();
            });

            // Also intercept password field changes
            const passwordField = this.loginForm.querySelector('input[type="password"]');
            if (passwordField) {
                passwordField.addEventListener('input', () => {
                    this.updateTrustStatus('Preparing security validation...');
                });
            }
        }
    }

    async handleLoginAttempt() {
        try {
            this.updateTrustStatus('Validating security credentials...');
            
            // Get stored metadata
            const metadata = await this.getStoredMetadata();
            if (!metadata) {
                this.updateTrustStatus('Error: Could not capture security data', 'error');
                return;
            }

            // Send trust score request
            const trustResponse = await this.requestTrustScore(metadata);
            
            if (trustResponse.success) {
                const { trustScore, isSuspicious, requireEmailVerification } = trustResponse;
                
                this.updateTrustScore(trustScore);
                
                if (isSuspicious) {
                    this.showSecurityAlert('Suspicious login detected. Access blocked.');
                    return;
                }
                
                if (requireEmailVerification) {
                    this.showSecurityAlert('Additional verification required. Check your email.');
                    // Continue with form submission but show warning
                    this.submitFormWithWarning();
                } else {
                    this.updateTrustStatus('Security validation passed', 'success');
                    // Allow normal form submission
                    setTimeout(() => {
                        this.submitForm();
                    }, 1000);
                }
            } else {
                this.updateTrustStatus('Security validation failed', 'error');
                this.showSecurityAlert('Unable to validate security. Please try again.');
            }
            
        } catch (error) {
            console.error('Login attempt error:', error);
            this.updateTrustStatus('Security validation error', 'error');
            this.showSecurityAlert('Security validation failed. Please try again.');
        }
    }

    async getStoredMetadata() {
        return new Promise((resolve) => {
            chrome.storage.local.get(['loginMetadata'], (result) => {
                resolve(result.loginMetadata);
            });
        });
    }

    async requestTrustScore(metadata) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trust-score`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + await this.getAuthToken()
                },
                body: JSON.stringify(metadata)
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Trust score request failed:', error);
            return { success: false, error: error.message };
        }
    }

    async getAuthToken() {
        // Get stored auth token or generate a simple one for demo
        return new Promise((resolve) => {
            chrome.storage.local.get(['authToken'], (result) => {
                resolve(result.authToken || 'demo-token-123');
            });
        });
    }

    updateTrustStatus(message, type = 'info') {
        if (this.trustBanner) {
            const statusText = this.trustBanner.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = message;
            }
            
            // Update banner appearance based on type
            this.trustBanner.className = `trust-banner-${type}`;
        }
    }

    updateTrustScore(score) {
        const scoreElement = document.getElementById('trust-score');
        if (scoreElement) {
            scoreElement.textContent = `${score}/100`;
            
            // Update color based on score
            scoreElement.className = 'value';
            if (score >= 70) {
                scoreElement.classList.add('trust-score-high');
            } else if (score >= 50) {
                scoreElement.classList.add('trust-score-medium');
            } else {
                scoreElement.classList.add('trust-score-low');
            }
        }
    }

    showSecurityAlert(message) {
        // Create alert overlay
        const alert = document.createElement('div');
        alert.id = 'walmart-security-alert';
        alert.innerHTML = `
            <div class="alert-content">
                <div class="alert-icon">⚠️</div>
                <div class="alert-message">${message}</div>
                <button class="alert-button" onclick="this.parentElement.parentElement.remove()">OK</button>
            </div>
        `;
        
        // Apply alert styles
        const style = document.createElement('style');
        style.textContent = `
            #walmart-security-alert {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10001;
            }
            
            .alert-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            
            .alert-icon {
                font-size: 48px;
                margin-bottom: 20px;
            }
            
            .alert-message {
                font-size: 16px;
                margin-bottom: 20px;
                color: #333;
            }
            
            .alert-button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .alert-button:hover {
                background: #0056b3;
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(alert);
    }

    submitFormWithWarning() {
        // Submit form but show warning
        this.updateTrustStatus('Proceeding with additional verification required', 'warning');
        setTimeout(() => {
            this.submitForm();
        }, 2000);
    }

    submitForm() {
        if (this.loginForm) {
            // Create a new submit event to trigger form submission
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            this.loginForm.dispatchEvent(submitEvent);
        }
    }
}

// Initialize the trust score security system
const trustSecurity = new TrustScoreSecurity(); 