// ============================================
// CART PAGE FUNCTIONALITY
// ============================================

/**
 * Update item quantity in cart
 * @param {string} itemId - Item ID
 * @param {number} newQuantity - New quantity
 */
function updateQuantity(itemId, newQuantity) {
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
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Remove item from cart
 * @param {string} itemId - Item ID to remove
 */
function removeItem(itemId) {
    fetch(`/api/cart/remove/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Item removed from cart');
            setTimeout(() => location.reload(), 500);
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 */
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}
