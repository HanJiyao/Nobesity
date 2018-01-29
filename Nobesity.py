from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, PasswordField, DecimalField, \
    IntegerField, DateField, validators, ValidationError
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

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email


class LoginForm(Form):
    username = StringField('Email / User Name')
    password = PasswordField('Password')


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    uid_db = root.child('Users').get()
    if request.method == 'POST' and login_form.validate():
        login_id = request.form.to_dict()['username'].lower()
        for i in uid_db:
            if uid_db[i]['email'] == login_id or login_id == i:
                session['username'] = i
                session['logged_in'] = True
                flash('Welcome Back, ' + session['username'], 'primary')
                return redirect(url_for('profile'))

    return render_template('login.html', form=login_form)


class SignUpForm(Form):
    username = StringField('User Name')
    email = StringField('Email')
    password = PasswordField('Password')
    confirm = PasswordField('Confirm Password')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignUpForm(request.form)
    if request.method == 'POST' and signup_form.validate():
        user_account = UserAccount(
            signup_form.username.data.lower(),
            signup_form.email.data.lower()
        )
        user_db = root.child('Users')
        user_db.child(user_account.get_username()).set({
            'email': user_account.get_email(),
        })
        session['logged_in'] = True
        session['username'] = signup_form.username.data.lower()
        flash('You are successfully signed up as '+session['username'], 'success')
        return redirect(url_for('verify_email'))

    return render_template('signup.html', form=signup_form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


class HealthDetailSetup:
    def __init__(self, gender, birth, height, weight_dict, bp_dict):
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
            self.__suggest_bfp = '< 25%'
            self.__suggest_cal = math.ceil(9.99 * current_weight + 6.25 * height * 100 - 4.92 * self.__age + 5)
        else:
            gender_index = 0
            self.__suggest_bfp = '< 32%'
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
        self.__plan_grade = 30
        self.__bmi_grade = 0
        if 18.5 > self.__bmi:
            self.__bmi_grade = 20 - (18.5 - self.__bmi) * 1.6
        elif 22.9 < self.__bmi:
            self.__bmi_grade = 20 - (self.__bmi - 22.9) * 1.6
        else:
            self.__bmi_grade = 20
        if self.__bmi_grade < 0:
            self.__bmi_grade = 0
        self.__bfp_grade = 0
        if gender == 'male':
            if self.__bfp > 25:
                self.__bfp_grade = 20 - (self.__bfp - 25) * 2
            else:
                self.__bfp_grade = 20
        if gender == 'female':
            if self.__bfp > 32:
                self.__bfp_grade = 20 - (self.__bfp - 30) * 2
            else:
                self.__bfp_grade = 20
        if self.__bfp_grade < 0:
            self.__bfp_grade = 0
        self.__sys_grade = 0
        self.__dias_grade = 0
        self.__pulse_grade = 0
        self.__bp_grade = 0
        if self.__current_systolic < 90:
            self.__sys_grade = 12 - (90 - self.__current_systolic) * 0.5
        elif self.__current_systolic > 120:
            self.__sys_grade = 12 - (self.__current_systolic - 120) * 0.5
        else:
            self.__sys_grade = 8
        if self.__sys_grade < 0:
            self.__sys_grade = 0
        if self.__current_diastolic < 60:
            self.__dias_grade = 12 - (60 - self.__current_diastolic) * 0.5
        elif self.__current_diastolic > 80:
            self.__dias_grade = 12 - (self.__current_diastolic - 80) * 0.5
        else:
            self.__dias_grade = 8
        if self.__dias_grade < 0:
            self.__dias_grade = 0
        if self.__current_pulse > 75:
            self.__pulse_grade = 6 - (self.__current_pulse - 75) * 0.3
        if self.__pulse_grade < 0:
            self.__pulse_grade = 0
        self.__bp_grade = self.__sys_grade + self.__dias_grade + self.__pulse_grade
        self.__grade = int(round(self.__plan_grade + self.__bmi_grade + self.__bfp_grade + self.__bp_grade))
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


@app.route('/setup/email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        return redirect(url_for('register_name'))
    return render_template('verifyEmail.html')


class NameForm(Form):
    display_name = StringField('Display Name', [validators.length(min=1, max=20), validators.DataRequired()])


@app.route('/setup/name', methods=['GET', 'POST'])
def register_name():
    name_form = NameForm(request.form)
    if request.method == 'POST' and name_form.validate():
        root.child('Users/'+session['username']).update({
            'displayName': name_form.display_name.data
        })
        return redirect(url_for('register_gender'))
    return render_template('firstTimeRegisterName.html', name_form=name_form)


class GenderForm(Form):
    gender = RadioField('Gender', [validators.DataRequired()], choices=[('male', 'Male'), ('female', 'Female')])


@app.route('/setup/gender', methods=['GET', 'POST'])
def register_gender():
    gender_form = GenderForm(request.form)
    if request.method == 'POST' and gender_form.validate():
        root.child('HealthDetail/'+session['username']).update({
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
        root.child('HealthDetail/'+session['username']).update({
            'height': str(moreinfo_form.height.data),
            'birthday': str(moreinfo_form.birth_year.data) +
            str(moreinfo_form.birth_month.data) +
            str(moreinfo_form.birth_day.data)
        })
        root.child('Weight/'+session['username']).update({
            register_date: str(moreinfo_form.initial_weight.data)
        }),
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
        root.child('BloodPressure/'+session['username']).update({
            register_time: {
                'systolic': str(bp_info_form.systol.data),
                'diastolic': str(bp_info_form.diastol.data),
                'pulse': str(bp_info_form.pulse.data)
            }
        })
        flash('You have Completed the Account Setup', 'success')
        return redirect(url_for('profile'))
    return render_template('firstTimeRegisterBp.html', bp_info_form=bp_info_form)


class UserHealthDetailForm(Form):
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
    uid_db = root
    if request.method == 'POST' and setup_detail_form.validate():
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
            'gender': user_info.get_gender(),
            'birthday': user_info.get_birth(),
            'height': user_info.get_height(),
        })
        for i in user_info.get_weight_dict():
            uid_db.child('Weight/' + session['username']).update({
                i: user_info.get_weight_dict()[i]
            })
        for i in user_info.get_bp_dict():
            uid_db.child('BloodPressure/' + session['username']).update({
                i: user_info.get_bp_dict()[i]
            })
        flash('Health Details Updated Successfully', 'success')
        return redirect(url_for('health_detail'))
    else:
        uid_db = root
        user_info_db = uid_db.child('HealthDetail/' + session['username']).get()
        user_weight_db = uid_db.child('Weight/' + session['username']).get()
        user_bp_db = uid_db.child('BloodPressure/' + session['username']).get()
        user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                      user_weight_db, user_bp_db
                                      )
        setup_detail_form.gender.data = user_info.get_gender()
        setup_detail_form.birth_year.data = user_info.get_birth()[:4]
        setup_detail_form.birth_month.data = user_info.get_birth()[4:6]
        setup_detail_form.birth_day.data = user_info.get_birth()[6:8]
        weight_dict = user_info.get_weight_dict()
        weight_date_list = []
        for date in weight_dict:
            weight_date_list.append(date)
        setup_detail_form.initial_weight.data = float(user_info.get_weight_dict()[weight_date_list[-1]])
        setup_detail_form.height.data = float(user_info.get_height())
        bp_dict = user_info.get_bp_dict()
        bp_time_list = []
        for time in bp_dict:
            bp_time_list.append(time)
        setup_detail_form.initial_systol.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['systolic'])
        setup_detail_form.initial_diastol.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['diastolic'])
        setup_detail_form.initial_pulse.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['pulse'])

    return render_template('healthDetail.html', setup_detail_form=setup_detail_form)


@app.route('/profile')
def profile():
    uid_db = root
    user_info_db = uid_db.child('HealthDetail/' + session['username']).get()
    user_weight_db = uid_db.child('Weight/' + session['username']).get()
    user_bp_db = uid_db.child('BloodPressure/' + session['username']).get()
    user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                  user_weight_db, user_bp_db
                                  )
    return render_template('profile.html', user=user_info)


@app.route('/plan')
def plans():
    return render_template('plan.html')


class Diet:
    def __init__(self, name, type, calories, fats, carbohydrates, protein, diet_date):
        self.dietID = ''
        self.name = name
        self.type = type
        self.calories = calories
        self.fats = fats
        self.carbohydrates = carbohydrates
        self.protein = protein
        self.diet_date = diet_date

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

    def get_dietDate(self):
        return self.diet_date

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
    total_calories = 0
    total_fats = 0
    total_carbohydrates = 0
    total_protein = 0
    username = session["username"]
    try:
        for dietID in Diet_db[username]:
            eachdiet = Diet_db[username][dietID]
            food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                    eachdiet['Carbohydrates Value'], eachdiet['Protein Value'], eachdiet['Diet Date'])
            total_calories += food.get_calories()
            total_fats += food.get_fats()
            total_carbohydrates += food.get_carbohydrates()
            total_protein += food.get_protein()
            food.set_dietID(dietID)
            diet_list.append(food)
    except TypeError :
        return redirect(url_for('new_diet'))
    except KeyError:
        return redirect(url_for('new_diet'))

    return render_template('diet.html', diet=diet_list, total_calories=total_calories,total_fats=total_fats,
                           total_carbohydrates=total_carbohydrates, total_protein=total_protein)


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
    username = session["username"]
    if request.method == 'POST' and new_form.validate():
        name = new_form.diet_name.data
        type = new_form.diet_type.data
        calories = new_form.calories.data
        fats = new_form.fats.data
        carbohydrates = new_form.carbohydrates.data
        protein = new_form.proteins.data
        diet_date = '{:%d/%m/%Y}'.format(datetime.date.today())
        food_diet = Diet(name, type, calories, fats, carbohydrates, protein,diet_date)
        food_diet.db = root.child('Food')
        food_diet.db.child(username).push({'Name': food_diet.get_name(),
                           'Type': food_diet.get_type(),
                           'Calories Value': food_diet.get_calories(),
                           'Fats Value': food_diet.get_fats(),
                           'Carbohydrates Value': food_diet.get_carbohydrates(),
                           'Protein Value': food_diet.get_protein(),
                           'Diet Date': food_diet.get_dietDate(),
                           })
        flash('New Diet inserted successfully', 'success')

        return redirect(url_for('diet'))

    return render_template('new_diet.html', form=new_form)


@app.route('/update_diet/<string:id>', methods=['GET', 'POST'])
def update_diet(id):
    username = session["username"]
    url = 'Food/' + username + '/' + id
    update_form = Food(request.form)
    if request.method == 'POST' and update_form.validate():
        name = update_form.diet_name.data
        food_type = update_form.diet_type.data
        calories = update_form.calories.data
        fats = update_form.fats.data
        carbohydrates = update_form.carbohydrates.data
        protein = update_form.proteins.data
        diet_date = root.child(url + '/Diet Date').get()
        food_diet = Diet(name, food_type, calories, fats, carbohydrates, protein, diet_date)
        Diet_db = root.child('Food/' + username + '/' + id)
        Diet_db.set({'Name': food_diet.get_name(),
                     'Type': food_diet.get_type(),
                     'Calories Value': food_diet.get_calories(),
                     'Fats Value': food_diet.get_fats(),
                     'Carbohydrates Value': food_diet.get_carbohydrates(),
                     'Protein Value': food_diet.get_protein(),
                     'Diet Date': diet_date})
        flash('Diet updated successfully', 'success')

        return redirect(url_for('diet'))
    else:
        eachdiet = root.child(url).get()
        food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                    eachdiet['Carbohydrates Value'], eachdiet['Protein Value'], eachdiet['Diet Date'])
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
    username = session["username"]
    Diet_db = root.child('Food/' + username + '/' + id)
    Diet_db.delete()
    flash('Diet deleted', 'Success')

    return redirect(url_for('diet'))


@app.route('/faq')
def faq():
    return render_template('faq.html')


class ActivityForm(Form):
    activity = StringField('Name Of Activity', [validators.Length(min=1, max=20), validators.DataRequired()])
    date = DateField('Date Of Activity', format='%Y/%m/%d')
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
    username=session["username"]
    if request.method == 'POST' and actform.validate():
        activity = actform.activity.data
        date = str(actform.date.data)
        duration = int(actform.duration.data)
        latest_activity = Activity(activity, date, duration)
        latest_activity.db = root.child('Activities/'+username)
        latest_activity.db.push({'Activity': latest_activity.get_activity(), 'Date': latest_activity.get_date(), 'Duration': latest_activity.get_duration()})
        flash('New activity updated successfully', 'success')
        return redirect(url_for('record'))

    return render_template('input_activity.html', actform=actform)


@app.route('/record')
def record():
    username = session["username"]
    Act_db = root.child('Activities/'+username).get()
    act_list = []
    message = 'You have not recorded any activities yet! Get moving!'
    try:
        for actID in Act_db:
            eachact = Act_db[actID]
            activities = Activity(eachact['Activity'], eachact['Date'], eachact['Duration'])
            # total_duration += activities.get_duration()
            activities.set_actID(actID)
            act_list.append(activities)
        #check if list is empty or not
        if not act_list:
            return message
        else:
            #if list is not empty, do the sorting by date
            #act_list.sort(key=xxxxx, reverse=True)
            act_list.sort(key=lambda activity: activity.get_date(), reverse=True)

            if eachact['Date'] == datetime.datetime.now():
                #output activity with today's date into the top section
                pass
            else:
                # return message into the top section
                pass
    except TypeError:
        return redirect(url_for('input_activity'))
    except KeyError:
        return redirect(url_for('input_activity'))
    today_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    return render_template('track_and_record.html', activity=act_list, date=today_date, display_msg=message)


@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


@app.route('/quiz', methods=['GET','POST'])
def quiz():
    new_form = leaderboardform(request.form)
    if request.method == 'POST' and new_form.validate():
        score = new_form.score.data
        username=session["username"]
        userscore = Leaderboard(username,score)
        userscore.db = root.child('Leaderboard')#map current userscore to firebase
        userscore.db.child(username).set({"Score": userscore.get_score()})#push means to update score
        flash('New score inserted successfully', 'success')

        return redirect(url_for('leaderboards'))
    return render_template('quiz.html', new_form=new_form)


@app.route('/leaderboards')
def leaderboards():
    leaderboard_db = root.child('Leaderboard').get()
    leaderboards_list = []  # create a list to store all the quiz results

    for eachscore in leaderboard_db:
        leaderboard=Leaderboard(eachscore,leaderboard_db[eachscore]["Score"])
        leaderboards_list.append(leaderboard)
    leaderboards_list.sort(key=lambda score: leaderboard.get_score(), reverse=True)
    for eachscore in leaderboards_list:
        rank=leaderboards_list.index(eachscore)+1
        eachscore.set_rank(rank)
    return render_template('leaderboards.html',leaderboards_list=leaderboards_list)


class Leaderboard:
    def __init__(self,username,score,rank=0):
        self.__username=username
        self.__score=score
        self.__rank=rank
    def set_score(self,score):
        self.__score=score
    def set_username(self,username):
        self.__username=username
    def get_score(self):
        return self.__score
    def get_username(self):
        return self.__username
    def set_rank(self,rank):
        self.__rank=rank
    def get_rank(self):
        return self.__rank


class leaderboardform(Form):
    score=StringField("Score")


if __name__ == '__main__':
    app.run()
