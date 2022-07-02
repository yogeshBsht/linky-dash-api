from flask import Flask
# from flask_cors import CORS
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
# app.config["DEBUG"] = True

# CORS(app)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)

from models import User, Link, Visitor
import routes

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Link': Link, 'Visitor': Visitor}