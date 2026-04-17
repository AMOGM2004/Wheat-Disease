# This file makes the routes folder a Python package
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
farmer_bp = Blueprint('farmer', __name__)
admin_bp = Blueprint('admin', __name__)

from . import auth, farmer, admin