import os

from flask import Flask, render_template, request
from models import *

app = Flask(__name__)
ENV = 'PROD'
dbcon = ''

if ENV == 'DEV':
    app.debug = True
    app.config['SQLALCHEMY_ECHO'] = True
    dbcon = 'postgresql://postgres:N3wd0r14@127.0.0.1/project1'
else:
    app.debug = False
    app.config['SQLALCHEMY_ECHO'] = False
    dbcon = 'postgres://ykazctrurcyqki:e0140a8b8637ee5b22906c588e53b7445d630d2736f52c43f3e718aade5f8f13@ec2-54-81-37-115.compute-1.amazonaws.com:5432/ddp1qc9fuitp0j'
app.config['SQLALCHEMY_DATABASE_URI'] = dbcon
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()
