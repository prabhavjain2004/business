/**
 * NFC Card Reader System
 * 
 * This script provides functionality for detecting and reading NFC cards
 * using the Web NFC API. It includes fallback methods for browsers that
 * don't support the Web NFC API.
 */

class NFCReader {
    constructor(options = {}) {
        this.options = {
            onReading: null,
            onError: null,
            onSuccess: null,
            onNotSupported: null,
            ...options
        };
        
        this.isReading = false;
        this.checkNFCSupport();
    }

    /**
     * Check if the Web NFC API is supported in the current browser
     */
    checkNFCSupport() {
        if ('NDEFReader' in window) {
            this.nfcSupported = true;
            console.log('Web NFC API is supported in this browser.');
        } else {
            this.nfcSupported = false;
            console.warn('Web NFC API is not supported in this browser.');
            if (typeof this.options.onNotSupported === 'function') {
                this.options.onNotSupported();
            }
        }
        return this.nfcSupported;
    }

    /**
     * Start reading NFC cards
     */
    async startReading() {
        if (!this.nfcSupported) {
            console.warn('NFC is not supported in this browser.');
            return false;
        }

        if (this.isReading) {
            console.warn('NFC reader is already active.');
            return true;
        }

        try {
            this.reader = new NDEFReader();
            await this.reader.scan();
            
            this.reader.addEventListener("reading", ({ message, serialNumber }) => {
                console.log(`NFC card detected! Serial Number: ${serialNumber}`);
                
                // Process the card data
                const cardData = {
                    serialNumber: serialNumber,
                    message: this.processNDEFMessage(message)
                };
                
                if (typeof this.options.onReading === 'function') {
                    this.options.onReading(cardData);
                }
                
                if (typeof this.options.onSuccess === 'function') {
                    this.options.onSuccess('Card read successfully');
                }
            });
            
            this.reader.addEventListener("readingerror", (error) => {
                console.error(`Error reading NFC card: ${error}`);
                if (typeof this.options.onError === 'function') {
                    this.options.onError(error);
                }
            });
            
            this.isReading = true;
            return true;
        } catch (error) {
            console.error(`Error starting NFC reader: ${error}`);
            if (typeof this.options.onError === 'function') {
                this.options.onError(error);
            }
            return false;
        }
    }

    /**
     * Stop reading NFC cards
     */
    stopReading() {
        if (!this.isReading || !this.reader) {
            return;
        }
        
        // The Web NFC API doesn't have a direct method to stop scanning
        // We'll set our internal state to indicate we're no longer interested in readings
        this.isReading = false;
        console.log('NFC reader stopped.');
    }

    /**
     * Process NDEF message from NFC card
     * @param {NDEFMessage} message - The NDEF message from the NFC card
     * @returns {Array} - Array of records from the NFC card
     */
    processNDEFMessage(message) {
        const records = [];
        
        for (const record of message.records) {
            const recordInfo = {
                recordType: record.recordType,
                mediaType: record.mediaType,
                data: null
            };
            
            // Process different types of records
            if (record.recordType === "text") {
                const textDecoder = new TextDecoder();
                recordInfo.data = textDecoder.decode(record.data);
            } else if (record.recordType === "url") {
                const textDecoder = new TextDecoder();
                recordInfo.data = textDecoder.decode(record.data);
            } else {
                // For other types, store the raw data
                recordInfo.data = record.data;
            }
            
            records.push(recordInfo);
        }
        
        return records;
    }

    /**
     * Simulate an NFC card reading (for testing or fallback)
     * @param {string} serialNumber - Simulated serial number
     */
    simulateReading(serialNumber = "04:A1:B2:C3:D4:E5") {
        if (typeof this.options.onReading === 'function') {
            const simulatedData = {
                serialNumber: serialNumber,
                message: [{
                    recordType: "text",
                    mediaType: "text/plain",
                    data: "Simulated NFC Card"
                }]
            };
            
            this.options.onReading(simulatedData);
        }
        
        if (typeof this.options.onSuccess === 'function') {
            this.options.onSuccess('Simulated card read successfully');
        }
    }
}

// NFC Card Manager for handling card data and server communication
class NFCCardManager {
    constructor(apiEndpoint = '/api/nfc/') {
        this.apiEndpoint = apiEndpoint;
    }

    /**
     * Send card data to the server
     * @param {Object} cardData - The NFC card data
     * @param {string} action - The action to perform with the card
     * @returns {Promise} - Promise resolving to the server response
     */
    async sendCardData(cardData, action = '') {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    card_id: cardData.serialNumber,
                    action: action,
                    timestamp: new Date().toISOString()
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error sending card data to server:', error);
            throw error;
        }
    }

    /**
     * Get CSRF token from cookie
     * @returns {string} - CSRF token
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        
        return cookieValue;
    }
}

// UI Handler for NFC reader interface
class NFCUIHandler {
    constructor(containerId, reader, cardManager) {
        this.container = document.getElementById(containerId);
        this.reader = reader;
        this.cardManager = cardManager;
        if (!this.container) {
            console.error(`Container with ID '${containerId}' not found.`);
            return;
        }
        this.initUI();
    }

    initUI() {
        // Minimal UI: Only scan button, status, and message
        this.container.innerHTML = `
            <div class="nfc-reader-container bg-white p-6 rounded-lg shadow-md">
                <h2 class="text-2xl font-semibold text-blue-600 mb-4">NFC/QR Scan</h2>
                <div class="nfc-status-container mb-4">
                    <div class="flex items-center mb-2">
                        <div id="nfc-status-indicator" class="w-4 h-4 rounded-full bg-gray-400 mr-2"></div>
                        <span id="nfc-status-text" class="text-gray-600">Inactive</span>
                    </div>
                </div>
                <button id="nfc-start-btn" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 mb-4">
                    Start Scan
                </button>
                <button id="nfc-stop-btn" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 mb-4" disabled>
                    Stop Scan
                </button>
                <div id="nfc-message" class="text-green-600 font-semibold mt-4"></div>
            </div>
        `;
        this.statusIndicator = document.getElementById('nfc-status-indicator');
        this.statusText = document.getElementById('nfc-status-text');
        this.startButton = document.getElementById('nfc-start-btn');
        this.stopButton = document.getElementById('nfc-stop-btn');
        this.messageBox = document.getElementById('nfc-message');
        this.setupEventListeners();
        this.updateUIForNFCSupport();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', async () => {
            const started = await this.reader.startReading();
            if (started) {
                this.updateReaderStatus(true);
                this.showMessage('Ready to scan. Please scan your card or QR.');
            } else {
                this.showMessage('Failed to start reader.', true);
            }
        });
        this.stopButton.addEventListener('click', () => {
            this.reader.stopReading();
            this.updateReaderStatus(false);
            this.showMessage('Reader stopped.');
        });
        // On successful scan
        this.reader.options.onReading = (cardData) => {
            this.showMessage('QR scanned! Data fetched successfully.');
            this.updateReaderStatus(false);
            // Automatically trigger the next step if a callback is provided
            if (typeof this.options.onSuccess === 'function') {
                this.options.onSuccess(cardData);
            }
            // Optionally, you can trigger a custom event for the UI to listen to
            const event = new CustomEvent('nfc-scan-success', { detail: cardData });
            document.dispatchEvent(event);
        };
        this.reader.options.onError = (error) => {
            this.showMessage('Error: ' + (error.message || error), true);
        };
        this.reader.options.onSuccess = (msg) => {
            // Optionally show success
        };
        this.reader.options.onNotSupported = () => {
            this.showMessage('NFC is not supported in this browser.', true);
        };
    }

    updateUIForNFCSupport() {
        if (this.reader.nfcSupported) {
            this.statusIndicator.classList.remove('bg-gray-400', 'bg-red-500');
            this.statusIndicator.classList.add('bg-green-500');
            this.statusText.textContent = 'Ready';
            this.startButton.disabled = false;
        } else {
            this.statusIndicator.classList.remove('bg-green-500');
            this.statusIndicator.classList.add('bg-gray-400');
            this.statusText.textContent = 'Not Supported';
            this.startButton.disabled = true;
        }
        this.stopButton.disabled = true;
    }

    updateReaderStatus(isActive) {
        if (isActive) {
            this.statusIndicator.classList.remove('bg-gray-400');
            this.statusIndicator.classList.add('bg-green-500');
            this.statusText.textContent = 'Scanning...';
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
        } else {
            this.statusIndicator.classList.remove('bg-green-500');
            this.statusIndicator.classList.add('bg-gray-400');
            this.statusText.textContent = 'Inactive';
            this.startButton.disabled = false;
            this.stopButton.disabled = true;
        }
    }

    showMessage(msg, isError = false) {
        this.messageBox.textContent = msg;
        this.messageBox.className = isError ? 'text-red-600 font-semibold mt-4' : 'text-green-600 font-semibold mt-4';
    }
}

// Initialize the NFC system when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if the NFC container exists on the page
    const nfcContainer = document.getElementById('nfc-reader');
    if (!nfcContainer) {
        return;
    }
    
    // Create NFC reader
    const nfcReader = new NFCReader();
    
    // Create card manager
    const cardManager = new NFCCardManager('/api/nfc/');
    
    // Create UI handler
    const uiHandler = new NFCUIHandler('nfc-reader', nfcReader, cardManager);
    
    // Expose to global scope for debugging
    window.nfcReader = nfcReader;
    window.nfcCardManager = cardManager;
    window.nfcUIHandler = uiHandler;
});
