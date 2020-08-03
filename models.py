import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    release = db.Column(db.String, nullable=False)
    reviews = db.relationship("Review", backref="book", lazy=True)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    reviews = db.relationship("Review", backref="user", lazy=True)

    def add_user(self, username, password, name, email):
        u = User(username=self.username, password=self.password, name=self.name, email=self.email)
        db.session.add(u)
        db.session.commit()

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, db.ForeignKey("users.username"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String, nullable=True)

    def add_review(self, username, book_id, review, rating):
        r = Review(username=self.username, book_id=self.book_id, review=self.review, rating=self.rating)
        db.session.add(r)
        db.session.commit()