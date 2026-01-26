// Star rating functionality
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('#starRating i');
    const ratingInput = document.getElementById('ratingInput');
    const reviewForm = document.getElementById('reviewForm');
    
    if (!stars.length || !reviewForm) return;
    
    let selectedRating = 0;
    
    // Hover effect
    stars.forEach(star => {
        star.addEventListener('mouseenter', function() {
            const rating = parseInt(this.dataset.rating);
            highlightStars(rating);
        });
    });
    
    // Reset on mouse leave
    document.getElementById('starRating').addEventListener('mouseleave', function() {
        highlightStars(selectedRating);
    });
    
    // Click to select
    stars.forEach(star => {
        star.addEventListener('click', function() {
            selectedRating = parseInt(this.dataset.rating);
            ratingInput.value = selectedRating;
            highlightStars(selectedRating);
            
            // Hide error if shown
            document.getElementById('ratingError').classList.add('d-none');
        });
    });
    
    function highlightStars(rating) {
        stars.forEach(star => {
            const starRating = parseInt(star.dataset.rating);
            if (starRating <= rating) {
                star.classList.remove('far');
                star.classList.add('fas', 'selected');
            } else {
                star.classList.remove('fas', 'selected');
                star.classList.add('far');
            }
        });
    }
    
    // Form submission
    reviewForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const rating = ratingInput.value;
        const comment = document.getElementById('comment').value.trim();

        // Get CSRF token from form
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;

        // Validation
        let hasError = false;
        
        if (!rating) {
            document.getElementById('ratingError').classList.remove('d-none');
            hasError = true;
        }
        
        if (comment.length < 10) {
            const commentError = document.getElementById('commentError');
            commentError.textContent = 'Comment must be at least 10 characters';
            commentError.classList.remove('d-none');
            hasError = true;
        } else if (comment.length > 500) {
            const commentError = document.getElementById('commentError');
            commentError.textContent = 'Comment must be less than 500 characters';
            commentError.classList.remove('d-none');
            hasError = true;
        } else {
            document.getElementById('commentError').classList.add('d-none');
        }
        
        if (hasError) return;
        
        // Disable submit button
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        
        try {
            const response = await fetch('/api/reviews/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken 
                },
                body: JSON.stringify({
                    rating: parseInt(rating),
                    comment: comment
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Show success message
                const successMsg = document.getElementById('successMessage');
                successMsg.textContent = data.message;
                successMsg.classList.remove('d-none');
                
                // Hide error message
                document.getElementById('errorMessage').classList.add('d-none');
                
                // Reset form
                reviewForm.reset();
                selectedRating = 0;
                highlightStars(0);
                ratingInput.value = '';
                
                // Reload page after 2 seconds to show new review
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                // Show error message
                const errorMsg = document.getElementById('errorMessage');
                errorMsg.textContent = data.error || 'Failed to submit review';
                errorMsg.classList.remove('d-none');
                
                // Hide success message
                document.getElementById('successMessage').classList.add('d-none');
            }
        } catch (error) {
            console.error('Error submitting review:', error);
            const errorMsg = document.getElementById('errorMessage');
            errorMsg.textContent = 'Network error. Please try again.';
            errorMsg.classList.remove('d-none');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Review';
        }
    });
});
