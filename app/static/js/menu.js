/**
 * Menu.js - Menu Page Functionality
 * Handles category filtering and adding items to cart
 */

// ============================================
// CATEGORY FILTERING
// ============================================

/**
 * Filter menu items by category
 * @param {string} category - Category to filter by 
 */
function filterCategory(category) {
    const items = document.querySelectorAll('.menu-item');
    const buttons = document.querySelectorAll('.category-btn');
    
    // Update active button
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Show/hide items based on category
    items.forEach(item => {
        if (category === 'all' || item.dataset.category === category) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// ============================================
// ADD TO CART
// ============================================

/**
 * Add item to shopping cart
 * @param {string} itemId - Item ID
 * @param {string} itemName - Item name
 * @param {number} itemPrice - Item price
 */
function addToCart(itemId, itemName, itemPrice) {

    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            item_id: itemId,
            name: itemName,
            price: parseFloat(itemPrice),
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (typeof updateCartCount === 'function') {
                updateCartCount();
            }
            showToast(`${itemName} added to cart!`, 'success');
        } else {
            showToast(data.error || 'Failed to add item', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Network error. Please try again.', 'error');
    });
}

// Make functions globally accessible
window.filterCategory = filterCategory;
window.addToCart = addToCart;
