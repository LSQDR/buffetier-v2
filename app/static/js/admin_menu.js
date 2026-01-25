/**
 * Admin Menu Image Upload
 * Handles Cloud Storage integration for menu item images
 */

const API_UPLOAD = '/api/upload-image';
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

/**
 * Upload image for create form
 */
async function uploadCreateImage() {
    const fileInput = document.getElementById('createImageFile');
    const file = fileInput.files[0];
    
    if (!file || !validateFile(file)) return;
    
    await uploadImage(file, 'create');
}

/**
 * Upload image for edit form
 */
async function uploadEditImage(itemId) {
    const fileInput = document.getElementById(`editImageFile${itemId}`);
    const file = fileInput.files[0];
    
    if (!file || !validateFile(file)) return;
    
    await uploadImage(file, 'edit', itemId);
}

/**
 * Core upload function
 */
async function uploadImage(file, mode, itemId = '') {
    const progressId = mode === 'create' ? 'createUploadProgress' : `editUploadProgress${itemId}`;
    const previewId = mode === 'create' ? 'createImagePreview' : `editImagePreview${itemId}`;
    const urlInputId = mode === 'create' ? 'createImageUrl' : `editImageUrl${itemId}`;
    
    showElement(progressId);
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch(API_UPLOAD, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            document.getElementById(urlInputId).value = result.url;
            document.getElementById(previewId).innerHTML = 
                `<img src="${result.url}" alt="Preview" class="img-fluid rounded" style="max-height: 200px;">`;
            showNotification('Image uploaded successfully!', 'success');
        } else {
            showNotification(result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        showNotification('Upload error: ' + error.message, 'error');
    } finally {
        hideElement(progressId);
    }
}

/**
 * Validate file
 */
function validateFile(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
        showNotification('Invalid file type. Use PNG, JPG, or WebP.', 'error');
        return false;
    }
    
    if (file.size > MAX_FILE_SIZE) {
        showNotification('File too large. Maximum size is 5MB.', 'error');
        return false;
    }
    
    return true;
}

/**
 * Remove image from edit form
 */
function removeEditImage(itemId) {
    if (!confirm('Remove this image?')) return;
    
    document.getElementById(`editImageUrl${itemId}`).value = '';
    document.getElementById(`editImagePreview${itemId}`).innerHTML = 
        '<div class="border rounded p-4 text-muted"><i class="bi bi-image" style="font-size: 2rem;"></i><p class="mb-0 small">No image</p></div>';
    
    showNotification('Image removed', 'info');
}

/**
 * Show/hide elements
 */
function showElement(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('d-none');
}

function hideElement(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('d-none');
}

/**
 * Show notification (uses your existing toast style)
 */
function showNotification(message, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 5000);
}

/**
 * Reset create form
 */
function resetCreateForm() {
    const form = document.getElementById('createForm');
    if (form) form.reset();
    
    document.getElementById('createImageUrl').value = '';
    document.getElementById('createImagePreview').innerHTML = 
        '<div class="border rounded p-4 text-muted"><i class="bi bi-image" style="font-size: 2rem;"></i><p class="mb-0 small">No image selected</p></div>';
}

/**
 * Initialize
 */
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', resetCreateForm);
    }
});
