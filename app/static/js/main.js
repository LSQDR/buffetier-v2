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
                    cartBadge.style.display = 'inline-block';
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
    const dropdown = document.getElementById('adminDropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Close dropdowns when clicking outside
 */
window.addEventListener('click', function(event) {
    if (!event.target.matches('.dropdown-toggle')) {
        const dropdowns = document.getElementsByClassName('dropdown-menu');
        for (let i = 0; i < dropdowns.length; i++) {
            dropdowns[i].style.display = 'none';
        }
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
    toast.className = 'toast';
    toast.textContent = message;
    
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
