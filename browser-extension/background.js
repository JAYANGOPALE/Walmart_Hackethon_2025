// Walmart Trust Score Security - Background Service Worker
// Handles API communication and background tasks

class TrustScoreBackground {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000';
        this.authToken = null;
        this.init();
    }

    init() {
        // Listen for extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.handleFirstInstall();
            }
        });

        // Listen for messages from content script
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async response
        });

        // Listen for tab updates to check for login pages
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.checkForLoginPage(tabId, tab.url);
            }
        });

        // Initialize auth token
        this.initializeAuthToken();
    }

    async handleFirstInstall() {
        console.log('Walmart Trust Score Security extension installed');
        
        // Set default settings
        await chrome.storage.local.set({
            'extensionEnabled': true,
            'apiBaseUrl': this.apiBaseUrl,
            'authToken': 'demo-token-123',
            'lastUpdated': new Date().toISOString()
        });

        // Log installation instead of showing notification
        console.log('Extension installed successfully. Security monitoring is now active.');
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            console.log('Background received message:', request.action);
            
            switch (request.action) {
                case 'getTrustScore':
                    const trustScore = await this.getTrustScore(request.metadata);
                    sendResponse({ success: true, data: trustScore });
                    break;

                case 'validateLogin':
                    const validation = await this.validateLogin(request.credentials, request.metadata);
                    sendResponse({ success: true, data: validation });
                    break;

                case 'getAuthToken':
                    const token = await this.getAuthToken();
                    sendResponse({ success: true, data: token });
                    break;

                case 'updateSettings':
                    await this.updateSettings(request.settings);
                    sendResponse({ success: true });
                    break;

                case 'getSettings':
                    const settings = await this.getSettings();
                    sendResponse({ success: true, data: settings });
                    break;

                default:
                    console.warn('Unknown action received:', request.action);
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background message handler error:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    async checkForLoginPage(tabId, url) {
        // Check if URL matches login page patterns
        const loginPatterns = [
            /\/login/i,
            /\/signin/i,
            /\/auth/i,
            /login\.html/i,
            /signin\.html/i
        ];

        const isLoginPage = loginPatterns.some(pattern => pattern.test(url));
        
        if (isLoginPage) {
            // Inject content script if not already injected
            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: ['content.js']
                });
                console.log(`Content script injected for tab ${tabId}`);
            } catch (error) {
                // Script might already be injected or tab might not be accessible
                console.log(`Content script injection skipped for tab ${tabId}:`, error.message);
            }
        }
    }

    async getTrustScore(metadata) {
        try {
            const authToken = await this.getAuthToken();
            
            const response = await fetch(`${this.apiBaseUrl}/api/trust-score`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(metadata)
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    trustScore: data.trust_score,
                    isSuspicious: data.is_suspicious,
                    requireEmailVerification: data.require_email_verification,
                    reason: data.reason || null
                };
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Trust score request failed:', error);
            // Return fallback trust score
            return {
                trustScore: 75, // Default high trust score
                isSuspicious: false,
                requireEmailVerification: false,
                reason: 'API unavailable, using default trust score'
            };
        }
    }

    async validateLogin(credentials, metadata) {
        try {
            const authToken = await this.getAuthToken();
            
            const response = await fetch(`${this.apiBaseUrl}/api/validate-login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    username: credentials.username,
                    password: credentials.password,
                    metadata: metadata
                })
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    success: data.success,
                    trustScore: data.trust_score,
                    isSuspicious: data.is_suspicious,
                    requireEmailVerification: data.require_email_verification,
                    message: data.message
                };
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Login validation failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getAuthToken() {
        return new Promise((resolve) => {
            chrome.storage.local.get(['authToken'], (result) => {
                resolve(result.authToken || 'demo-token-123');
            });
        });
    }

    async initializeAuthToken() {
        const token = await this.getAuthToken();
        this.authToken = token;
    }

    async updateSettings(settings) {
        await chrome.storage.local.set(settings);
        
        // Update auth token if provided
        if (settings.authToken) {
            this.authToken = settings.authToken;
        }
    }

    async getSettings() {
        return new Promise((resolve) => {
            chrome.storage.local.get([
                'extensionEnabled',
                'apiBaseUrl',
                'authToken',
                'lastUpdated'
            ], (result) => {
                resolve(result);
            });
        });
    }

    // Utility method to make API requests with retry logic
    async makeApiRequest(url, options, retries = 3) {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(url, options);
                return response;
            } catch (error) {
                if (i === retries - 1) {
                    throw error;
                }
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }

    // Method to log security events
    async logSecurityEvent(eventType, details) {
        try {
            const authToken = await this.getAuthToken();
            
            await fetch(`${this.apiBaseUrl}/api/security-events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    event_type: eventType,
                    details: details,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to log security event:', error);
        }
    }
}

// Initialize the background service worker
const background = new TrustScoreBackground(); 