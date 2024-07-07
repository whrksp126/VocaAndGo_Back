from flask import Blueprint

login_bp = Blueprint('login', __name__, url_prefix='/login')
search_bp = Blueprint('search', __name__, url_prefix='/search')
ocr_bp = Blueprint('ocr', __name__, url_prefix='/ocr')


from app.routes import login
from app.routes import search
from app.routes import ocr
