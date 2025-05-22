/**
 * Modern scripts for the TapNex application
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeDropdowns();
});

/**
 * Initialize tooltips with modern styling
 */
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(tooltip => {
        try {
            const tooltipText = tooltip.getAttribute('data-tooltip');
            if (!tooltipText) {
                console.warn('Tooltip element found without tooltip text');
                return;
            }

            const tooltipElement = document.createElement('div');
            tooltipElement.classList.add('tooltip-text');
            tooltipElement.textContent = tooltipText;
            
            tooltip.classList.add('tech-tooltip');
            tooltip.appendChild(tooltipElement);
        } catch (error) {
            console.error('Error initializing tooltip:', error);
        }
    });
}

/**
 * Initialize dropdown menus with improved event handling
 */
function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
    let openDropdown = null;
    
    // Single document click listener for all dropdowns
    const documentClickHandler = (e) => {
        if (openDropdown && !openDropdown.contains(e.target)) {
            closeDropdown(openDropdown);
        }
    };

    // Add single event listener for document
    document.addEventListener('click', documentClickHandler);

    function closeDropdown(dropdown) {
        if (dropdown) {
            dropdown.classList.add('hidden');
            dropdown.classList.remove('block');
            openDropdown = null;
        }
    }

    function openDropdown(dropdown) {
        if (openDropdown) {
            closeDropdown(openDropdown);
        }
        dropdown.classList.remove('hidden');
        dropdown.classList.add('block');
        openDropdown = dropdown;
    }

    dropdownToggles.forEach(toggle => {
        try {
            const targetId = toggle.getAttribute('data-dropdown-toggle');
            if (!targetId) {
                console.warn('Dropdown toggle found without target ID');
                return;
            }

            const target = document.getElementById(targetId);
            if (!target) {
                console.warn(`Dropdown target not found: ${targetId}`);
                return;
            }

            // Initialize dropdown state
            target.classList.add('hidden');
            
            // Add click handler to toggle
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (target.classList.contains('hidden')) {
                    openDropdown(target);
                } else {
                    closeDropdown(target);
                }
            });
        } catch (error) {
            console.error('Error initializing dropdown:', error);
        }
    });

    // Cleanup function for removing event listeners
    return function cleanup() {
        document.removeEventListener('click', documentClickHandler);
    };
}
