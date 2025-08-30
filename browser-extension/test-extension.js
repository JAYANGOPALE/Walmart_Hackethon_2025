// Test script for Walmart Trust Security Extension
// Run this in the browser console to test extension functionality

console.log('🧪 Testing Walmart Trust Security Extension...');

// Test 1: Check if extension is loaded
if (typeof chrome !== 'undefined' && chrome.runtime) {
    console.log('✅ Chrome extension API available');
} else {
    console.log('❌ Chrome extension API not available');
}

// Test 2: Check if content script is running
if (document.getElementById('walmart-trust-banner')) {
    console.log('✅ Trust banner found on page');
} else {
    console.log('❌ Trust banner not found on page');
}

// Test 3: Check if login form is detected
const loginForm = document.querySelector('form[action*="login"], form input[type="password"]');
if (loginForm) {
    console.log('✅ Login form detected');
} else {
    console.log('❌ Login form not detected');
}

// Test 4: Check extension storage
chrome.storage.local.get(['extensionEnabled', 'apiBaseUrl'], (result) => {
    console.log('📦 Extension settings:', result);
});

// Test 5: Test API connection
fetch('http://localhost:5000/api/health')
    .then(response => response.json())
    .then(data => {
        console.log('✅ API connection successful:', data);
    })
    .catch(error => {
        console.log('❌ API connection failed:', error.message);
    });

console.log('🧪 Extension test completed'); 