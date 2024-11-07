from app import create_app, db
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from app.init import start_scheduler

# login_manager = LoginManager()

app = create_app()
migrate = Migrate(app, db)
# login_manager.init_app(app)
# login_manager.login_view = "main_login.html"
# CORS(app)

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)