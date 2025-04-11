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
            
            // Store the simulated data for future use
            this.options.lastCardData = simulatedData;
            
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
     * @param {Object} additionalData - Additional data to send with the request
     * @returns {Promise} - Promise resolving to the server response
     */
    async sendCardData(cardData, action = '', additionalData = {}) {
        try {
            // Prepare request data
            const requestData = {
                action: action,
                timestamp: new Date().toISOString(),
                ...additionalData
            };
            
            // For initial card registration, use card_id
            if (action === 'issue_card' || !cardData.secureKey) {
                requestData.card_id = cardData.serialNumber;
            } 
            // For transactions, use secure_key if available
            else if (cardData.secureKey) {
                requestData.secure_key = cardData.secureKey;
            }
            // Fallback to card_id if secure_key is not available
            else {
                requestData.card_id = cardData.serialNumber;
            }
            
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(requestData)
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

    /**
     * Initialize the UI
     */
    initUI() {
        // Create UI elements
        this.createUIElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Update UI based on NFC support
        this.updateUIForNFCSupport();
    }

    /**
     * Create UI elements
     */
    createUIElements() {
        this.container.innerHTML = `
            <div class="nfc-reader-container bg-white p-6 rounded-lg shadow-md">
                <h2 class="text-2xl font-semibold text-blue-600 mb-4">NFC Card Reader</h2>
                
                <div class="nfc-status-container mb-6">
                    <div class="flex items-center mb-2">
                        <div id="nfc-status-indicator" class="w-4 h-4 rounded-full bg-gray-400 mr-2"></div>
                        <span id="nfc-status-text" class="text-gray-600">NFC Reader Inactive</span>
                    </div>
                    <p id="nfc-support-message" class="text-sm text-gray-500"></p>
                </div>
                
                <div class="nfc-controls mb-6">
                    <button id="nfc-start-btn" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 mr-2">
                        Start NFC Reader
                    </button>
                    <button id="nfc-stop-btn" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 mr-2" disabled>
                        Stop NFC Reader
                    </button>
                    <button id="nfc-simulate-btn" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200">
                        Simulate Card
                    </button>
                </div>
                
                <div class="nfc-card-info bg-gray-50 p-4 rounded-lg mb-6 hidden" id="nfc-card-info">
                    <h3 class="text-lg font-medium text-blue-600 mb-2">Card Information</h3>
                    <p><strong>Card ID:</strong> <span id="nfc-card-id">-</span></p>
                    <p><strong>Read Time:</strong> <span id="nfc-read-time">-</span></p>
                    <p><strong>Status:</strong> <span id="nfc-read-status">-</span></p>
                </div>
                
                <div class="nfc-action-container mb-6 hidden" id="nfc-action-container">
                    <h3 class="text-lg font-medium text-blue-600 mb-2">Select Action</h3>
                    <select id="nfc-action-select" class="w-full p-2 border border-gray-300 rounded-lg">
                        <option value="">-- Select Action --</option>
                        <option value="check_in">Check In</option>
                        <option value="check_out">Check Out</option>
                        <option value="verify">Verify Identity</option>
                    </select>
                    <button id="nfc-submit-action-btn" class="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Submit Action
                    </button>
                </div>
                
                <div class="nfc-log-container">
                    <h3 class="text-lg font-medium text-blue-600 mb-2">Activity Log</h3>
                    <div id="nfc-log" class="bg-gray-50 p-4 rounded-lg h-40 overflow-y-auto text-sm">
                        <p class="text-gray-500">NFC reader initialized.</p>
                    </div>
                </div>
            </div>
        `;
        
        // Get references to UI elements
        this.statusIndicator = document.getElementById('nfc-status-indicator');
        this.statusText = document.getElementById('nfc-status-text');
        this.supportMessage = document.getElementById('nfc-support-message');
        this.startButton = document.getElementById('nfc-start-btn');
        this.stopButton = document.getElementById('nfc-stop-btn');
        this.simulateButton = document.getElementById('nfc-simulate-btn');
        this.cardInfo = document.getElementById('nfc-card-info');
        this.cardId = document.getElementById('nfc-card-id');
        this.readTime = document.getElementById('nfc-read-time');
        this.readStatus = document.getElementById('nfc-read-status');
        this.actionContainer = document.getElementById('nfc-action-container');
        this.actionSelect = document.getElementById('nfc-action-select');
        this.submitActionButton = document.getElementById('nfc-submit-action-btn');
        this.logContainer = document.getElementById('nfc-log');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Start button
        this.startButton.addEventListener('click', async () => {
            const started = await this.reader.startReading();
            if (started) {
                this.updateReaderStatus(true);
                this.addLogMessage('NFC reader started.');
            } else {
                this.addLogMessage('Failed to start NFC reader.', 'error');
            }
        });
        
        // Stop button
        this.stopButton.addEventListener('click', () => {
            this.reader.stopReading();
            this.updateReaderStatus(false);
            this.addLogMessage('NFC reader stopped.');
        });
        
        // Simulate button
        this.simulateButton.addEventListener('click', () => {
            this.reader.simulateReading();
            this.addLogMessage('Simulated NFC card reading.');
        });
        
        // Submit action button
        this.submitActionButton.addEventListener('click', async () => {
            const action = this.actionSelect.value;
            if (!action) {
                this.addLogMessage('Please select an action.', 'error');
                return;
            }
            
            const cardId = this.cardId.textContent;
            if (cardId === '-') {
                this.addLogMessage('No card detected. Please scan a card first.', 'error');
                return;
            }
            
            try {
                // Find the card data with secure key
                const cardData = this.reader.options.lastCardData || { serialNumber: cardId };
                
                // Send the action with the card data (which may include secure key)
                const response = await this.cardManager.sendCardData(cardData, action);
                if (response.status === 'error') {
                    this.addLogMessage(`Error: ${response.message}`, 'error');
                    alert(response.message); // Display error message to the user
                    return;
                }
                this.addLogMessage(`Action "${action}" submitted successfully.`);
                this.actionContainer.classList.add('hidden');
            } catch (error) {
                this.addLogMessage(`Error submitting action: ${error.message}`, 'error');
            }
        });
        
        // Set up reader callbacks
        this.reader.options.onReading = (cardData) => {
            this.handleCardReading(cardData);
        };
        
        this.reader.options.onError = (error) => {
            this.addLogMessage(`Error: ${error.message || error}`, 'error');
        };
        
        this.reader.options.onSuccess = (message) => {
            this.addLogMessage(message);
        };
        
        this.reader.options.onNotSupported = () => {
            this.updateUIForNFCSupport();
        };
    }

    /**
     * Update UI based on NFC support
     */
    updateUIForNFCSupport() {
        if (this.reader.nfcSupported) {
            this.supportMessage.textContent = 'NFC is supported in this browser.';
            this.supportMessage.classList.remove('text-red-500');
            this.supportMessage.classList.add('text-green-500');
            this.startButton.disabled = false;
        } else {
            this.supportMessage.textContent = 'NFC is not supported in this browser. You can use the simulation feature instead.';
            this.supportMessage.classList.remove('text-green-500');
            this.supportMessage.classList.add('text-red-500');
            this.startButton.disabled = true;
        }
    }

    /**
     * Update reader status in UI
     * @param {boolean} isActive - Whether the reader is active
     */
    updateReaderStatus(isActive) {
        if (isActive) {
            this.statusIndicator.classList.remove('bg-gray-400', 'bg-red-500');
            this.statusIndicator.classList.add('bg-green-500');
            this.statusText.textContent = 'NFC Reader Active';
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
        } else {
            this.statusIndicator.classList.remove('bg-green-500', 'bg-red-500');
            this.statusIndicator.classList.add('bg-gray-400');
            this.statusText.textContent = 'NFC Reader Inactive';
            this.startButton.disabled = false;
            this.stopButton.disabled = true;
            
            // Hide card info and action container when reader is stopped
            this.cardInfo.classList.add('hidden');
            this.actionContainer.classList.add('hidden');
        }
    }

    /**
     * Handle card reading
     * @param {Object} cardData - The NFC card data
     */
    handleCardReading(cardData) {
        // Update card info
        this.cardId.textContent = cardData.serialNumber;
        this.readTime.textContent = new Date().toLocaleTimeString();
        this.readStatus.textContent = 'Success';
        
        // Show card info and action container
        this.cardInfo.classList.remove('hidden');
        this.actionContainer.classList.remove('hidden');
        
        // Add log message
        this.addLogMessage(`Card detected: ${cardData.serialNumber}`);
        
        // Get card details from server including secure key
        this.cardManager.sendCardData({ serialNumber: cardData.serialNumber }, 'balance_inquiry')
            .then(response => {
                // Store secure key for future transactions
                cardData.secureKey = response.secure_key;
                
                // Store the card data with secure key for future use
                this.reader.options.lastCardData = cardData;
                
                // Add additional info to log
                if (response.customer_name) {
                    this.addLogMessage(`Customer: ${response.customer_name}`);
                }
                if (response.balance !== undefined) {
                    this.addLogMessage(`Balance: ₹${response.balance}`);
                }
            })
            .catch(error => {
                this.addLogMessage(`Error getting card details: ${error.message}`, 'error');
            });
        
        // Play a sound to indicate successful reading
        this.playSound('success');
    }

    /**
     * Add a message to the log
     * @param {string} message - The message to add
     * @param {string} type - The type of message (info, error, etc.)
     */
    addLogMessage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('p');
        
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        if (type === 'error') {
            logEntry.classList.add('text-red-500');
        } else {
            logEntry.classList.add('text-gray-700');
        }
        
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    /**
     * Play a sound
     * @param {string} type - The type of sound to play
     */
    playSound(type) {
        // Create audio element
        const audio = new Audio();
        
        // Set source based on type
        switch (type) {
            case 'success':
                audio.src = '/static/core/sounds/success.mp3';
                break;
            case 'error':
                audio.src = '/static/core/sounds/error.mp3';
                break;
            default:
                audio.src = '/static/core/sounds/beep.mp3';
        }
        
        // Play the sound
        audio.play().catch(error => {
            console.warn('Could not play sound:', error);
        });
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