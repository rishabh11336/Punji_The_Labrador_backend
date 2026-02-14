// Image Preview
document.getElementById('image')?.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        // Check file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            alert('File size must be less than 5MB');
            this.value = '';
            return;
        }

        // Check file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid image file (JPG, PNG, or WebP)');
            this.value = '';
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = function (e) {
            const preview = document.getElementById('imagePreview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
});

// Form validation
document.getElementById('productForm')?.addEventListener('submit', function (e) {
    const price = parseFloat(document.getElementById('price').value);
    const originalPrice = document.getElementById('originalPrice').value;

    if (originalPrice && parseFloat(originalPrice) <= price) {
        alert('Original price should be higher than current price');
        e.preventDefault();
        return false;
    }

    const rating = parseFloat(document.getElementById('rating').value);
    if (rating < 1 || rating > 5) {
        alert('Rating must be between 1 and 5');
        e.preventDefault();
        return false;
    }

    const reviews = parseInt(document.getElementById('reviews').value);
    if (reviews < 0) {
        alert('Review count cannot be negative');
        e.preventDefault();
        return false;
    }

    // Show loading state
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span>Uploading...</span>';
    submitBtn.disabled = true;
});

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});
