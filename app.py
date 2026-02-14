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

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'Punji Admin Backend'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
