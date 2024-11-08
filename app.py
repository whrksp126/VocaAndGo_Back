from app import create_app, db
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS




app = create_app()
migrate = Migrate(app, db)





if __name__ == '__main__':
    
    app.run(debug=True)