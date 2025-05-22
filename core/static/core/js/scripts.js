/**
 * Modern scripts for the TapNex application
 * All animations and delays removed
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
        const tooltipText = tooltip.getAttribute('data-tooltip');
        const tooltipElement = document.createElement('div');
        tooltipElement.classList.add('tooltip-text');
        tooltipElement.textContent = tooltipText;
        
        tooltip.classList.add('tech-tooltip');
        tooltip.appendChild(tooltipElement);
    });
}

/**
 * Initialize dropdown menus
 */
function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
    
    dropdownToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-dropdown-toggle');
        const target = document.getElementById(targetId);
        
        if (target) {
            target.classList.add('hidden');
            
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (target.classList.contains('hidden')) {
                    // Close any open dropdowns first
                    document.querySelectorAll('[data-dropdown].block').forEach(dropdown => {
                        dropdown.classList.add('hidden');
                        dropdown.classList.remove('block');
                    });
                    
                    // Open this dropdown
                    target.classList.remove('hidden');
                    target.classList.add('block');
                } else {
                    target.classList.add('hidden');
                    target.classList.remove('block');
                }
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                if (!target.classList.contains('hidden')) {
                    target.classList.add('hidden');
                    target.classList.remove('block');
                }
            });
        }
    });
}
