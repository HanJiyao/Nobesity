from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, PasswordField, validators, ValidationError
from Diet import Diet
import firebase_admin
from firebase_admin import credentials, db
cred = credentials.Certificate('./cred/nobesity-it1705-firebase-adminsdk-xo793-bbfa4432da.json')
default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://nobesity-it1705.firebaseio.com/'})
root = db.reference()
app = Flask(__name__)
app.secret_key = 'secret'
UserId_db = root.child('UserAccount').get()

uid_db = {}
for key in UserId_db:
    uid_db[key] = UserId_db[key]

class RequiredIf(object):
    def __init__(self, *args, **kwargs):
        self.conditions = kwargs

    def __call__(self, form, field):
        for name, data in self.conditions.items():
            if name not in form._fields:
                validators.Optional()(field)
            else:
                condition_field = form._fields.get(name)
                if condition_field.data == data:
                    validators.DataRequired().__call__(form, field)
                else:
                    validators.Optional().__call__(form, field)


@app.route('/')
def index():
    if session.get('logged_in') is True:
        return redirect(url_for('timeline'))
    return render_template('home.html')


class UserAccount:
    def __init__(self, username, email, password):
        self.__username = username
        self.__email = email
        self.__password = password

    def get_username(self):
        return self.__username

    def get_email(self):
        return self.__email

    def get_password(self):
        return self.__password


def validate_login(form, field):
    valid = False
    for i in uid_db:
        if field.data == i or field.data == uid_db[i]['email']:
            valid = True
    if valid is False:
        raise ValidationError('Invalid User Name or Email')


class LoginForm(Form):
    username = StringField('Email / User Name', [validators.data_required(), validate_login])
    password = PasswordField('Password', [validators.data_required()])


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    password_check = ''
    if request.method == 'POST' and login_form.validate():
        login_id = request.form.to_dict()['username']
        valid = False
        try:
            if uid_db[login_id]['password'] == request.form.to_dict()['password']:
                valid = True
        except KeyError:
            for i in uid_db:
                if uid_db[i]['email'] == login_id:
                    if uid_db[i]['password'] == request.form.to_dict()['password']:
                        valid = True
        finally:
            if valid is False:
                password_check = 'Invalid'
            else:
                session['logged_in'] = True
                return redirect(url_for('index'))
    return render_template('login.html', form=login_form, password_check=password_check)


def validate_uid(form, field):
    for i in uid_db:
        if field.data == i:
            raise ValidationError('The username is already registered')


def validate_email(form, field):
    for i in uid_db:
        if field.data == uid_db[i]['email']:
            raise ValidationError('The Email is already registered')


class SignUpForm(Form):
    username = StringField('User Name', [
        validators.length(min=5, max=20),
        validators.DataRequired(),
        validate_uid])
    email = StringField('Email', [
        validators.email(),
        validators.DataRequired(),
        validate_email])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignUpForm(request.form)
    if request.method == 'POST' and signup_form.validate():
        user_account = UserAccount(
            signup_form.username.data,
            signup_form.email.data,
            signup_form.password.data
        )
        user_db = root.child('UserAccount')
        user_db.child(user_account.get_username()).set({
            'email': user_account.get_email(),
            'password': user_account.get_password()
        })
        session['logged_in'] = True
        return redirect(url_for('register_name'))
    return render_template('signup.html', form=signup_form)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/timeline')
def timeline():
    session['logged_in'] = True
    return render_template('timeline.html')


@app.route('/registerName')
def register_name():
    return render_template('firstTimeRegisterName.html')


@app.route('/registerGender')
def register_gender():
    return render_template('firstTimeRegisterGender.html')


@app.route('/registerInfo')
def register_info():
    return render_template('firstTimeRegisterInfo.html')


@app.route('/accountinfo')
def accountinfo():
    return render_template('accountinfoDisplay.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/plans')
def plans():
    return render_template('plans.html')


@app.route('/diet')
def diet():
    return render_template('diet.html')


class Food(Form):
    food_name = StringField('Name',[validators.length(min=1,max=150),validators.DataRequired()])
    food_type = StringField('Type',[validators.length(min=1,max=150),validators.DataRequired()])
    calories = StringField('Calories value',[validators.length(min=1,max=3),validators.DataRequired()])
    fats = StringField('Fats value',[validators.length(min=1,max=3),validators.DataRequired()])
    carbohydrates = StringField('Carbohydrates value',[validators.length(min=1,max=3),validators.DataRequired()])
    proteins = StringField('Protein value',[validators.length(min=1,max=3),validators.DataRequired()])


@app.route('/new_diet', methods=['GET','POST'])
def new_diet():
    new_form = Food(request.form)
    if request.method == 'POST' and new_form.validate():
            name = new_form.food_name.data
            type = new_form.food_type.data
            calories = new_form.calories.data
            fats = new_form.fats.data
            carbohydrates = new_form.carbohydrates.data
            protein = new_form.proteins.data
            food_diet = Diet(name, type, calories, fats, carbohydrates, protein)
            food_diet.db = root.child('Food')
            food_diet.db.push({'Name': food_diet.get_name(), 'Type': food_diet.get_type(),
                      'Calories value': food_diet.get_calories(), 'Fats Value': food_diet.get_fats(),
                      'Carbohydrates value': food_diet.get_carbohydrates(),'Protein value': food_diet.get_protein()
            })
            flash('New Diet inserted successfully', 'success')
            return redirect(url_for('diet'))
    return render_template('new_diet.html', form=new_form)


@app.route('/update_diet')
def update_diet():
    update_form = Food(request.form)
    if request.method =='POST' and update_form.validate():
        name = update_form.food_name.data
        food_type = update_form.food_type.data
        calories = update_form.calories.data
        fats = update_form.fats.data
        carbohydrates = update_form.carbohydrates.data
        protein = update_form.proteins.data
        food_diet = Diet(name,food_type,calories,fats,carbohydrates,protein)
        food_diet.db = root.child('Food')
        food_diet.db.push({'Name': food_diet.get_name(), 'Type': food_diet.get_type(),'Calories value': food_diet.get_calories(),
                      'Fats Value': food_diet.get_fats(), 'Carbohydrates value': food_diet.get_carbohydrates(),
                      'Protein value': food_diet.get_protein()})
        flash('Diet updated successfully', 'success')
        return redirect(url_for('diet'))
    return render_template('update_diet.html', form=update_form)


@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


@app.route('/leaderboards')
def leaderboards():
    return render_template('leaderboards.html')


if __name__ == '__main__':
    app.run()
