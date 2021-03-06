from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, PasswordField, DecimalField, \
    IntegerField, DateField, validators, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, db
import datetime
import math


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
        return redirect(url_for('dashboard'))
    return render_template('home.html')


class UserAccount:
    def __init__(self, username, email):
        self.username = username
        self.email = email
        # self.password = password

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email

    # def get_password(self):
        # return self.password


# def validate_login(form, field):
#     valid = False
#     for i in root.child('UserAccount').get():
#         if field.data == i or field.data == root.child('UserAccount').get()[i]['email']:
#             valid = True
#     if valid is False:
#         raise ValidationError('Invalid User Name or Email')


class LoginForm(Form):
    username = StringField('Email / User Name')
    password = PasswordField('Password')


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    # password_check = ''
    uid_db = root.child('Users/Account').get()
    if request.method == 'POST' and login_form.validate():
        login_id = request.form.to_dict()['username']
        valid = False
        # try:
        #     if check_password_hash(pwhash=uid_db[login_id]['pwhash'],
        #                            password=str(request.form.to_dict()['password'])) is True:
        #     if
        #         valid = True
        #         session['username'] = login_id
        # except KeyError:
        print(uid_db)
        for i in uid_db:
            print(uid_db[i])
            if uid_db[i]['email'] == login_id:
                # if check_password_hash(pwhash=uid_db[i]['pwhash'],
                #                        password=str(request.form.to_dict()['password'])) is True:
                    valid = True
                    session['username'] = i
        # finally:
        if valid is False:
            password_check = 'Invalid'
        else:
            session['logged_in'] = True
            flash('Welcome Back, ' + session['username'], 'primary')
            return redirect(url_for('profile'))

    return render_template('login.html', form=login_form)


def validate_uid(form, field):
    for i in root.child('Users/Account').get():
        if field.data == i:
            raise ValidationError('The username is already registered')


def validate_email(form, field):
    for i in root.child('Users/Account').get():
        try:
            if field.data == root.child('Users/Account').get()[i]['email']:
                raise ValidationError('The Email is already registered')
        except KeyError:
            pass
        except TypeError:
            pass


class SignUpForm(Form):
    username = StringField('User Name', [
        validators.length(min=4, max=20),
        validators.DataRequired(),
        validate_uid])
    email = StringField('Email', [
        validators.email(),
        validators.length(min=4, max=20),
        validators.DataRequired(),
        validate_email])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.length(min=6, max=20),
        validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignUpForm(request.form)
    if request.method == 'POST' and signup_form.validate():
        user_account = UserAccount(
            signup_form.username.data,
            signup_form.email.data
            # generate_password_hash(signup_form.password.data)
        )
        user_db = root.child('Users/Account')
        user_db.child(user_account.get_username()).set({
            'email': user_account.get_email(),
            # 'pwhash': user_account.get_password()
        })
        session['logged_in'] = True
        session['username'] = signup_form.username.data
        flash('You are successfully signed up as ' + session['username'], 'success')
        return redirect(url_for('verify_email'))
    return render_template('signup.html', form=signup_form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    session['logged_in'] = True
    return render_template('dashboard.html')


class HealthDetailSetup:
    def __init__(self, gender, birth, height, weight_dict, bp_dict):
        # self.__first_name = first_name
        # self.__last_name = last_name
        # self.__display_name = display_name
        self.__gender = gender
        self.__birth = birth
        self.__height = height
        height = float(height)
        self.__weight_dict = weight_dict
        self.__bp_dict = bp_dict
        today = '{:%Y%m%d}'.format(datetime.date.today())
        weight_date = []
        for i in weight_dict:
            weight_date.append(i)
        weight_date.sort()
        current_weight = float(weight_dict[weight_date[-1]])
        self.__age = int(str(int(today) - int(birth))[:2])
        self.__current_weight = round(current_weight, 1)
        self.__bmi = round(float(current_weight) / (height ** 2), 1)
        if gender == 'male':
            gender_index = 1
            self.__suggest_bfp = '21 - 30%'
            self.__suggest_cal = math.ceil(9.99 * current_weight + 6.25 * height * 100 - 4.92 * self.__age + 5)
        else:
            gender_index = 0
            self.__suggest_bfp = '14 - 25%'
            self.__suggest_cal = math.ceil(9.99 * current_weight + 6.25 * height * 100 - 4.92 * self.__age - 161)
        if self.__age < 18:
            self.__bfp = round(self.__bmi * 1.51 - 0.70 * self.__age - 3.6 * gender_index + 1.4, 1)
        else:
            self.__bfp = round(self.__bmi * 1.20 + 0.23 * self.__age - 10.8 * gender_index - 5.4, 1)
        self.__suggest_cal_range = str(math.ceil(self.__suggest_cal * 0.9)) + ' - ' + str(
            math.ceil(self.__suggest_cal * 1.1))
        self.__suggest_weight_min = math.ceil(18.5 * (height ** 2))
        self.__suggest_weight_max = math.ceil(23 * (height ** 2))
        self.__suggest_weight = str(self.__suggest_weight_min) + ' - ' + str(self.__suggest_weight_max)
        bp_time = []
        for i in bp_dict:
            bp_time.append(i)
        bp_time.sort()
        self.__current_pulse = int(bp_dict[bp_time[-1]]['pulse'])
        self.__current_systolic = int(bp_dict[bp_time[-1]]['systolic'])
        self.__current_diastolic = int(bp_dict[bp_time[-1]]['diastolic'])
        self.__hr_hrr = 207 - self.__age * 0.7 - int(self.__current_pulse)
        self.__suggest_hr_min = math.ceil(0.5 * self.__hr_hrr)
        self.__suggest_hr_max = math.ceil(0.85 * self.__hr_hrr)
        self.__suggest_hr = str(self.__suggest_hr_min) + ' - ' + str(self.__suggest_hr_max)
        self.__diet_grade = 10
        self.__quiz_grade = 5
        self.__activity_grade = 10
        self.__plan_grade = 15
        self.__bmi_grade = 0
        if 18.5 < self.__bmi < 22.9:
            self.__bmi_grade = 20
        self.__bfp_grade = 0
        if gender == 'male':
            if 21 < self.__bfp < 30:
                self.__bfp_grade = 20
        if gender == 'female':
            if 14 < self.__bfp < 25:
                self.__bfp_grade = 20
        self.__bp_grade = 0
        if 120 < self.__current_systolic < 140 and 80 < self.__current_diastolic < 90:
            self.__bp_grade = 20
        self.__grade = (self.__diet_grade + self.__quiz_grade + self.__activity_grade + self.__plan_grade +
                        self.__bmi_grade + self.__bfp_grade + self.__bp_grade)
        if 80 <= self.__grade <= 100:
            self.__grade_display = 'A'
        elif 60 <= self.__grade < 80:
            self.__grade_display = 'B'
        elif 40 <= self.__grade < 60:
            self.__grade_display = 'C'
        elif 20 <= self.__grade < 40:
            self.__grade_display = 'D'
        elif 0 <= self.__grade < 20:
            self.__grade_display = 'E'

    # def get_first_name(self):
    #     return self.__first_name
    #
    # def get_last_name(self):
    #     return self.__last_name
    #
    # def get_display_name(self):
    #     return self.__display_name

    def get_gender(self):
        return self.__gender

    def get_birth(self):
        return self.__birth

    def get_height(self):
        return self.__height

    def get_weight_dict(self):
        return self.__weight_dict

    def get_bp_dict(self):
        return self.__bp_dict

    def get_current_weight(self):
        return self.__current_weight

    def get_bmi(self):
        return self.__bmi

    def get_bfp(self):
        return self.__bfp

    def get_suggest_weight(self):
        return self.__suggest_weight

    def get_suggest_bfp(self):
        return self.__suggest_bfp

    def get_suggest_cal(self):
        return self.__suggest_cal

    def get_suggest_cal_range(self):
        return self.__suggest_cal_range

    def get_suggest_hr(self):
        return self.__suggest_hr

    def get_current_pulse(self):
        return self.__current_pulse

    def get_current_systolic(self):
        return self.__current_systolic

    def get_current_diastolic(self):
        return self.__current_diastolic

    def get_grade(self):
        return self.__grade

    def get_grade_display(self):
        return self.__grade_display


@app.route('/setup/email' ,methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        return redirect(url_for('register_name'))
    return render_template('verifyEmail.html')


class NameForm(Form):
    # first_name = StringField('First Name', [validators.length(min=1, max=20), validators.DataRequired()])
    # last_name = StringField('Last Name', [validators.length(min=1, max=20), validators.DataRequired()])
    display_name = StringField('Display Name', [validators.length(min=1, max=20), validators.DataRequired()])


@app.route('/setup/name', methods=['GET', 'POST'])
def register_name():
    name_form = NameForm(request.form)
    if request.method == 'POST' and name_form.validate():
        root.child('Users/Account/'+session['username']).update({
            # 'first_name': name_form.first_name.data,
            # 'last_name': name_form.last_name.data,
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
        root.child('Users/HealthDetail/'+session['username']).update({
            'gender': gender_form.gender.data,
        })
        return redirect(url_for('register_info'))
    return render_template('firstTimeRegisterGender.html', gender_form=gender_form)


class MoreInfoForm(Form):
    height = DecimalField('Current Height (m)', places=2)
    initial_weight = DecimalField('Current Weight (kg)', places=1)
    birth_day = SelectField(
        'Day', choices=[
            ('01', '1'), ('02', '2'), ('03', '3'), ('04', '4'), ('05', '5'), ('06', '6'), ('07', '7'), ('08', '8'),
            ('09', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
            ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'),
            ('23', '23'), ('24', '24'), ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'),
            ('30', '30'), ('31', '31'),
        ]
    )
    birth_month = SelectField(
        'Month', choices=[
            ('01', 'Jan'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Apr'), ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'),
            ('08', 'Aug'), ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')
        ]
    )
    birth_year = IntegerField('Year', [validators.NumberRange(min=1000, max=9999, message="Invalid Year Input")])


@app.route('/setup/detail', methods=['GET', 'POST'])
def register_info():
    moreinfo_form = MoreInfoForm(request.form)
    register_date = '{:%Y%m%d}'.format(datetime.date.today())
    if request.method == 'POST' and moreinfo_form.validate():
        root.child('Users/HealthDetail/'+session['username']).update({
            'height': str(moreinfo_form.height.data),
            'weight_dict': {
                register_date: str(moreinfo_form.initial_weight.data)
            },
            'birthday': str(moreinfo_form.birth_year.data) +
            str(moreinfo_form.birth_month.data) +
            str(moreinfo_form.birth_day.data)
        })
        return redirect(url_for('register_bp'))
    return render_template('firstTimeRegisterInfo.html', moreinfo_form=moreinfo_form)


class BpInfoForm(Form):
    systol = IntegerField('Systolic Pressure')
    diastol = IntegerField('Diastolic Pressure')
    pulse = IntegerField('Pulse Rate')


@app.route('/setup/bp', methods=['GET', 'POST'])
def register_bp():
    bp_info_form = BpInfoForm(request.form)
    register_time = '{:%Y%m%d%H%M}'.format(datetime.datetime.now())
    if request.method == 'POST' and bp_info_form.validate():
        root.child('Users/HealthDetail/'+session['username']).update({
            'bp_dict': {
                register_time: {
                    'systolic': str(bp_info_form.systol.data),
                    'diastolic': str(bp_info_form.diastol.data),
                    'pulse': str(bp_info_form.pulse.data)
                }
            }
        })
        flash('You have Completed the Account Setup', 'success')
        return redirect(url_for('profile'))
    return render_template('firstTimeRegisterBp.html', bp_info_form=bp_info_form)


class UserHealthDetailForm(Form):
    # first_name = StringField('First Name', [validators.length(min=1, max=20), validators.DataRequired()])
    # last_name = StringField('Last Name', [validators.length(min=1, max=20), validators.DataRequired()])
    # display_name = StringField('Display Name', [validators.length(min=1, max=20), validators.DataRequired()])
    gender = RadioField('Gender', [validators.DataRequired()], choices=[('male', 'Male'), ('female', 'Female')])
    initial_weight = DecimalField('Current Weight (kg)', [validators.DataRequired()], places=1)
    birth_day = SelectField(
        'Day', choices=[
            ('01', '1'), ('02', '2'), ('03', '3'), ('04', '4'), ('05', '5'), ('06', '6'), ('07', '7'), ('08', '8'),
            ('09', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
            ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'),
            ('23', '23'), ('24', '24'), ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'),
            ('30', '30'), ('31', '31'),
        ]
    )
    birth_month = SelectField(
        'Month', choices=[
            ('01', 'Jan'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Apr'), ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'),
            ('08', 'Aug'), ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')
        ]
    )
    birth_year = IntegerField('Year', [validators.NumberRange(min=1000, max=9999, message="Invalid Year Input")])
    height = DecimalField('Current Height (m)', [validators.DataRequired()], places=2)
    initial_systol = IntegerField('Systol')
    initial_diastol = IntegerField('Diastol')
    initial_pulse = IntegerField('Pulse')


@app.route('/account/detail', methods=['GET', 'POST'])
def health_detail():
    setup_date = '{:%Y%m%d}'.format(datetime.date.today())
    setup_time = '{:%Y%m%d%H%M}'.format(datetime.datetime.now())
    setup_detail_form = UserHealthDetailForm(request.form)
    uid_db = root.child('Users')
    if request.method == 'POST' and setup_detail_form.validate():
        # first_name = setup_detail_form.first_name.data
        # last_name = setup_detail_form.last_name.data
        # display_name = setup_detail_form.display_name.data
        gender = setup_detail_form.gender.data
        birthday = str(
            setup_detail_form.birth_year.data) + setup_detail_form.birth_month.data + setup_detail_form.birth_day.data
        height = str(setup_detail_form.height.data)
        weight_dict = {
            setup_date: str(setup_detail_form.initial_weight.data)
        }
        bp_dict = {
            setup_time: {
                'systolic': str(setup_detail_form.initial_systol.data),
                'diastolic': str(setup_detail_form.initial_diastol.data),
                'pulse': str(setup_detail_form.initial_pulse.data)
            }
        }
        user_info = HealthDetailSetup(
            gender, birthday, height, weight_dict, bp_dict
        )
        uid_db.child('HealthDetail/'+session['username']).update({
            # 'first_name': user_info.get_first_name(),
            # 'last_name': user_info.get_last_name(),
            'gender': user_info.get_gender(),
            'birthday': user_info.get_birth(),
            'height': user_info.get_height(),
            'weight_dict': user_info.get_weight_dict(),
            'bp_dict': user_info.get_bp_dict()
        })
        flash('Health Details Updated Successfully', 'success')
        return redirect(url_for('health_detail'))
    else:
        user_info_db = uid_db.child('HealthDetail/'+session['username']).get()
        user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                      user_info_db['weight_dict'], user_info_db['bp_dict']
                                      )
        # setup_detail_form.first_name.data = user_info.get_first_name()
        # setup_detail_form.last_name.data = user_info.get_last_name()
        # setup_detail_form.display_name.data = user_info.get_display_name()
        setup_detail_form.gender.data = user_info.get_gender()
        setup_detail_form.birth_year.data = user_info.get_birth()[:4]
        setup_detail_form.birth_month.data = user_info.get_birth()[4:6]
        setup_detail_form.birth_day.data = user_info.get_birth()[6:8]
        weight_dict = user_info.get_weight_dict()
        weight_date_list = []
        for date in weight_dict:
            weight_date_list.append(date)
        setup_detail_form.initial_weight.data = float(user_info.get_weight_dict()[weight_date_list[0]])
        setup_detail_form.height.data = float(user_info.get_height())
        bp_dict = user_info.get_bp_dict()
        bp_time_list = []
        for time in bp_dict:
            bp_time_list.append(time)
        setup_detail_form.initial_systol.data = int(user_info.get_bp_dict()[bp_time_list[0]]['systolic'])
        setup_detail_form.initial_diastol.data = int(user_info.get_bp_dict()[bp_time_list[0]]['diastolic'])
        setup_detail_form.initial_pulse.data = int(user_info.get_bp_dict()[bp_time_list[0]]['pulse'])

    return render_template('healthDetail.html', setup_detail_form=setup_detail_form)


@app.route('/profile')
def profile():
    uid_db = root.child('Users')
    user_info_db = uid_db.child('HealthDetail/' + session['username']).get()
    user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                 user_info_db['weight_dict'], user_info_db['bp_dict']
                                 )
    return render_template('profile.html', user=user_info)


@app.route('/plan')
def plans():
    return render_template('plan.html')


class Diet:
    def __init__(self, name, type, calories, fats, carbohydrates, protein):
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

    def set_dietID(self, dietID):
        self.dietID = dietID

    def set_name(self, name):
        self.name = name

    def set_type(self, type):
        self.type = type

    def set_calories(self, calories):
        self.calories = calories

    def set_fats(self, fats):
        self.fats = fats

    def set_carbohydrates(self, cabohydrates):
        self.cabohydrates = cabohydrates

    def set_protein(self, protein):
        self.protein = protein


@app.route('/diet')
def diet():
    Diet_db = root.child('Food').get()
    diet_list = []
    for dietID in Diet_db:
        eachdiet = Diet_db[dietID]
        food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                    eachdiet['Carbohydrates Value'], eachdiet['Protein Value'])
        food.set_dietID(dietID)
        diet_list.append(food)

    return render_template('diet.html', diet=diet_list)


class Food(Form):
    diet_name = StringField('Name', [validators.length(min=1, max=150), validators.DataRequired()])
    diet_type = SelectField('Type', [validators.DataRequired()], choices=[("", "Select"), ("Foods", "Foods"),
                                                                          ("Drinks", "Drinks"), ("Fruits", "Fruits")])
    calories = IntegerField('Calories Value')
    fats = IntegerField('Fats Value')
    carbohydrates = IntegerField('Carbohydrates Value')
    proteins = IntegerField('Protein Value')


@app.route('/new_diet', methods=['GET', 'POST'])
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
        food_diet.db.push({'Name': food_diet.get_name(),
                           'Type': food_diet.get_type(),
                           'Calories Value': food_diet.get_calories(),
                           'Fats Value': food_diet.get_fats(),
                           'Carbohydrates Value': food_diet.get_carbohydrates(),
                           'Protein Value': food_diet.get_protein()
                           })
        flash('New Diet inserted successfully', 'success')

        return redirect(url_for('diet'))

    return render_template('new_diet.html', form=new_form)


@app.route('/update_diet/<string:id>', methods=['GET', 'POST'])
def update_diet(id):
    update_form = Food(request.form)
    if request.method == 'POST' and update_form.validate():
        name = update_form.diet_name.data
        food_type = update_form.diet_type.data
        calories = update_form.calories.data
        fats = update_form.fats.data
        carbohydrates = update_form.carbohydrates.data
        protein = update_form.proteins.data
        food_diet = Diet(name, food_type, calories, fats, carbohydrates, protein)
        Diet_db = root.child('Food/' + id)
        Diet_db.set({'Name': food_diet.get_name(),
                     'Type': food_diet.get_type(),
                     'Calories Value': food_diet.get_calories(),
                     'Fats Value': food_diet.get_fats(),
                     'Carbohydrates Value': food_diet.get_carbohydrates(),
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
    flash('Diet deleted', 'Success')

    return redirect(url_for('diet'))


@app.route('/faq')
def faq():
    return render_template('faq.html')


class ActivityForm(Form):
    activity = StringField('Name Of Activity', [validators.Length(min=1, max=20), validators.DataRequired()])
    date = DateField('Date Of Activity', format='%d/%M/%Y')
    duration = IntegerField('Duration Of Activity')


class Activity:
    def __init__(self, activity, date, duration):
        self.__actID = ''
        self.__activity = activity
        self.__date = date
        self.__duration = duration

    def get_activity(self):
        return self.__activity

    def get_date(self):
        return self.__date

    def get_actID(self):
        return self.__actID

    def get_duration(self):
        return self.__duration

    def set_activity(self, activity):
        self.__activity = activity

    def set_date(self, date):
        self.__date = date

    def set_actID(self, actID):
        self.__actID = actID

    def set_duration(self, duration):
        self.__duration = duration


@app.route('/input_activity', methods=['GET', 'POST'])
def input_activity():
    actform = ActivityForm(request.form)
    if request.method == 'POST' and actform.validate():
        activity = actform.activity.data
        date = str(actform.date.data)
        duration = int(actform.duration.data)
        latest_activity = Activity(activity, date, duration)
        latest_activity.db = root.child('Activities')
        latest_activity.db.push({'Activity': latest_activity.get_activity(), 'Date': latest_activity.get_date(), 'Duration': latest_activity.get_duration()})
        flash('New activity updated successfully', 'success')
        return redirect(url_for('record'))

    return render_template('input_activity.html', actform=actform)


@app.route('/record')
def record():
    Act_db = root.child('Activities').get()
    act_list = []
    for actID in Act_db:
        eachact = Act_db[actID]
        activities = Activity(eachact['Activity'], eachact['Date'], eachact['Duration'])
        activities.set_actID(actID)
        act_list.append(activities)
    return render_template('track_and_record.html', activity=act_list)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    new_form = leaderboardform(request.form)
    if request.method == 'POST' and new_form.validate():
        score = new_form.score.data
        username = session["username"]
        userscore = leaderboard(username, score)
        userscore.db = root.child('Leaderboard')
        userscore.db.push({"username": userscore.get_username(), "Score": userscore.get_score()})
        flash('New score inserted successfully', 'success')

        return redirect(url_for('leaderboards'))
    return render_template('quiz.html', new_form=new_form)


@app.route('/leaderboards')
def leaderboards():
    return render_template('leaderboards.html')


class leaderboard:
    def __init__(self, username, score):
        self.__username = username
        self.__score = score

    def set_score(self, score):
        self.__score = score

    def set_username(self, username):
        self.__username = username

    def get_score(self):
        return self.__score

    def get_username(self):
        return self.__username


class leaderboardform(Form):
    score = StringField("Score")


@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


if __name__ == '__main__':
    app.run(port=80)
