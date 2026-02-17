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

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');

            // Remove active class from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            btn.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');

            // Load products if manage tab is clicked
            if (tabName === 'manage') {
                loadProducts();
            }
        });
    });
});

// Load products from server
async function loadProducts() {
    const loading = document.getElementById('productsLoading');
    const error = document.getElementById('productsError');
    const list = document.getElementById('productsList');

    loading.style.display = 'block';
    error.style.display = 'none';
    list.innerHTML = '';

    try {
        const response = await fetch('/products');
        if (!response.ok) throw new Error('Failed to load products');

        const data = await response.json();
        const products = data.products || [];

        loading.style.display = 'none';

        if (products.length === 0) {
            list.innerHTML = '<p class="empty">No products found. Add your first product!</p>';
            return;
        }

        // Render products
        list.innerHTML = products.map((product, index) => `
            <div class="product-card">
                <img src="${product.image}" alt="${product.name}" class="product-thumb">
                <div class="product-info">
                    <h3>${product.name}</h3>
                    <p class="product-meta">
                        <span class="category">${getCategoryIcon(product.category)} ${product.category}</span>
                        <span class="price">₹${product.price}</span>
                        <span class="rating">⭐ ${product.rating} (${product.reviews} reviews)</span>
                    </p>
                </div>
                <div class="product-actions">
                    <a href="/edit/${index}" class="btn-edit">✏️ Edit</a>
                    <button class="btn-delete" data-index="${index}" data-name="${product.name}">🗑️ Delete</button>
                </div>
            </div>
        `).join('');

        // Attach delete handlers
        attachDeleteHandlers();

    } catch (err) {
        loading.style.display = 'none';
        error.style.display = 'block';
        error.textContent = `Error: ${err.message}`;
    }
}

// Helper function to get category icon
function getCategoryIcon(category) {
    const icons = {
        'toys': '🎾',
        'treats': '🦴',
        'bowls': '🍽️',
        'accessories': '🎀'
    };
    return icons[category] || '📦';
}

// Attach delete handlers to buttons
function attachDeleteHandlers() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const index = btn.getAttribute('data-index');
            const name = btn.getAttribute('data-name');
            showDeleteModal(index, name);
        });
    });
}

// Show delete confirmation modal
function showDeleteModal(index, name) {
    const modal = document.getElementById('deleteModal');
    const productName = document.getElementById('deleteProductName');
    const confirmBtn = document.getElementById('confirmDelete');

    productName.textContent = name;
    modal.style.display = 'flex';

    // Remove old event listeners
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    // Attach new event listener
    newConfirmBtn.addEventListener('click', () => deleteProduct(index));
}

// Close modal handlers
document.getElementById('cancelDelete')?.addEventListener('click', () => {
    document.getElementById('deleteModal').style.display = 'none';
});

document.getElementById('deleteModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'deleteModal') {
        e.target.style.display = 'none';
    }
});

// Delete product
async function deleteProduct(index) {
    const modal = document.getElementById('deleteModal');
    const confirmBtn = document.getElementById('confirmDelete');

    // Show loading state
    confirmBtn.textContent = 'Deleting...';
    confirmBtn.disabled = true;

    try {
        const response = await fetch(`/delete/${index}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to delete product');

        // Close modal
        modal.style.display = 'none';

        // Reload products
        loadProducts();

        // Show success message
        showAlert('Product deleted successfully!', 'success');

    } catch (err) {
        showAlert(`Error: ${err.message}`, 'error');
        confirmBtn.textContent = 'Delete';
        confirmBtn.disabled = false;
    }
}

// Show alert message
function showAlert(message, type) {
    const container = document.querySelector('.container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.5s';
        setTimeout(() => alert.remove(), 500);
    }, 3000);
}
