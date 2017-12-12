from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, PasswordField, DecimalField, IntegerField, DateField, validators, ValidationError
import firebase_admin
from firebase_admin import credentials, db
import datetime
cred = credentials.Certificate('./cred/nobesity-it1705-firebase-adminsdk-xo793-bbfa4432da.json')
default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://nobesity-it1705.firebaseio.com/'})
root = db.reference()
app = Flask(__name__)
app.secret_key = 'secret'


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
        self.username = username
        self.email = email
        self.password = password

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email

    def get_password(self):
        return self.password


def validate_login(form, field):
    valid = False
    for i in root.child('UserAccount').get():
        if field.data == i or field.data == root.child('UserAccount').get()[i]['email']:
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
    uid_db = root.child('UserAccount').get()
    if request.method == 'POST' and login_form.validate():
        login_id = request.form.to_dict()['username']
        valid = False
        try:
            if uid_db[login_id]['password'] == request.form.to_dict()['password']:
                valid = True
                session['username'] = login_id
        except KeyError:
            for i in uid_db:
                if uid_db[i]['email'] == login_id:
                    if uid_db[i]['password'] == request.form.to_dict()['password']:
                        valid = True
                        session['username'] = uid_db[i]
        finally:
            if valid is False:
                password_check = 'Invalid'
            else:
                session['logged_in'] = True
                return redirect(url_for('index'))
    return render_template('login.html', form=login_form, password_check=password_check)


def validate_uid(form, field):
    for i in root.child('UserAccount').get():
        if field.data == i:
            raise ValidationError('The username is already registered')


def validate_email(form, field):
    for i in root.child('UserAccount').get():
        try:
            if field.data == root.child('UserAccount').get()[i]['email']:
                raise ValidationError('The Email is already registered')
        except KeyError:
            pass


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
        session['username'] = signup_form.username.data
        return redirect(url_for('register_name'))
    return render_template('signup.html', form=signup_form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/timeline')
def timeline():
    session['logged_in'] = True
    return render_template('timeline.html')


class NameForm(Form):
    first_name = StringField('First Name', [validators.length(min=1, max=20), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.length(min=1, max=20), validators.DataRequired()])
    display_name = StringField('Display Name', [validators.length(min=1, max=20), validators.DataRequired()])


class AccountSetup:
    def __init__(self, first_name, last_name, display_name, gender, birth, height, weight_dict, bp_dict):
        self.first_name = first_name
        self.last_name = last_name
        self.display_name = display_name
        self.gender = gender
        self.birth = birth
        self.height = height
        self.weight_dict = weight_dict
        self.bp_dict = bp_dict

    def get_first_name(self):
        return self.first_name

    def get_last_name(self):
        return self.last_name

    def get_display_name(self):
        return self.display_name

    def get_gender(self):
        return self.gender

    def get_birth(self):
        return self.birth

    def get_height(self):
        return self.height

    def get_weight_dict(self):
        return self.weight_dict

    def get_bp_dict(self):
        return self.bp_dict


@app.route('/setup/name', methods=['GET', 'POST'])
def register_name():
    name_form = NameForm(request.form)
    if request.method == 'POST' and name_form.validate():
        root.child('UserAccount').child(session['username']).update({
            'first_name': name_form.first_name.data,
            'last_name': name_form.last_name.data,
            'display_name': name_form.display_name.data
        })
        return redirect(url_for('register_gender'))
    return render_template('firstTimeRegisterName.html', name_form=name_form)


class GenderForm(Form):
    gender = RadioField('Gender', [validators.DataRequired()], choices=[('male', 'Male'), ('female', 'Female')])


@app.route('/setup/gender', methods=['GET', 'POST'])
def register_gender():
    gender_form = GenderForm(request.form)
    if request.method == 'POST' and gender_form.validate():
        root.child('UserAccount').child(session['username']).update({
            'gender': gender_form.gender.data,
        })
        return redirect(url_for('register_info'))
    return render_template('firstTimeRegisterGender.html', gender_form=gender_form)


class MoreInfoForm(Form):
    height = DecimalField('Current Height (m)', places=2)
    current_weight = DecimalField('Current Weight (kg)', places=2)
    birth_day = SelectField('Day', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                                            ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                                            ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                            ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                            ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'),
                                            ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30'),
                                            ('31', '31')
                                            ]
                            )
    birth_month = SelectField('Month', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                                                ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                                                ('11', '11'), ('12', '12')
                                                ]
                              )
    birth_year = IntegerField('Year')
    

@app.route('/setup/moreinfo', methods=['GET', 'POST'])
def register_info():
    moreinfo_form = MoreInfoForm(request.form)
    register_date = '{:%Y-%m-%d}'.format(datetime.date.today())
    if request.method == 'POST' and moreinfo_form.validate():
        root.child('UserAccount').child(session['username']).update({
            'height': str(moreinfo_form.height.data),
            'weight_dict': {
                register_date: str(moreinfo_form.current_weight.data)
            },
            'birthday': str(moreinfo_form.birth_year.data) + '-' +
                        str(moreinfo_form.birth_month.data) + '-' +
                        str(moreinfo_form.birth_day.data)
        })
        return redirect(url_for('profile'))
    return render_template('firstTimeRegisterInfo.html', moreinfo_form=moreinfo_form)


class UserAccountSetupForm(Form):
    first_name = StringField('First Name', [validators.length(min=1, max=20), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.length(min=1, max=20), validators.DataRequired()])
    display_name = StringField('Display Name', [validators.length(min=1, max=20), validators.DataRequired()])
    gender = RadioField('Gender', [validators.DataRequired()], choices=[('male', 'Male'), ('female', 'Female')])
    current_weight = DecimalField('Current Weight (kg)', [validators.DataRequired()], places=2)
    birthday = DateField('Birthday')
    height = DecimalField('Current Height (m)', [validators.DataRequired()], places=2)
    systol = DecimalField('Systol')
    diastol = DecimalField('Diastol')
    pulse = DecimalField('Pulse')


@app.route('/account/info', methods=['GET', 'POST'])
def account_info():
    setup_date = '{:%Y-%m-%d}'.format(datetime.date.today())
    setup_form = UserAccountSetupForm(request.form)
    if request.method == 'POST' and setup_form.validate():
        first_name = setup_form.first_name.data
        last_name = setup_form.last_name.data
        display_name = setup_form.display_name.data
        gender = setup_form.gender.data
        birthday = str(setup_form.birthday.data)
        height = str(setup_form.height.data)
        weight_dict = {setup_date: str(setup_form.current_weight.data)}
        bp_dict = {
            setup_date: {
                'systol': str(setup_form.systol.data),
                'diastol': str(setup_form.diastol.data),
                'pulse': str(setup_form.pulse.data)
            }
        }
        user_setup = AccountSetup(first_name, last_name, display_name, gender, birthday, height, weight_dict, bp_dict)
        root.child('UserAccount').child(session['username']).update({
            'first_name': user_setup.get_first_name(),
            'last_name': user_setup.get_last_name(),
            'display_name': user_setup.get_display_name(),
            'gender': user_setup.get_gender(),
            'birthday': user_setup.get_birth(),
            'height': user_setup.get_height(),
            'weight_dict': user_setup.get_weight_dict(),
            'bp_dict': user_setup.get_bp_dict()
        })
        return redirect(url_for('account_info'))
    return render_template('accountInfo.html', setup_form=setup_form)


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/plans')
def plans():
    return render_template('plans.html')



class Diet:
    def __init__(self,name,type,calories,fats,carbohydrates,protein):
        self.dietID = ''
        self.name = name
        self.type = type
        self.calories = calories
        self.fats = fats
        self.carbohydrates = carbohydrates
        self.protein = protein

    def get_dietID(self):
        return self.dietID

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type

    def get_calories(self):
        return self.calories

    def get_fats(self):
        return self.fats

    def get_carbohydrates(self):
        return self.carbohydrates

    def get_protein(self):
        return self.protein

    def set_dietID(self,dietID):
        self.dietID = dietID

    def set_name(self, name):
        self.name = name

    def set_type(self, type):
        self.type = type

    def set_calories(self,calories):
        self.calories = calories

    def set_fats(self, fats):
            self.fats = fats

    def set_carbohydrates(self,cabohydrates):
        self.cabohydrates = cabohydrates

    def set_protein(self,protein):
        self.protein = protein


@app.route('/diet')
def diet():
    Diet_db = root.child('Food').get()
    diet_list = []
    for dietID in Diet_db:
        eachdiet = Diet_db[dietID]
        food = Diet(eachdiet['Name'],eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                    eachdiet['Carbohydrates Value'], eachdiet['Protein Value'] )
        food.set_dietID(dietID)
        diet_list.append(food)

    return render_template('diet.html', diet=diet_list)


class Food(Form):
    diet_name = StringField('Name',[validators.length(min=1,max=150),validators.DataRequired()])
    diet_type = SelectField('Type',[validators.DataRequired()],choices=[("","Select"),("Foods","Foods"),("Drinks","Drinks"),("Fruits","Fruits")])
    calories = IntegerField('Calories Value')
    fats = IntegerField('Fats Value')
    carbohydrates = IntegerField('Carbohydrates Value')
    proteins = IntegerField('Protein Value')


@app.route('/new_diet', methods=['GET','POST'])
def new_diet():
    new_form = Food(request.form)
    if request.method == 'POST' and new_form.validate():
            name = new_form.diet_name.data
            type = new_form.diet_type.data
            calories = new_form.calories.data
            fats = new_form.fats.data
            carbohydrates = new_form.carbohydrates.data
            protein = new_form.proteins.data
            food_diet = Diet(name, type, calories, fats, carbohydrates, protein)
            food_diet.db = root.child('Food')
            food_diet.db.push({'Name': food_diet.get_name(), 'Type': food_diet.get_type(),
                      'Calories Value': food_diet.get_calories(), 'Fats Value': food_diet.get_fats(),
                      'Carbohydrates Value': food_diet.get_carbohydrates(),'Protein Value': food_diet.get_protein()
            })
            flash('New Diet inserted successfully', 'success')

            return redirect(url_for('diet'))

    return render_template('new_diet.html', form=new_form)


@app.route('/update_diet/<string:id>', methods=['GET','POST'])
def update_diet(id):
    update_form = Food(request.form)
    if request.method == 'POST' and update_form.validate():
        name = update_form.diet_name.data
        food_type = update_form.diet_type.data
        calories = update_form.calories.data
        fats = update_form.fats.data
        carbohydrates = update_form.carbohydrates.data
        protein = update_form.proteins.data
        food_diet = Diet(name,food_type, calories,fats,carbohydrates,protein)
        Diet_db = root.child('Food/' + id)
        Diet_db.set({'Name': food_diet.get_name(), 'Type': food_diet.get_type(),'Calories Value': food_diet.get_calories(),
                    'Fats Value': food_diet.get_fats(), 'Carbohydrates Value': food_diet.get_carbohydrates(),
                     'Protein Value': food_diet.get_protein()})
        flash('Diet updated successfully', 'success')

        return redirect(url_for('diet'))
    else:
        url = 'Food/' + id
        eachdiet = root.child(url).get()
        food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                    eachdiet['Carbohydrates Value'], eachdiet['Protein Value'])
        food.set_dietID(id)
        update_form.diet_name.data = food.get_name()
        update_form.diet_type.data = food.get_type()
        update_form.calories.data = food.get_calories()
        update_form.fats.data = food.get_fats()
        update_form.carbohydrates.data = food.get_carbohydrates()
        update_form.proteins.data = food.get_protein()

        return render_template('update_diet.html', form=update_form)


@app.route('/delete_diet/<string:id>', methods=['POST'])
def delete_diet(id):
    Diet_db = root.child('Food/' + id)
    Diet_db.delete()
    flash('Diet deleted','Success')

    return redirect(url_for('diet'))


@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/record')
def record():
    return render_template('track_and_record.html')


@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


@app.route('/leaderboards')
def leaderboards():
    return render_template('leaderboards.html')


if __name__ == '__main__':
    app.run()
