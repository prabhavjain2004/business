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
        this.soundPlayed = false; // Flag to track if sound has been played
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

    /**
     * Handle card reading
     * @param {Object} cardData - The NFC card data
     */
    handleCardReading(cardData) {
        // Play sound only if it hasn't been played yet for the current card
        if (!this.soundPlayed) {
            this.playSound('success'); // Play sound when a card is detected
            this.soundPlayed = true; // Set flag to true
        }
        
        // Update card info
        this.cardId.textContent = cardData.serialNumber;
        this.readTime.textContent = new Date().toLocaleTimeString();
        this.readStatus.textContent = 'Success';
        
        // Show card info and action container
        this.cardInfo.classList.remove('hidden');
        this.actionContainer.classList.remove('hidden');
        
        // Add log message
        this.addLogMessage(`Card detected: ${cardData.serialNumber}`);
        
        // Check if the card is already issued
        this.cardManager.sendCardData({ serialNumber: cardData.serialNumber }, 'issue_card')
            .then(issueResponse => {
                if (issueResponse.status === 'error') {
                    this.addLogMessage(`Error: ${issueResponse.message}`, 'error');
                    alert(issueResponse.message); // Inform user that card is already issued or has an error
                    throw new Error(issueResponse.message); // Exit promise chain
                }

                // Card is not issued yet, proceed to get card details
                return this.cardManager.sendCardData({ serialNumber: cardData.serialNumber }, 'balance_inquiry');
            })
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
    const nfcReader = new NFCReader({
        onReading: (cardData) => {
            // Check if the card is already issued
            nfcCardManager.sendCardData({ serialNumber: cardData.serialNumber }, 'issue_card')
                .then(issueResponse => {
                    if (issueResponse.status === 'error') {
                        nfcUIHandler.addLogMessage(`Error: ${issueResponse.message}`, 'error');
                        alert(issueResponse.message); // Inform user that card is already issued or has an error
                        throw new Error(issueResponse.message); // Exit promise chain
                    }

                    // Card is not issued yet, proceed to get card details
                    return nfcCardManager.sendCardData({ serialNumber: cardData.serialNumber }, 'balance_inquiry');
                })
                .then(response => {
                    // Store secure key for future transactions
                    cardData.secureKey = response.secure_key;
                    
                    // Store the card data with secure key for future use
                    nfcReader.options.lastCardData = cardData;
                    
                    // Add additional info to log
                    if (response.customer_name) {
                        nfcUIHandler.addLogMessage(`Customer: ${response.customer_name}`);
                    }
                    if (response.balance !== undefined) {
                        nfcUIHandler.addLogMessage(`Balance: ₹${response.balance}`);
                    }
                })
                .catch(error => {
                    nfcUIHandler.addLogMessage(`Error getting card details: ${error.message}`, 'error');
                });
        },
        onError: (error) => {
            nfcUIHandler.addLogMessage(`Error: ${error.message || error}`, 'error');
        },
        onSuccess: (message) => {
            nfcUIHandler.addLogMessage(message);
        },
        onNotSupported: () => {
            nfcUIHandler.updateUIForNFCSupport();
        }
    });
    
    // Create card manager
    const nfcCardManager = new NFCCardManager('/api/nfc/');
    
    // Create UI handler
    const nfcUIHandler = new NFCUIHandler('nfc-reader', nfcReader, nfcCardManager);
    
    // Expose to global scope for debugging
    window.nfcReader = nfcReader;
    window.nfcCardManager = nfcCardManager;
    window.nfcUIHandler = nfcUIHandler;
});
