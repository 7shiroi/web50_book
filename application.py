import os
import requests

from flask import Flask, session, render_template, jsonify, request, flash, redirect, url_for, logging
from flask_session import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from functools import wraps

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


# # Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db.init_app(app)

username = None

# Set up database
# engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine(dbcon)
db = scoped_session(sessionmaker(bind=engine))

def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login_page', next=request.url))
    return decorated_function

@app.route("/")
@is_logged_in
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")
    
@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        errors = []

        user = db.query(User).filter_by(username = username).first()

        if not user:
            errors.append("Login failed (user not found)")
        else:
            if sha256_crypt.verify(password, user.password):
                session['logged_in'] = True
                session['username'] = username
                
                return redirect(url_for("index"))
            else:
                errors.append("Login failed (password incorrect)")

        if len(errors) > 0 :
            return render_template("login.html", errors = errors)
        
    # return render_template("login.html", errors = errors)


@app.route('/register')
def register_page():
    return render_template("register.html")

    
@app.route("/register", methods=['POST'])
def register_user():
    if request.method == 'POST':
        errors = []
        # validation
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            errors.append("Password doesn't match")

        user = User.query.filter_by(username = username).all()
        if user:
            errors.append("Username is already used")

        user = User.query.filter_by(email = email).all()
        if user:
            errors.append("Email is already used")

        if len(errors) == 0:
            password = sha256_crypt.encrypt(str(request.form.get('password')))
            user = User(username = username, password = password, name = name, email = email)
            user.add_user(username = username, password = password, name = name, email = email)
            flash("User registered")
            return redirect(url_for("login"))
        else:
            return render_template("register.html", errors = errors)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route('/books/<int:page_num>', methods=['get'])
@is_logged_in
def books_list(page_num):
    if request.args.get('searchAnyValue') != None:
        books = Book.query.filter(
            (Book.isbn.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.title.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.author.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.release.ilike('%'+request.args.get('searchAnyValue')+'%'))).paginate(per_page=20, page=page_num, error_out=True)
        return render_template("book/list.html", books = books, searchAnyValue = request.args.get('searchAnyValue'))
    else:
        books = Book.query.paginate(per_page=20, page=page_num, error_out=True)
        return render_template("book/list.html", books = books)


# @app.route('/books/<int:page_num>')
# @is_logged_in
# def books_list(page_num):
#     books = Book.query.paginate(per_page=20, page=page_num, error_out=True)
#     return render_template("book/list.html", books = books)


@app.route('/books', methods=["GET"])
@is_logged_in
def books_list0(page_num=1):
    if request.args.get('searchAnyValue') != None:
        books = Book.query.filter(
            (Book.isbn.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.title.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.author.ilike('%'+request.args.get('searchAnyValue')+'%'))
            | (Book.release.ilike('%'+request.args.get('searchAnyValue')+'%'))).paginate(per_page=20, page=page_num, error_out=True)
        return render_template("book/list.html", books = books, searchAnyValue= request.args.get('searchAnyValue'))
    else:
        books = Book.query.paginate(per_page=20, page=page_num, error_out=True)
        return render_template("book/list.html", books = books)

# @app.route('/books')
# @is_logged_in
# def books_list0(page_num=1):
#     books = Book.query.paginate(per_page=20, page=page_num, error_out=True)
#     return render_template("book/list.html", books = books)
   
@app.route('/review/<int:book_id>')
@is_logged_in
def book_review(book_id):
    # get book details
    book = Book.query.get(book_id)
    if book is None:
        return render_template("error.html", message="Book not founded.")

    # get book rating info
    rating = Review.query.with_entities(func.avg(Review.rating).label('average_rating'), func.count(Review.rating).label('ratings_count')).filter(Review.book_id == book_id).first()

    # get goodreads rating info
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "V3fDKiHPaVcMyeYTIGMlJw", "isbns" : book.isbn})
    if res.status_code != 200:
        return render_template("error.html", message="Can't retreive data from GoodReads.")
    data = res.json()
    grRating = {}
    grRating['average_rating'] = data['books'][0]['average_rating']
    grRating['ratings_count'] = data['books'][0]['ratings_count']

    # get user's review
    rev = Review.query.filter_by(username = session['username']).first()
    review = {}
    review['status'] = False
    if rev:
        review['status'] = True
        review['rating'] = rev.rating
        review['review'] = rev.review
        review['username'] = rev.username

    return render_template("book/review.html", book = book, grRating = grRating, userRating = rating, review = review)

@app.route('/review/<int:book_id>', methods=["GET", "POST"])
@is_logged_in
def book_review_post(book_id):
    if request.method == "POST":
        errors = []

        data = {}
        data['review'] = request.form.get('review')
        data['rating'] = request.form.get('rating')

        if int(data['rating']) < 1 or int(data['rating']) > 5:
            errors.append("Rating must be between 1 and 5")
        
        if len(errors) > 0:
            return render_template(url_for("book_review", book_id = book_id), data = data, errors = errors)
        else:
            reviews = Review(book_id = book_id, username = session['username'], rating = data['rating'], review = data['review'])
            reviews.add_review(book_id = book_id, username = session['username'], rating = data['rating'], review = data['review'])
            flash('Your review has been posted!')
            return redirect(url_for("book_review", book_id = book_id))

    else:
        book = Book.query.get(book_id)
        if book is None:
            return render_template("error.html", message="Book not founded.")

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "V3fDKiHPaVcMyeYTIGMlJw", "isbns" : book.isbn})
        if res.status_code != 200:
            return render_template("error.html", message="Can't retreive data from GoodReads.")
        data = res.json()
        grRating = {}
        grRating['average_rating'] = data['books'][0]['average_rating']
        grRating['ratings_count'] = data['books'][0]['ratings_count']
        return render_template("book/review.html", book = book, grRating = grRating)

@app.route("/api/<isbn>")
def book_api(isbn):
    """Return details about a book."""

    # Make sure book exists.
    book = Book.query.filter_by(isbn = isbn).first()
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 422

    # Get rating info.
    rating = Review.query.with_entities(func.avg(Review.rating).label('average_rating'), func.count(Review.rating).label('ratings_count')).filter(Review.book_id == book.id).first()
    average_rating = str("{:.2f}".format(rating.average_rating))
    print("{:.2f}".format(rating.average_rating))

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.release,
            "isbn": book.isbn,
            "review_count": rating.ratings_count,
            "average_count": average_rating
        })


if __name__ == '__main__':
    app.run()
