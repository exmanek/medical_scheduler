from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from models import User

def hash_password(password: str) -> str:
    """Hash a password using Werkzeug's default hashing (scrypt/pbkdf2)."""
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """Verify a password against its hash."""
    return check_password_hash(password_hash, password)

def login_user(user: User):
    """Store user information in Flask session."""
    session['user_id'] = user.id
    session['role'] = user.role
    session.permanent = True  # session remains active according to app configuration

def logout_user():
    """Clear user information from Flask session."""
    session.pop('user_id', None)
    session.pop('role', None)

def get_current_user() -> User:
    """Retrieve the currently logged-in user from the database, if any."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require one of the specified roles for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': f'Access forbidden. Requires one of roles: {list(allowed_roles)}'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
