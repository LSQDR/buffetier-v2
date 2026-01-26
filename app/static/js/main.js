/**
 * Main.js - Global Utilities
 * Contains shared functions used across multiple pages
 */

// ============================================
// CART COUNT MANAGEMENT
// ============================================

/**
 * Update cart count badge in navbar
 */
function updateCartCount() {
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartBadge = document.getElementById('cart-count');
            if (cartBadge) {
                cartBadge.textContent = data.count || 0;
                // Show or hide badge based on count
                if (data.count > 0) {
                    cartBadge.style.display = 'flex';
                } else {
                    cartBadge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error fetching cart count:', error));
}

// ============================================
// DROPDOWN MANAGEMENT
// ============================================

/**
 * Toggle admin dropdown menu
 * @param {Event} event - Click event
 */
function toggleDropdown(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const dropdown = document.getElementById('adminDropdown');
    const toggle = event.target.closest('.dropdown-toggle');
    
    // Close all other dropdowns first
    const allDropdowns = document.querySelectorAll('.dropdown-menu');
    allDropdowns.forEach(menu => {
        if (menu !== dropdown) {
            menu.classList.remove('show');
        }
    });
    const allToggles = document.querySelectorAll('.dropdown-toggle');
    allToggles.forEach(t => {
        if (t !== toggle) {
            t.classList.remove('active');
        }
    });
    
    // Toggle the clicked dropdown
    if (toggle && dropdown) {
        toggle.classList.toggle('active');
        dropdown.classList.toggle('show');
    }
}


/**
 * Close dropdowns when clicking outside
 */
document.addEventListener('click', function(event) {
    // Check if click is outside all dropdowns and toggles
    const isDropdownToggle = event.target.closest('.dropdown-toggle');
    const isDropdownMenu = event.target.closest('.dropdown-menu');
    
    if (!isDropdownToggle && !isDropdownMenu) {
        // Close all dropdowns
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(menu => menu.classList.remove('show'));
        const toggles = document.querySelectorAll('.dropdown-toggle');
        toggles.forEach(toggle => toggle.classList.remove('active'));
    }
});

// ============================================
// TOAST NOTIFICATIONS
// ============================================

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type: 'success', 'error', 'info', 'warning'
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px; margin: 0;';
    
    // Add type-specific styling
    if (type === 'error') {
        toast.style.background = '#e74c3c';
    } else if (type === 'warning') {
        toast.style.background = '#f39c12';
    } else if (type === 'info') {
        toast.style.background = '#3498db';
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize global features on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Update cart count if user is logged in
    if (document.getElementById('cart-count')) {
        updateCartCount();
        // Refresh cart count every 30 seconds
        setInterval(updateCartCount, 30000);
    }
});

// Make functions globally accessible
window.updateCartCount = updateCartCount;
window.toggleDropdown = toggleDropdown;
window.showToast = showToast;
