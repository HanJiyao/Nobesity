from flask import Flask, render_template, request
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, validators

app = Flask(__name__)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def timeline():
    return render_template('timeline.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/plans')
def plans():
    return render_template('plans.html')


@app.route('/diet')
def diet():
    return render_template('healthy_diet.html')


@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


if __name__ == '__main__':
    app.run()