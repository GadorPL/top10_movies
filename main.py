from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DETAILS_URL ="https://api.themoviedb.org/3/movie"
IMAGE_PATH = "https://image.tmdb.org/t/p/w500"
api_key = "ce6d35f80cfdb264c7cc8680499ab0aa"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    rating = FloatField("Your rating Out of 10 e.g. 7.5", validators=[DataRequired(), NumberRange(0, 10)])
    review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    movies = db.session.query(Movie).order_by(Movie.rating).all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        # UPDATE RECORD
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    movie_title = form.title.data
    if form.validate_on_submit():
        response = requests.get(url=MOVIE_DB_SEARCH_URL, params={"api_key": api_key, "query": movie_title})
        data = response.json()["results"]
        return render_template('select.html', data=data)

    return render_template('add.html', form=form)


@app.route("/find", methods=["GET", "POST"])
def find():
    movie_id = request.args.get("id")
    if movie_id:
        response = requests.get(url=f"{MOVIE_DETAILS_URL}/{movie_id}", params={"api_key": api_key})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{IMAGE_PATH}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
