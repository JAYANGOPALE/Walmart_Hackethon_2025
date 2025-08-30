// Walmart Trust Score Security - Popup Script
// Handles popup UI interactions and settings management

class PopupManager {
    constructor() {
        this.init();
    }

    init() {
        // Load settings when popup opens
        this.loadSettings();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Check API connection
        this.checkApiConnection();
        
        // Update trust score display
        this.updateTrustScore();
    }

    setupEventListeners() {
        // Save settings button
        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Enable/disable extension toggle
        document.getElementById('enable-extension').addEventListener('change', (e) => {
            this.toggleExtension(e.target.checked);
        });

        // Auto-save on input changes
        document.getElementById('api-url').addEventListener('input', () => {
            this.autoSaveSettings();
        });

        document.getElementById('auth-token').addEventListener('input', () => {
            this.autoSaveSettings();
        });
    }

    async loadSettings() {
        try {
            const response = await chrome.runtime.sendMessage({ action: 'getSettings' });
            
            if (response.success) {
                const settings = response.data;
                
                // Populate form fields
                document.getElementById('api-url').value = settings.apiBaseUrl || 'http://localhost:5000';
                document.getElementById('auth-token').value = settings.authToken || '';
                document.getElementById('enable-extension').checked = settings.extensionEnabled !== false;
                
                // Update status displays
                document.getElementById('extension-status').textContent = 
                    settings.extensionEnabled !== false ? 'Active' : 'Disabled';
                
                if (settings.lastUpdated) {
                    const date = new Date(settings.lastUpdated);
                    document.getElementById('last-updated').textContent = 
                        date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                }
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async saveSettings() {
        try {
            const settings = {
                apiBaseUrl: document.getElementById('api-url').value,
                authToken: document.getElementById('auth-token').value,
                extensionEnabled: document.getElementById('enable-extension').checked,
                lastUpdated: new Date().toISOString()
            };

            const response = await chrome.runtime.sendMessage({
                action: 'updateSettings',
                settings: settings
            });

            if (response.success) {
                this.showNotification('Settings saved successfully!', 'success');
                this.updateLastUpdated();
            } else {
                this.showNotification('Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showNotification('Error saving settings', 'error');
        }
    }

    async autoSaveSettings() {
        // Debounce auto-save
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveSettings();
        }, 1000);
    }

    async toggleExtension(enabled) {
        try {
            const settings = {
                extensionEnabled: enabled,
                lastUpdated: new Date().toISOString()
            };

            await chrome.runtime.sendMessage({
                action: 'updateSettings',
                settings: settings
            });

            document.getElementById('extension-status').textContent = enabled ? 'Active' : 'Disabled';
            this.updateLastUpdated();
            
            this.showNotification(
                enabled ? 'Extension enabled' : 'Extension disabled',
                'info'
            );
        } catch (error) {
            console.error('Failed to toggle extension:', error);
        }
    }

    async checkApiConnection() {
        try {
            const apiUrl = document.getElementById('api-url').value || 'http://localhost:5000';
            
            const response = await fetch(`${apiUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                document.getElementById('api-status').textContent = 'Online';
                document.getElementById('api-status').className = 'status-value status-online';
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            document.getElementById('api-status').textContent = 'Offline';
            document.getElementById('api-status').className = 'status-value status-offline';
            console.log('API connection check failed:', error);
        }
    }

    async updateTrustScore() {
        try {
            // Get current metadata for trust score calculation
            const metadata = await this.getCurrentMetadata();
            
            if (metadata) {
                const response = await chrome.runtime.sendMessage({
                    action: 'getTrustScore',
                    metadata: metadata
                });

                if (response.success) {
                    const data = response.data;
                    this.displayTrustScore(data.trustScore);
                    this.updateSecurityLevel(data.trustScore);
                }
            }
        } catch (error) {
            console.error('Failed to update trust score:', error);
            this.displayTrustScore(75); // Default fallback
        }
    }

    async getCurrentMetadata() {
        try {
            const metadata = {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform,
                screenResolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                url: 'popup'
            };

            // Try to get IP and location data
            try {
                const ipResponse = await fetch('https://ipapi.co/json/');
                const ipData = await ipResponse.json();
                metadata.ipAddress = ipData.ip;
                metadata.city = ipData.city;
                metadata.country = ipData.country_name;
            } catch (error) {
                console.log('IP detection failed in popup:', error);
            }

            return metadata;
        } catch (error) {
            console.error('Failed to get metadata:', error);
            return null;
        }
    }

    displayTrustScore(score) {
        const scoreElement = document.getElementById('current-trust-score');
        scoreElement.textContent = score;
        
        // Update color based on score
        scoreElement.className = 'trust-score';
        if (score >= 70) {
            scoreElement.classList.add('high');
        } else if (score >= 50) {
            scoreElement.classList.add('medium');
        } else {
            scoreElement.classList.add('low');
        }
    }

    updateSecurityLevel(score) {
        const levelElement = document.getElementById('security-level');
        
        if (score >= 80) {
            levelElement.textContent = 'High Security';
            levelElement.className = 'status-value status-online';
        } else if (score >= 60) {
            levelElement.textContent = 'Medium Security';
            levelElement.className = 'status-value';
        } else if (score >= 40) {
            levelElement.textContent = 'Low Security';
            levelElement.className = 'status-value status-offline';
        } else {
            levelElement.textContent = 'Critical';
            levelElement.className = 'status-value status-offline';
        }
    }

    updateLastUpdated() {
        const now = new Date();
        document.getElementById('last-updated').textContent = 
            now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
    }

    showNotification(message, type = 'info') {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
        
        // Add CSS animations
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PopupManager();
}); 