from flask import render_template, redirect, url_for, request, session, jsonify
from app.routes import search_bp

@search_bp.route('/')
def index():
    return render_template('index.html')
