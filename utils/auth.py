from functools import wraps
from flask import session, redirect, url_for, request
import os

def check_auth(username, password):
    """Check if username/password is valid"""
    return (username == os.getenv('ADMIN_USERNAME') and 
            password == os.getenv('ADMIN_PASSWORD'))

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
