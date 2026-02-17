import requests
import json
import base64
from datetime import datetime
import os

class GitHubService:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER')
        self.repo_name = os.getenv('DATA_REPO_NAME')
        self.base_url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}'
        
        if not all([self.token, self.repo_owner, self.repo_name]):
            raise ValueError("Missing GitHub configuration in environment variables")
    
    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_file_sha(self, path):
        """Get SHA of file for updates"""
        url = f'{self.base_url}/contents/{path}'
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            return response.json()['sha']
        return None
    
    def get_current_products(self):
        """Fetch current products.json from data repo"""
        url = f'{self.base_url}/contents/products.json'
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return json.loads(content)
        
        # Return empty structure if file doesn't exist
        return {
            'products': [],
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0'
        }
    
    def add_product(self, product_data):
        """Add new product to products.json"""
        # Get current data
        current_data = self.get_current_products()
        
        # Generate new ID
        if current_data['products']:
            max_id = max(p['id'] for p in current_data['products'])
            product_data['id'] = max_id + 1
        else:
            product_data['id'] = 1
        
        # Add new product
        current_data['products'].append(product_data)
        current_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update file on GitHub
        return self._update_json_file('products.json', current_data)
    
    def upload_image(self, image_path, filename):
        """Upload image to data repo"""
        url = f'{self.base_url}/contents/images/products/{filename}'
        
        # Read image file
        with open(image_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        
        data = {
            'message': f'Add product image: {filename}',
            'content': content,
            'branch': 'main'
        }
        
        response = requests.put(url, json=data, headers=self._headers())
        
        if response.status_code in [201, 200]:
            return self._get_cdn_url(filename)
        else:
            raise Exception(f'Failed to upload image: {response.json()}')
    
    def _update_json_file(self, filename, data):
        """Update JSON file in repository"""
        url = f'{self.base_url}/contents/{filename}'
        
        # Get current file SHA
        sha = self.get_file_sha(filename)
        
        # Prepare content
        content_str = json.dumps(data, indent=2)
        content_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        
        payload = {
            'message': f'Update {filename}',
            'content': content_b64,
            'branch': 'main'
        }
        
        if sha:
            payload['sha'] = sha
        
        response = requests.put(url, json=payload, headers=self._headers())
        
        if response.status_code in [200, 201]:
            return True
        else:
            raise Exception(f'Failed to update {filename}: {response.json()}')
    
    def _get_cdn_url(self, filename):
        """Get CDN URL for uploaded image"""
        return f'https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/images/products/{filename}'
    
    def get_products(self):
        """Get list of all products"""
        data = self.get_current_products()
        return data.get('products', [])
    
    def update_product(self, index, product_data):
        """Update a product at specific index"""
        # Get current data
        current_data = self.get_current_products()
        products = current_data['products']
        
        # Validate index
        if index < 0 or index >= len(products):
            raise ValueError(f'Product index {index} out of range')
        
        # Preserve the ID from the existing product
        existing_id = products[index].get('id')
        if existing_id:
            product_data['id'] = existing_id
        
        # Update the product
        products[index] = product_data
        current_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save to GitHub
        return self._update_json_file('products.json', current_data)
    
    def delete_product(self, index):
        """Delete a product at specific index"""
        # Get current data
        current_data = self.get_current_products()
        products = current_data['products']
        
        # Validate index
        if index < 0 or index >= len(products):
            raise ValueError(f'Product index {index} out of range')
        
        # Get product info before deleting (for logging)
        deleted_product = products[index]
        
        # Remove the product
        products.pop(index)
        current_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save to GitHub
        result = self._update_json_file('products.json', current_data)
        
        return {
            'success': result,
            'deleted_product': deleted_product
        }
    
    def delete_image(self, image_url):
        """Delete an image from GitHub (optional cleanup)"""
        # Extract filename from URL
        filename = image_url.split('/')[-1]
        path = f'images/products/{filename}'
        
        # Get file SHA
        sha = self.get_file_sha(path)
        if not sha:
            return False  # Image doesn't exist
        
        url = f'{self.base_url}/contents/{path}'
        data = {
            'message': f'Delete product image: {filename}',
            'sha': sha,
            'branch': 'main'
        }
        
        response = requests.delete(url, json=data, headers=self._headers())
        return response.status_code == 200
