# routes/__init__.py
from .users_routes import login
from .users_routes  import auth_register

__all__ = ['login', 'auth_register']