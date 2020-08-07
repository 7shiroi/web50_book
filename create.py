import os

from flask import Flask, render_template, request
from models import *

app = Flask(__name__)
ENV = 'PROD'
dbcon = ''

if ENV == 'DEV':
    app.debug = True
    app.config['SQLALCHEMY_ECHO'] = True
    dbcon = 'postgres-local'
else:
    app.debug = False
    app.config['SQLALCHEMY_ECHO'] = False
    dbcon = 'postgres-heroku'
app.config['SQLALCHEMY_DATABASE_URI'] = dbcon
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()
