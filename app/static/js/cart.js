/**
 * Cart.js - Shopping Cart Management
 * Handles cart operations: update quantity, remove items
 */

// ============================================
// QUANTITY MANAGEMENT
// ============================================

/**
 * Update item quantity in cart
 * @param {string} itemId - Item ID
 * @param {number} newQuantity - New quantity
 */
function updateQuantity(itemId, newQuantity) {
    newQuantity = parseInt(newQuantity);
    
    if (newQuantity < 1) {
        removeItem(itemId);
        return;
    }
    
    fetch('/api/cart/update', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: newQuantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            showToast(data.error || 'Failed to update quantity', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Network error. Please try again.', 'error');
    });
}

// ============================================
// REMOVE ITEMS
// ============================================

/**
 * Remove item from cart
 * @param {string} itemId - Item ID to remove
 */
function removeItem(itemId) {
    if (!confirm('Remove this item from cart?')) {
        return;
    }
    
    fetch(`/api/cart/remove/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Item removed from cart', 'info');
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.error || 'Failed to remove item', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Network error. Please try again.', 'error');
    });
}

// Make functions globally accessible
window.updateQuantity = updateQuantity;
window.removeItem = removeItem;
