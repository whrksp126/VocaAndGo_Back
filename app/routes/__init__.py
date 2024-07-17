from flask import Blueprint

login_bp = Blueprint('login', __name__, url_prefix='/login')
search_bp = Blueprint('search', __name__, url_prefix='/search')
tts_bp = Blueprint('tts', __name__, url_prefix='/tts')


from app.routes import login
from app.routes import search
from app.routes import tts