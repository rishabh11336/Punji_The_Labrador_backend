from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
from services.github_service import GitHubService
from services.image_service import ImageService
from utils.auth import check_auth, require_auth

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Initialize services
try:
    github_service = GitHubService()
    image_service = ImageService()
except ValueError as e:
    print(f"WARNING: {e}")
    print("Please configure environment variables in .env file")
    github_service = None
    image_service = ImageService()

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if check_auth(username, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@require_auth
def admin():
    return render_template('admin.html', username=session.get('username'))

@app.route('/upload', methods=['POST'])
@require_auth
def upload_product():
    try:
        if not github_service:
            flash('GitHub service not configured. Please set environment variables.', 'error')
            return redirect(url_for('admin'))
        
        # Get form data
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '0')
        original_price = request.form.get('originalPrice', '')
        rating = request.form.get('rating', '0')
        reviews = request.form.get('reviews', '0')
        description = request.form.get('description', '').strip()
        affiliate_link = request.form.get('affiliateLink', '').strip()
        badge = request.form.get('badge', '').strip()
        
        # Validate required fields
        if not all([name, category, price, rating, reviews, description, affiliate_link]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('admin'))
        
        # Process image
        image_file = request.files.get('image')
        if not image_file or image_file.filename == '':
            flash('Image is required', 'error')
            return redirect(url_for('admin'))
        
        filepath, filename = image_service.process_image(image_file)
        
        # Upload image to GitHub
        image_url = github_service.upload_image(filepath, filename)
        
        # Clean up local file
        image_service.cleanup(filepath)
        
        # Prepare product data
        product_data = {
            'name': name,
            'category': category,
            'price': float(price),
            'rating': float(rating),
            'reviews': int(reviews),
            'image': image_url,
            'description': description,
            'affiliateLink': affiliate_link
        }
        
        if original_price:
            product_data['originalPrice'] = float(original_price)
        if badge:
            product_data['badge'] = badge
        
        # Add product to GitHub
        github_service.add_product(product_data)
        
        flash(f'Product "{name}" added successfully!', 'success')
        return render_template('success.html', product_name=name, product_url=image_url)
        
    except ValueError as ve:
        flash(f'Validation error: {str(ve)}', 'error')
        return redirect(url_for('admin'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/products')
@require_auth
def list_products():
    """API endpoint to get all products"""
    try:
        if not github_service:
            return {'error': 'GitHub service not configured'}, 500
        
        products = github_service.get_products()
        return {'products': products}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/edit/<int:product_index>', methods=['GET', 'POST'])
@require_auth
def edit_product(product_index):
    """Edit an existing product"""
    try:
        if not github_service:
            flash('GitHub service not configured. Please set environment variables.', 'error')
            return redirect(url_for('admin'))
        
        # GET: Show edit form
        if request.method == 'GET':
            products = github_service.get_products()
            if product_index < 0 or product_index >= len(products):
                flash('Product not found', 'error')
                return redirect(url_for('admin'))
            
            product = products[product_index]
            return render_template('edit.html', product=product, index=product_index, username=session.get('username'))
        
        # POST: Update product
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '0')
        original_price = request.form.get('originalPrice', '')
        rating = request.form.get('rating', '0')
        reviews = request.form.get('reviews', '0')
        description = request.form.get('description', '').strip()
        affiliate_link = request.form.get('affiliateLink', '').strip()
        badge = request.form.get('badge', '').strip()
        
        # Validate required fields
        if not all([name, category, price, rating, reviews, description, affiliate_link]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('edit_product', product_index=product_index))
        
        # Get current product to preserve image if no new upload
        products = github_service.get_products()
        current_product = products[product_index]
        image_url = current_product.get('image')
        
        # Check if new image was uploaded
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Process new image
            filepath, filename = image_service.process_image(image_file)
            image_url = github_service.upload_image(filepath, filename)
            image_service.cleanup(filepath)
            
            # Optional: Delete old image
            old_image_url = current_product.get('image')
            if old_image_url:
                try:
                    github_service.delete_image(old_image_url)
                except:
                    pass  # Continue even if old image deletion fails
        
        # Prepare updated product data
        product_data = {
            'name': name,
            'category': category,
            'price': float(price),
            'rating': float(rating),
            'reviews': int(reviews),
            'image': image_url,
            'description': description,
            'affiliateLink': affiliate_link
        }
        
        if original_price:
            product_data['originalPrice'] = float(original_price)
        if badge:
            product_data['badge'] = badge
        
        # Update product
        github_service.update_product(product_index, product_data)
        
        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    except ValueError as ve:
        flash(f'Error: {str(ve)}', 'error')
        return redirect(url_for('admin'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/delete/<int:product_index>', methods=['POST'])
@require_auth
def delete_product(product_index):
    """Delete a product"""
    try:
        if not github_service:
            return {'error': 'GitHub service not configured'}, 500
        
        # Get product before deleting (for image cleanup)
        products = github_service.get_products()
        if product_index < 0 or product_index >= len(products):
            return {'error': 'Product not found'}, 404
        
        product = products[product_index]
        
        # Delete product from JSON
        result = github_service.delete_product(product_index)
        
        # Optional: Delete image
        image_url = product.get('image')
        if image_url:
            try:
                github_service.delete_image(image_url)
            except:
                pass  # Continue even if image deletion fails
        
        flash(f'Product "{product.get("name")}" deleted successfully!', 'success')
        return {'success': True, 'message': 'Product deleted'}, 200
    
    except ValueError as ve:
        return {'error': str(ve)}, 404
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'Punji Admin Backend'}, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
