// ============================================
// MENU PAGE FUNCTIONALITY
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

/**
 * Add item to shopping cart
 * @param {string} itemId - Item ID
 * @param {string} itemName - Item name
 * @param {number} itemPrice - Item price
 */
function addToCart(itemId, itemName, itemPrice) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            name: itemName,
            price: itemPrice,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount();
            showToast(`${itemName} added to cart!`);
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Update cart count badge
 */
function updateCartCount() {
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('cart-count');
            if (badge) {
                badge.textContent = data.count;
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

// Load cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
});
