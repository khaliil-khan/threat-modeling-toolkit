from flask import Blueprint

dfd_bp = Blueprint('dfd', __name__)

from . import routes