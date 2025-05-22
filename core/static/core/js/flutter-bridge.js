/**
 * Flutter WebView Bridge Integration
 * Provides integration between web frontend and Flutter app for NFC operations
 */

// Global object to store bridge state and callbacks
window.TapNexBridgeState = {
    isFlutterApp: false,
    onCardRead: null
};

/**
 * Request NFC scanning through Flutter bridge
 * Falls back to Web NFC API if not in Flutter app
 */
function requestNFC() {
    // Check if running in Flutter WebView
    if (window.TapNexBridge) {
        console.log('Requesting NFC scan through Flutter bridge');
        window.TapNexBridge.postMessage('scanCard');
        return true;
    } else {
        console.log('TapNexBridge not available - not running in Flutter app');
        alert('NFC scanning is only available in the TapNex mobile app');
        return false;
    }
}

/**
 * Handle card UID received from Flutter
 * @param {string} uid - The UID of the scanned NFC card
 */
function handleCardUID(uid) {
    console.log('Received card UID from Flutter:', uid);
    
    // If we have an existing NFC system, integrate with it
    if (window.nfcReader && window.nfcUIHandler) {
        // Simulate a card reading with the UID from Flutter
        window.nfcReader.simulateReading(uid);
    } else {
        // Basic handling if NFC system is not available
        console.log('Processing card UID:', uid);
        // You can add custom handling here
    }
}

// Initialize bridge detection
document.addEventListener('DOMContentLoaded', function() {
    // Check if running in Flutter WebView
    if (window.TapNexBridge) {
        console.log('TapNexBridge detected - running in Flutter app');
        window.TapNexBridgeState.isFlutterApp = true;
    }
});
