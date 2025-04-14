/**
 * Modern scripts for the TapNex application
 * Includes animations, interactive elements, and UI enhancements
 */

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeTooltips();
    initializeDropdowns();
    initializeAnimations();
    initializeParticles();
    initializeTypewriterEffect();
    initializeScrollEffects();
    initializeHoverEffects();
    initializeCardEffects();
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
 * Initialize dropdown menus with animations
 */
function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
    
    dropdownToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-dropdown-toggle');
        const target = document.getElementById(targetId);
        
        if (target) {
            // Add necessary classes
            target.classList.add('hidden', 'animate-fade-in');
            
            // Toggle dropdown on click
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

/**
 * Initialize animations for elements with animation classes
 */
function initializeAnimations() {
    // Add animation classes to elements when they enter the viewport
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const animation = element.getAttribute('data-animation') || 'animate-fade-in';
                element.classList.add(animation);
                observer.unobserve(element);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
    
    // Add staggered animations to lists
    const staggeredLists = document.querySelectorAll('[data-staggered-list]');
    
    staggeredLists.forEach(list => {
        const items = list.children;
        const staggerDelay = parseInt(list.getAttribute('data-stagger-delay') || 100);
        
        Array.from(items).forEach((item, index) => {
            item.style.animationDelay = `${index * staggerDelay}ms`;
            item.classList.add('animate-fade-in');
        });
    });
}

/**
 * Initialize particle background effect
 */
function initializeParticles() {
    const particlesContainer = document.querySelector('.particles-container');
    if (!particlesContainer) return;
    
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        // Random size between 2px and 6px
        const size = Math.random() * 4 + 2;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        // Random position
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        // Random animation delay
        particle.style.animationDelay = `${Math.random() * 5}s`;
        
        particlesContainer.appendChild(particle);
    }
}

/**
 * Initialize typewriter effect for elements with the class
 */
function initializeTypewriterEffect() {
    const typewriterElements = document.querySelectorAll('.typewriter');
    
    typewriterElements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        element.classList.add('animate-typing');
        
        let i = 0;
        const speed = parseInt(element.getAttribute('data-speed') || 50);
        
        function typeWriter() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            }
        }
        
        // Start the typewriter effect
        typeWriter();
    });
}

/**
 * Initialize scroll-based effects
 */
function initializeScrollEffects() {
    // Parallax effect
    const parallaxElements = document.querySelectorAll('.parallax');
    
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        
        parallaxElements.forEach(element => {
            const speed = parseFloat(element.getAttribute('data-parallax-speed') || 0.2);
            element.style.transform = `translateY(${scrollY * speed}px)`;
        });
        
        // Progress bar for scroll position
        const scrollProgress = document.querySelector('.scroll-progress');
        if (scrollProgress) {
            const scrollPercent = (scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
            scrollProgress.style.width = `${scrollPercent}%`;
        }
    });
    
    // Floating action button visibility
    const floatingBtn = document.querySelector('.floating-action-btn');
    if (floatingBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                floatingBtn.style.opacity = '1';
                floatingBtn.style.pointerEvents = 'auto';
            } else {
                floatingBtn.style.opacity = '0';
                floatingBtn.style.pointerEvents = 'none';
            }
        });
        
        // Scroll to top when clicked
        floatingBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        // Initialize button state
        window.dispatchEvent(new Event('scroll'));
    }
}

/**
 * Initialize hover effects for interactive elements
 */
function initializeHoverEffects() {
    // 3D card tilt effect
    const tiltCards = document.querySelectorAll('.tilt-card');
    
    tiltCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
        });
    });
    
    // Magnetic button effect
    const magneticButtons = document.querySelectorAll('.magnetic-btn');
    
    magneticButtons.forEach(button => {
        button.addEventListener('mousemove', (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const deltaX = (x - centerX) / 8;
            const deltaY = (y - centerY) / 8;
            
            button.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translate(0, 0)';
        });
    });
}

/**
 * Initialize special effects for NFC cards
 */
function initializeCardEffects() {
    const nfcCards = document.querySelectorAll('.nfc-card');
    
    nfcCards.forEach(card => {
        // Add 3D tilt effect
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateY = ((x - centerX) / centerX) * 10;
            const rotateX = ((centerY - y) / centerY) * 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
            
            // Dynamic highlight effect
            const shine = card.querySelector('.card-shine') || document.createElement('div');
            if (!card.querySelector('.card-shine')) {
                shine.classList.add('card-shine');
                card.appendChild(shine);
            }
            
            const shineX = (x / rect.width) * 100;
            const shineY = (y / rect.height) * 100;
            shine.style.background = `radial-gradient(circle at ${shineX}% ${shineY}%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 50%)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
            
            const shine = card.querySelector('.card-shine');
            if (shine) {
                shine.style.background = 'none';
            }
        });
    });
}
