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
