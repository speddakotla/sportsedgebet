/* ========================================
   SportsEdgeBet - Main JavaScript
   ======================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all components
    initNavigation();
    initPricingToggle();
    initFAQ();
    initSportTabs();
    initAnimations();
    initTrialCountdown();
    initModals();
});

/* ========================================
   Navigation
   ======================================== */
function initNavigation() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    const navActions = document.querySelector('.nav-actions');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenuBtn.classList.toggle('active');
            
            // Create mobile menu if it doesn't exist
            let mobileMenu = document.querySelector('.mobile-menu');
            if (!mobileMenu) {
                mobileMenu = document.createElement('div');
                mobileMenu.className = 'mobile-menu';
                mobileMenu.innerHTML = `
                    <div class="mobile-menu-content">
                        ${navLinks ? navLinks.innerHTML : ''}
                        ${navActions ? navActions.innerHTML : ''}
                    </div>
                `;
                mobileMenu.style.cssText = `
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    background: var(--bg-secondary);
                    border-bottom: 1px solid var(--border-color);
                    padding: 24px;
                    display: none;
                    flex-direction: column;
                    gap: 16px;
                    z-index: 999;
                    animation: fadeInDown 0.3s ease;
                `;
                document.body.appendChild(mobileMenu);
            }
            
            mobileMenu.style.display = mobileMenu.style.display === 'none' ? 'flex' : 'none';
        });
    }
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 100) {
                navbar.style.background = 'rgba(10, 10, 11, 0.95)';
                navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.3)';
            } else {
                navbar.style.background = 'rgba(10, 10, 11, 0.8)';
                navbar.style.boxShadow = 'none';
            }
            
            lastScroll = currentScroll;
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

/* ========================================
   Pricing Toggle (Monthly/Yearly)
   ======================================== */
function initPricingToggle() {
    const toggle = document.getElementById('billing-toggle');
    const togglePage = document.getElementById('billing-toggle-page');
    
    const setupToggle = (toggleEl) => {
        if (!toggleEl) return;
        
        toggleEl.addEventListener('change', () => {
            const isYearly = toggleEl.checked;
            
            // Update toggle labels
            const monthlyLabel = document.querySelector('#monthly-label, .toggle-label:first-of-type');
            const yearlyLabel = document.querySelector('#yearly-label, .toggle-label:last-of-type');
            
            document.querySelectorAll('.toggle-label').forEach((label, index) => {
                if (index === 0) {
                    label.classList.toggle('active', !isYearly);
                } else {
                    label.classList.toggle('active', isYearly);
                }
            });
            
            // Update all price amounts
            document.querySelectorAll('.amount, .price-amount').forEach(el => {
                const monthly = el.dataset.monthly;
                const yearly = el.dataset.yearly;
                
                if (monthly !== undefined && yearly !== undefined) {
                    // Animate the price change
                    el.style.transform = 'translateY(-10px)';
                    el.style.opacity = '0';
                    
                    setTimeout(() => {
                        el.textContent = isYearly ? yearly : monthly;
                        el.style.transform = 'translateY(0)';
                        el.style.opacity = '1';
                    }, 150);
                }
            });
            
            // Update period text
            document.querySelectorAll('.period, .price-period').forEach(el => {
                if (el.textContent.includes('forever')) return;
                el.textContent = '/month';
            });
        });
    };
    
    setupToggle(toggle);
    setupToggle(togglePage);
}

/* ========================================
   FAQ Accordion
   ======================================== */
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', () => {
            // Close other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.classList.contains('active')) {
                    otherItem.classList.remove('active');
                }
            });
            
            // Toggle current item
            item.classList.toggle('active');
        });
    });
}

/* ========================================
   Sport Tabs (Dashboard)
   ======================================== */
function initSportTabs() {
    const tabs = document.querySelectorAll('.sport-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all
            tabs.forEach(t => t.classList.remove('active'));
            // Add active to clicked
            tab.classList.add('active');
            
            // Here you would typically fetch/filter games based on sport
            // For demo, we'll just show a visual feedback
            const gamesSection = document.querySelector('.games-section');
            if (gamesSection) {
                gamesSection.style.opacity = '0.5';
                setTimeout(() => {
                    gamesSection.style.opacity = '1';
                }, 300);
            }
        });
    });
}

/* ========================================
   Scroll Animations
   ======================================== */
function initAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements
    const animateElements = document.querySelectorAll(
        '.feature-card, .step, .pricing-card, .pricing-card-detailed, .testimonial-card, .faq-item, .trial-card, .stat-card, .game-card'
    );
    
    animateElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });
    
    // Add the animation class styles
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
    
    // Parallax effect for hero floating cards
    const floatingCards = document.querySelectorAll('.odds-card');
    if (floatingCards.length > 0) {
        window.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX / window.innerWidth - 0.5;
            const mouseY = e.clientY / window.innerHeight - 0.5;
            
            floatingCards.forEach((card, index) => {
                const speed = (index + 1) * 10;
                const x = mouseX * speed;
                const y = mouseY * speed;
                card.style.transform = `translate(${x}px, ${y}px)`;
            });
        });
    }
}

/* ========================================
   Trial Countdown Timer
   ======================================== */
function initTrialCountdown() {
    const countdownValues = document.querySelectorAll('.countdown-value');
    if (countdownValues.length === 0) return;
    
    // Simulate a countdown (in a real app, this would be based on actual trial end date)
    let days = 4;
    let hours = 12;
    let minutes = 38;
    
    const updateCountdown = () => {
        minutes--;
        if (minutes < 0) {
            minutes = 59;
            hours--;
            if (hours < 0) {
                hours = 23;
                days--;
                if (days < 0) {
                    days = 0;
                    hours = 0;
                    minutes = 0;
                }
            }
        }
        
        countdownValues.forEach((el, index) => {
            if (index === 0) el.textContent = days;
            if (index === 1) el.textContent = hours;
            if (index === 2) el.textContent = minutes;
        });
    };
    
    // Update every minute (60000ms) - for demo, update every second
    setInterval(updateCountdown, 60000);
}

/* ========================================
   Modal System
   ======================================== */
function initModals() {
    // Trial signup modal
    const trialButtons = document.querySelectorAll('#start-pro-trial, #start-elite-trial, .btn-primary[href="pricing.html"]');
    
    trialButtons.forEach(btn => {
        if (btn.id === 'start-pro-trial' || btn.id === 'start-elite-trial') {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                showTrialModal(btn.id === 'start-elite-trial' ? 'Elite' : 'Pro');
            });
        }
    });
}

function showTrialModal(plan) {
    // Remove existing modal if any
    const existingModal = document.querySelector('.trial-modal');
    if (existingModal) existingModal.remove();
    
    const modal = document.createElement('div');
    modal.className = 'trial-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <button class="modal-close">&times;</button>
            <div class="modal-icon">🚀</div>
            <h2>Start Your ${plan} Trial</h2>
            <p>Get 7 days of full ${plan} access. No credit card required.</p>
            <form class="trial-form">
                <div class="form-group">
                    <label for="trial-email">Email Address</label>
                    <input type="email" id="trial-email" placeholder="you@example.com" required>
                </div>
                <div class="form-group">
                    <label for="trial-password">Create Password</label>
                    <input type="password" id="trial-password" placeholder="Min. 8 characters" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Start Free Trial</button>
            </form>
            <p class="modal-terms">By signing up, you agree to our <a href="#">Terms</a> and <a href="#">Privacy Policy</a>.</p>
        </div>
    `;
    
    // Add modal styles
    const modalStyles = `
        .trial-modal {
            position: fixed;
            inset: 0;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            animation: fadeIn 0.3s ease;
        }
        .modal-overlay {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
        }
        .modal-content {
            position: relative;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 48px;
            max-width: 420px;
            width: 100%;
            text-align: center;
            animation: slideUp 0.4s ease;
        }
        .modal-close {
            position: absolute;
            top: 16px;
            right: 16px;
            width: 40px;
            height: 40px;
            background: var(--bg-tertiary);
            border: none;
            border-radius: 50%;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .modal-close:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        .modal-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        .modal-content h2 {
            font-size: 1.75rem;
            margin-bottom: 8px;
        }
        .modal-content > p {
            color: var(--text-secondary);
            margin-bottom: 32px;
        }
        .trial-form {
            text-align: left;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 8px;
            color: var(--text-secondary);
        }
        .form-group input {
            width: 100%;
            padding: 14px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
            transition: all 0.2s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-primary-dim);
        }
        .form-group input::placeholder {
            color: var(--text-muted);
        }
        .modal-terms {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 20px;
        }
        .modal-terms a {
            color: var(--accent-primary);
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { 
                opacity: 0;
                transform: translateY(30px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    
    // Add styles if not already added
    if (!document.querySelector('#modal-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'modal-styles';
        styleEl.textContent = modalStyles;
        document.head.appendChild(styleEl);
    }
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Close modal handlers
    const closeModal = () => {
        modal.style.animation = 'fadeIn 0.3s ease reverse';
        setTimeout(() => {
            modal.remove();
            document.body.style.overflow = '';
        }, 280);
    };
    
    modal.querySelector('.modal-overlay').addEventListener('click', closeModal);
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    
    // Form submission
    modal.querySelector('.trial-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const email = modal.querySelector('#trial-email').value;
        const password = modal.querySelector('#trial-password').value;
        
        // Show success state
        modal.querySelector('.modal-content').innerHTML = `
            <div class="modal-icon">✅</div>
            <h2>Welcome to SportsEdgeBet!</h2>
            <p>Your ${plan} trial is now active. Check your email for login details.</p>
            <a href="dashboard.html" class="btn btn-primary btn-block">Go to Dashboard</a>
        `;
    });
    
    // Focus first input
    setTimeout(() => {
        modal.querySelector('#trial-email').focus();
    }, 100);
}

/* ========================================
   Utility Functions
   ======================================== */

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format odds display
function formatOdds(odds, format = 'american') {
    if (format === 'american') {
        return odds > 0 ? `+${odds}` : odds.toString();
    }
    // Add decimal/fractional format support as needed
    return odds.toString();
}

// Highlight best odds in a row
function highlightBestOdds(container) {
    const oddsElements = container.querySelectorAll('.odds-cell, .book-value');
    let bestValue = -Infinity;
    let bestElement = null;
    
    oddsElements.forEach(el => {
        const value = parseInt(el.textContent.replace(/[^-\d]/g, ''));
        if (value > bestValue) {
            bestValue = value;
            bestElement = el;
        }
    });
    
    if (bestElement) {
        oddsElements.forEach(el => el.classList.remove('best'));
        bestElement.classList.add('best');
    }
}

/* ========================================
   Dashboard Specific Functions
   ======================================== */

// Simulate live odds updates
function simulateLiveOdds() {
    const oddsElements = document.querySelectorAll('.odds-cell:not(.header)');
    
    setInterval(() => {
        // Randomly update some odds
        const randomIndex = Math.floor(Math.random() * oddsElements.length);
        const element = oddsElements[randomIndex];
        
        if (element && !element.closest('.odds-header')) {
            const currentText = element.textContent;
            const match = currentText.match(/([+-]?\d+)/);
            
            if (match) {
                const currentValue = parseInt(match[1]);
                const change = Math.random() > 0.5 ? 1 : -1;
                const newValue = currentValue + change;
                
                // Flash animation
                element.style.transition = 'background-color 0.3s ease';
                element.style.backgroundColor = change > 0 ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)';
                
                setTimeout(() => {
                    element.textContent = currentText.replace(match[1], newValue > 0 ? `+${newValue}` : newValue.toString());
                    element.style.backgroundColor = '';
                }, 150);
            }
        }
    }, 5000);
}

// Initialize live odds simulation on dashboard
if (document.querySelector('.dashboard-layout')) {
    simulateLiveOdds();
}

/* ========================================
   Search Functionality
   ======================================== */
function initSearch() {
    const searchInput = document.querySelector('.search-box input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', debounce((e) => {
        const query = e.target.value.toLowerCase();
        const gameCards = document.querySelectorAll('.game-card');
        
        gameCards.forEach(card => {
            const teamNames = card.querySelectorAll('.team-name');
            let matches = false;
            
            teamNames.forEach(name => {
                if (name.textContent.toLowerCase().includes(query)) {
                    matches = true;
                }
            });
            
            card.style.display = matches || query === '' ? 'block' : 'none';
        });
    }, 300));
}

// Initialize search on dashboard
if (document.querySelector('.search-box')) {
    initSearch();
}

/* ========================================
   Notifications System
   ======================================== */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span class="notification-message">${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: var(--bg-card);
        border: 1px solid ${type === 'success' ? 'var(--positive)' : type === 'error' ? 'var(--negative)' : 'var(--border-color)'};
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        z-index: 9999;
        animation: slideInRight 0.4s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.4s ease reverse';
        setTimeout(() => notification.remove(), 380);
    }, 4000);
}

// Add notification animations
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    .notification-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .notification-success .notification-icon {
        background: var(--accent-primary-dim);
        color: var(--accent-primary);
    }
    .notification-error .notification-icon {
        background: rgba(239, 68, 68, 0.15);
        color: var(--negative);
    }
`;
document.head.appendChild(notificationStyles);


