from flask import Flask, render_template, request
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, validators

import firebase_admin
app = Flask(__name__)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/timeline')
def timeline():
    return render_template('timeline.html')


@app.route('/registerGender')
def registergender():
    return render_template('firstTimeRegistGender.html')


@app.route('/registerInfo')
def registerinfo():
    return render_template('firstTimeRegistInfo.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/accountinfo')
def accountinfo():
    return render_template('accountinfo.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/plans')
def plans():
    return render_template('plans.html')



@app.route('/diet')
def diet():
    return render_template('Reference/healthy_diet.html')

class nutrition_food(Form):
    food_name = StringField('name',[validators.length(min=1,max=150),validators.DataRequired()])
    food_type = StringField('Type',[validators.length(min=1,max=150),validators.DataRequired()])
    calories = StringField('Calories value',[validators.length(min=1,max=3),validators.DataRequired()])
    fats = StringField('Fats value',[validators.length(min=1,max=3),validators.DataRequired()])
    carbohydrates = StringField('Carbohydrates value',[validators.length(min=1,max=3),validators.DataRequired()])
    proteins = StringField('Protein value',[validators.length(min=1,max=3),validators.DataRequired()])

@app.route('/create_nutrition')
def new_food():
    form = nutrition_food(request.form)
    if request.method == 'POST' and form.validate():
        name = form.food_name.data
        type = form.food_type.data
        calories = form.calories.data
        fats = form.fats.data
        carbohydrates = form.carbohydrates.data
        protein = form.proteins.data



@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


@app.route('/bread')
def bread():
    return render_template('Reference/bread.html')

@app.route('/porridge')
def porridge():
    return render_template('Reference/porridge.html')


@app.route('/oats')
def oats():
    return render_template('Reference/oats.html')


@app.route('/salad')
def salad():
    return render_template('Reference/salad.html')


@app.route('/juices')
def juices():
    return render_template('Reference/juices.html')


@app.route('/kway_teow_soup')
def kway_teow_soup():
    return render_template('Reference/kway_teow_soup.html')


@app.route('/fishsoup')
def fishsoup():
    return render_template('Reference/fishsoup.html')


@app.route('/herbalsoup')
def herbalsoup():
    return render_template('Reference/herbalsoup.html')


@app.route('/seafoodsoup')
def seafoodsoup():
    return render_template('Reference/seafoodsoup.html')


@app.route('/leaderboards')
def leaderboards():
    return render_template('leaderboards.html')


if __name__ == '__main__':
    app.run()
