from flask import Flask, render_template, request, flash, redirect, url_for, session
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, PasswordField, DecimalField, \
    IntegerField, DateField, validators, ValidationError, BooleanField
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
        return redirect(url_for('profile'))
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
        login_id = login_form.username.data.lower()
        for i in uid_db:
            if root.child('Users/' + i + '/email').get() == login_id or login_id == i:
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
    return render_template('Reference/dashboard.html')


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
        self.__bmi_grade = 0
        if 18.5 > self.__bmi:
            self.__bmi_grade = 25 - (18.5 - self.__bmi) * 1.8
        elif 22.9 < self.__bmi:
            self.__bmi_grade = 25 - (self.__bmi - 22.9) * 1.8
        else:
            self.__bmi_grade = 25
        if self.__bmi_grade < 0:
            self.__bmi_grade = 0
        self.__bfp_grade = 0
        if gender == 'male':
            if self.__bfp > 25:
                self.__bfp_grade = 25 - (self.__bfp - 25) * 2.5
            else:
                self.__bfp_grade = 25
        if gender == 'female':
            if self.__bfp > 32:
                self.__bfp_grade = 25 - (self.__bfp - 30) * 2.5
            else:
                self.__bfp_grade = 25
        if self.__bfp_grade < 0:
            self.__bfp_grade = 0
        self.__sys_grade = 0
        self.__dias_grade = 0
        self.__pulse_grade = 0
        self.__bp_grade = 0
        if self.__current_systolic < 90:
            self.__sys_grade = 20 - (90 - self.__current_systolic) * 0.9
        elif self.__current_systolic > 120:
            self.__sys_grade = 20 - (self.__current_systolic - 120) * 0.9
        else:
            self.__sys_grade = 20
        if self.__sys_grade < 0:
            self.__sys_grade = 0
        if self.__current_diastolic < 60:
            self.__dias_grade = 20 - (60 - self.__current_diastolic) * 0.9
        elif self.__current_diastolic > 80:
            self.__dias_grade = 20 - (self.__current_diastolic - 80) * 0.9
        else:
            self.__dias_grade = 20
        if self.__dias_grade < 0:
            self.__dias_grade = 0
        if self.__current_pulse > 75:
            self.__pulse_grade = 10 - (self.__current_pulse - 75) * 0.5
        else:
            self.__pulse_grade = 10
        if self.__pulse_grade < 0:
            self.__pulse_grade = 0
        self.__bp_grade = self.__sys_grade + self.__dias_grade + self.__pulse_grade
        self.__grade = int(round(self.__bmi_grade + self.__bfp_grade + self.__bp_grade))
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
        return float(self.__height)

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

    def get_suggest_weight_max(self):
        return self.__suggest_weight_max

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
    display_name = StringField('Display Name',
                               [validators.length(min=1, max=20),
                                validators.DataRequired(message="Please enter Display Name")])


@app.route('/setup/name', methods=['GET', 'POST'])
def register_name():
    try:
        name_form = NameForm(request.form)
        if request.method == 'POST' and name_form.validate():
            root.child('Users/' + session['username']).update({
                'displayName': name_form.display_name.data
            })
            return redirect(url_for('register_gender'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('firstTimeRegisterName.html', name_form=name_form)


class GenderForm(Form):
    gender = RadioField('Gender', [validators.DataRequired()], choices=[('male', 'Male'), ('female', 'Female')])


@app.route('/setup/gender', methods=['GET', 'POST'])
def register_gender():
    try:
        gender_form = GenderForm(request.form)
        if request.method == 'POST' and gender_form.validate():
            root.child('HealthDetail/' + session['username']).update({
                'gender': gender_form.gender.data,
            })
            return redirect(url_for('register_info'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('firstTimeRegisterGender.html', gender_form=gender_form)


class MoreInfoForm(Form):
    height = IntegerField('Current Height (cm)',
                          [validators.DataRequired('Please Enter Current Height'),
                           validators.NumberRange(min=1, max=300, message="Please Enter Correct Height < 300cm")])
    initial_weight = DecimalField('Current Weight (kg)',
                                  [validators.DataRequired('Please Enter Current Weight'),
                                   validators.NumberRange(min=1, max=300,
                                                          message="Please Enter Correct Weight < 300kg")],
                                  places=1)
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
    birth_year = IntegerField('Year', [validators.NumberRange
                                       (min=1800,
                                        max=datetime.date.today().year,
                                        message="Please Enter a correct Year")])


@app.route('/setup/detail', methods=['GET', 'POST'])
def register_info():
    try:
        more_info_form = MoreInfoForm(request.form)
        register_date = '{:%Y%m%d}'.format(datetime.date.today())
        birth_year = more_info_form.birth_year.data
        birth_month = more_info_form.birth_month.data
        birth_day = more_info_form.birth_day.data
        date_error = False
        if request.method == 'POST' and more_info_form.validate():
            root.child('HealthDetail/' + session['username']).update({
                'height': str(more_info_form.height.data / 100),
                'birthday': str(birth_year) + str(birth_month) + str(birth_day)
            })
            root.child('Weight/' + session['username']).update({
                register_date: str(more_info_form.initial_weight.data)
            })
            try:
                datetime.date(int(more_info_form.birth_year.data),
                              int(more_info_form.birth_month.data),
                              int(more_info_form.birth_day.data))
            except ValueError:
                date_error = True
                return render_template('firstTimeRegisterInfo.html', moreinfo_form=more_info_form,
                                       date_error=date_error)
            else:
                input_date = datetime.date(int(more_info_form.birth_year.data),
                                           int(more_info_form.birth_month.data),
                                           int(more_info_form.birth_day.data))
                if str(datetime.date.today() - input_date)[0] == "-":
                    date_error = True
                else:
                    return redirect(url_for('register_bp'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('firstTimeRegisterInfo.html', moreinfo_form=more_info_form, date_error=date_error)


class BpInfoForm(Form):
    systole = IntegerField('Systole', [validators.DataRequired('Please Enter Systolic Pressure'),
                                       validators.NumberRange
                                       (min=1, max=300, message="Please Enter A valid BP < 300")])
    diastole = IntegerField('Diastole', [validators.DataRequired('Please Enter Diastolic Pressure'),
                                         validators.NumberRange
                                         (min=1, max=300, message="Please Enter A valid BP < 300")])
    pulse = IntegerField('Pulse', [validators.DataRequired('Please Enter the Pulse Rate'),
                                   validators.NumberRange
                                   (min=1, max=300, message="Please Enter A valid Pulse < 300")])


@app.route('/setup/bp', methods=['GET', 'POST'])
def register_bp():
    try:
        bp_info_form = BpInfoForm(request.form)
        register_time = '{:%Y%m%d%H%M}'.format(datetime.datetime.now())
        if request.method == 'POST' and bp_info_form.validate():
            root.child('BloodPressure/' + session['username']).update({
                register_time: {
                    'systolic': str(bp_info_form.systole.data),
                    'diastolic': str(bp_info_form.diastole.data),
                    'pulse': str(bp_info_form.pulse.data)
                }
            })
            flash('You have Completed the Account Setup', 'success')
            return redirect(url_for('profile'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
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
    birth_year = IntegerField('Year',
                              [validators.NumberRange(min=1800, max=datetime.date.today().year,
                                                      message="Please Enter a correct Year")])
    height = IntegerField('Current Height (cm)',
                          [validators.NumberRange(min=0, max=300, message="Please Enter Correct Height (cm)")])
    initial_systole = IntegerField('Systole', [validators.DataRequired('Please Enter Systolic Pressure'),
                                               validators.NumberRange(min=0, max=300,
                                                                      message="Please Enter A valid BP < 300")])
    initial_diastole = IntegerField('Diastole', [validators.DataRequired('Please Enter Diastolic Pressure'),
                                                 validators.NumberRange(min=0, max=250,
                                                                        message="Please Enter A valid BP < 250")])
    initial_pulse = IntegerField('Pulse', [validators.DataRequired('Please Enter the Pulse Rate'),
                                           validators.NumberRange(min=0, max=300,
                                                                  message="Please Enter A valid Pulse < 300")])


@app.route('/account/detail', methods=['GET', 'POST'])
def health_detail():
    try:
        setup_date = '{:%Y%m%d}'.format(datetime.date.today())
        setup_time = '{:%Y%m%d%H%M}'.format(datetime.datetime.now())
        setup_detail_form = UserHealthDetailForm(request.form)
        uid_db = root
        if request.method == 'POST' and setup_detail_form.validate():
            gender = setup_detail_form.gender.data
            birthday = str(
                setup_detail_form.birth_year.data)+setup_detail_form.birth_month.data+setup_detail_form.birth_day.data
            height = str(setup_detail_form.height.data / 100)
            weight_dict = {
                setup_date: str(setup_detail_form.initial_weight.data)
            }
            bp_dict = {
                setup_time: {
                    'systolic': str(setup_detail_form.initial_systole.data),
                    'diastolic': str(setup_detail_form.initial_diastole.data),
                    'pulse': str(setup_detail_form.initial_pulse.data)
                }
            }
            user_info = HealthDetailSetup(
                gender, birthday, height, weight_dict, bp_dict
            )
            uid_db.child('HealthDetail/' + session['username']).update({
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
            setup_detail_form.height.data = round(float(user_info.get_height()) * 100)
            bp_dict = user_info.get_bp_dict()
            bp_time_list = []
            for time in bp_dict:
                bp_time_list.append(time)
            setup_detail_form.initial_systole.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['systolic'])
            setup_detail_form.initial_diastole.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['diastolic'])
            setup_detail_form.initial_pulse.data = int(user_info.get_bp_dict()[bp_time_list[-1]]['pulse'])
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('healthDetail.html', setup_detail_form=setup_detail_form)


@app.route('/account/info', methods=['GET', 'POST'])
def personal_info():
    try:
        name_form = NameForm(request.form)
        file_name = root.child('Users/' + session['username'] + '/photoName').get()
        photo_url = root.child('Users/' + session['username'] + '/photoURL').get()
        if request.method == 'POST' and name_form.validate():
            root.child('Users/' + session['username']).update({
                'displayName': name_form.display_name.data
            })
            flash('Personal information updated successful', 'success')
        else:
            name_form.display_name.data = root.child('Users/' + session['username'] + '/displayName').get()
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('personalInfo.html', name_form=name_form, photoURL=photo_url, fileName=file_name)


@app.route('/account/security')
def security():
    return render_template('security.html')


@app.route('/password')
def password_reset():
    session.pop('username', None)
    session.pop('logged_in', None)
    return render_template('passwordReset.html')


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    try:
        file_name = root.child('Users/' + session['username'] + '/photoName').get()
        if request.method == 'POST':
            root.child('Activities/' + session['username']).delete()
            root.child('BloodPressure/' + session['username']).delete()
            root.child('Food/' + session['username']).delete()
            root.child('HealthDetail/' + session['username']).delete()
            root.child('Leaderboard/' + session['username']).delete()
            root.child('Rewards/' + session['username']).delete()
            root.child('Users/' + session['username']).delete()
            root.child('Weight/' + session['username']).delete()
            session.pop('username', None)
            session.pop('logged_in', None)
            return redirect(url_for('index'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('delete.html', fileName=file_name)


@app.route('/profile')
def profile():
    try:
        uid_db = root
        user_info_db = uid_db.child('HealthDetail/' + session['username']).get()
        user_weight_db = uid_db.child('Weight/' + session['username']).get()
        user_bp_db = uid_db.child('BloodPressure/' + session['username']).get()
        user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                      user_weight_db, user_bp_db
                                      )
        display_name = root.child('Users/' + session['username'] + '/displayName').get()
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    except TypeError:
        flash('Please complete the user setup first', 'danger')
        return redirect(url_for('register_info'))
    return render_template('profile.html', user=user_info, display_name=display_name)


class BloodPressure:
    def __init__(self, bp_date, bp_time, sys, dias, pulse):
        self.__bp_date = bp_date
        self.__bp_time = bp_time
        self.__sys = int(sys)
        self.__dias = int(dias)
        self.__pulse = int(pulse)
        self.__pulse_p = self.__sys - self.__dias
        if self.__sys > 160 or self.__dias > 100:
            self.__bp_indicator = "#FF5722"
        elif self.__sys > 142 or self.__dias > 95:
            self.__bp_indicator = "#FF9800"
        elif self.__sys > 134 or self.__dias > 90:
            self.__bp_indicator = "#FFC107"
        elif self.__sys > 128 or self.__dias > 85:
            self.__bp_indicator = "#FFEB3B"
        elif self.__sys > 120 or self.__dias > 80:
            self.__bp_indicator = "#CDDC39"
        else:
            self.__bp_indicator = "#8BC34A"

    def get_bp_date(self):
        return self.__bp_date

    def get_bp_time(self):
        return self.__bp_time

    def get_bp_datetime(self):
        return str(self.__bp_date)+str(self.__bp_time)

    def display_bp_date(self):
        return datetime.date(int(self.__bp_date[0:4]),
                             int(self.__bp_date[4:6]),
                             int(self.__bp_date[6:8])).strftime("%A, %d %B")

    def display_bp_time(self):
        return datetime.time(hour=int(self.__bp_time[0:2]),
                             minute=int(self.__bp_time[2:4])).isoformat(timespec='minutes')

    def get_sys(self):
        return self.__sys

    def get_dias(self):
        return self.__dias

    def get_pulse(self):
        return self.__pulse

    def get_pulse_p(self):
        return self.__pulse_p

    def get_bp_indicator(self):
        return self.__bp_indicator


@app.route('/bloodPressure')
def blood_pressure():
    try:
        uid_db = root
        user_bp_db = uid_db.child('BloodPressure/' + session['username']).get()
        bp_dict = {}
        bp_datetime_list = []
        bp_date_list = []
        bp_sys_list = []
        bp_dias_list = []
        bp_pulse_list = []
        bp_pulse_p_list = []
        for j in user_bp_db:
            bp_date_list.append(j[0:8])
        bp_date_list = list(set(bp_date_list))
        for k in bp_date_list:
            bp_dict.update({k: []})
        bp_date_list = list(reversed(sorted(bp_date_list)))
        for i in user_bp_db:
            bp = BloodPressure(i[0:8], i[8:12], user_bp_db[i]['systolic'], user_bp_db[i]['diastolic'],
                               user_bp_db[i]['pulse'])
            bp_datetime_list.append(bp.get_bp_date() + bp.get_bp_time())
            bp_sys_list.append(bp.get_sys())
            bp_dias_list.append(bp.get_dias())
            bp_pulse_list.append(bp.get_pulse())
            bp_pulse_p_list.append(bp.get_pulse_p())
            for k in bp_dict:
                if bp.get_bp_date() == k:
                    bp_dict[k].insert(0, bp)
        max_sys = max(bp_sys_list)
        max_dias = max(bp_dias_list)
        avg_sys = str(round(float(sum(bp_sys_list)) / max(len(bp_sys_list), 1)))
        avg_dias = str(round(float(sum(bp_dias_list)) / max(len(bp_sys_list), 1)))
        avg_bp = avg_sys + '/' + avg_dias
        avg_pp = round(float(sum(bp_pulse_p_list)) / max(len(bp_pulse_p_list), 1),1)
    except TypeError:
        flash('Please Finish the Account Setup First', 'danger')
        return redirect(url_for('register_bp'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('bloodPressure.html', bp_dict=bp_dict, bp_datetime_list=bp_datetime_list,
                           bp_date_list=bp_date_list, bp_sys_list=bp_sys_list, bp_dias_list=bp_dias_list,
                           bp_pulse_list=bp_pulse_list, avg_bp=avg_bp, avg_pp=avg_pp, max_sys=max_sys,
                           max_dias=max_dias)


@app.route('/weight')
def weight():
    try:
        uid_db = root
        user_info_db = uid_db.child('HealthDetail/' + session['username']).get()
        user_weight_db = uid_db.child('Weight/' + session['username']).get()
        user_bp_db = uid_db.child('BloodPressure/' + session['username']).get()
        user_info = HealthDetailSetup(user_info_db['gender'], user_info_db['birthday'], user_info_db['height'],
                                      user_weight_db, user_bp_db
                                      )
        weight_date_list = []
        weight_list = []
        weight_difference_list = []
        for i in user_weight_db:
            weight_date_list.insert(0, i)
            weight_list.insert(0, float(user_weight_db[i]))
        weight_list_len = len(weight_list)
        for i in range(0, len(weight_list)):
            try:
                weight_difference_list.append(round(weight_list[i]-weight_list[i+1], 1))
            except IndexError:
                weight_difference_list.append(0)
        display_weight_difference_list = []
        for i in weight_difference_list:
            if i > 0:
                display_weight_difference_list.append(
                    '<i class="material-icons weight-up" style="color:#F44336">arrow_drop_up</i>'+str(i))
            elif i == 0:
                display_weight_difference_list.append(
                    '<i class="weight-equal" style="color:#FFEB3B">=</i>' + str(i))
            elif i < 0:
                display_weight_difference_list.append(
                    '<i class="material-icons weight-down" style="color:#64DD17">arrow_drop_down</i>' + str(abs(i)))
        total_weight_difference = round((weight_list[0]-weight_list[-1]), 1)
        total_indicator = ''
        if total_weight_difference > 0:
            total_indicator = '<i class="material-icons weight-up" ' \
                              'style="color:#F44336;top: -5px;left: 10px;">arrow_drop_up</i>'
        elif total_weight_difference == 0:
            total_indicator = '<i class="weight-equal" style="color:#FFEB3B;top: -5px;left: 36px;">=</i>'
        elif total_weight_difference < 0:
            total_indicator = '<i class="material-icons weight-down" ' \
                              'style="color:#64DD17;top: -5px;left: 10px;">arrow_drop_down</i>'
            total_weight_difference = abs(total_weight_difference)

    except TypeError:
        flash('Please Finish the Account Setup First', 'danger')
        return redirect(url_for('register_info'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('weight.html', user=user_info, weight_date_list=weight_date_list, weight_list=weight_list,
                           weight_difference_list=weight_difference_list, weight_list_len=weight_list_len,
                           total_weight_difference=total_weight_difference, total_indicator=total_indicator,
                           display_weight_difference_list=display_weight_difference_list)


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
    try:
        Diet_db = root.child('Food').get()
        diet_list = []
        entries = 0
        total_calories = 0
        total_fats = 0
        total_carbohydrates = 0
        total_protein = 0
        total = 0
        username = session["username"]
        try:
            for dietID in Diet_db[username]:
                eachdiet = Diet_db[username][dietID]
                food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                            eachdiet['Carbohydrates Value'], eachdiet['Protein Value'], eachdiet['Diet Date'])
                total_calories += food.get_calories()
                entries += 1
                total_fats += food.get_fats()
                total_carbohydrates += food.get_carbohydrates()
                total_protein += food.get_protein()
                total = total_fats + total_carbohydrates + total_protein
                fat_percent = (total_fats / total) * 100
                fat_percentage = '{0:.0f}'.format(fat_percent)
                carbohydrate_percent = (total_carbohydrates / total) * 100
                carbohydrate_percentage = '{0:.0f}'.format(carbohydrate_percent)
                protein_percent = (total_protein / total) * 100
                protein_percentage = '{0:.0f}'.format(protein_percent)
                food.set_dietID(dietID)
                diet_list.append(food)
        except TypeError:
            return redirect(url_for('new_diet'))
        except KeyError:
            return redirect(url_for('new_diet'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('diet.html', diet=diet_list, total_calories=total_calories, entries=entries,
                           total_fats=total_fats,
                           total_carbohydrates=total_carbohydrates, total_protein=total_protein,
                           fat_percentage=fat_percentage,
                           carbohydrate_percentage=carbohydrate_percentage, protein_percentage=protein_percentage)


class Food(Form):
    diet_name = StringField('Name', [validators.length(min=1, max=150), validators.DataRequired()])
    diet_type = SelectField('Type', [validators.DataRequired()], choices=[("", "Select"), ("Foods", "Foods"),
                                                                          ("Drinks", "Drinks"), ("Fruits", "Fruits")])
    calories = IntegerField('Calories Value', [validators.number_range(min=1, max=999, message="Invalid number range"),
                                               validators.DataRequired()])
    fats = IntegerField('Fats Value', [validators.number_range(min=1, max=999, message="Invalid number range"),
                                       validators.DataRequired()])
    carbohydrates = IntegerField('Carbohydrates Value',
                                 [validators.number_range(min=1, max=999, message="Invalid number range"),
                                  validators.DataRequired()])
    proteins = IntegerField('Protein Value', [validators.number_range(min=1, max=999, message="Invalid number range"),
                                              validators.DataRequired()])
    calories = IntegerField('Calories Value')
    fats = IntegerField('Fats Value')
    carbohydrates = IntegerField('Carbohydrates Value')
    proteins = IntegerField('Protein Value')


@app.route('/new_diet', methods=['GET', 'POST'])
def new_diet():
    try:
        new_form = Food(request.form)
        username = session["username"]
        if request.method == 'POST' and new_form.validate():
            name = new_form.diet_name.data
            type = new_form.diet_type.data
            calories = new_form.calories.data
            fats = new_form.fats.data
            carbohydrates = new_form.carbohydrates.data
            protein = new_form.proteins.data
            diet_date = '{:%d-%m-%Y}'.format(datetime.date.today())
            food_diet = Diet(name, type, calories, fats, carbohydrates, protein, diet_date)
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
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('new_diet.html', form=new_form)


@app.route('/update_diet/<string:id>', methods=['GET', 'POST'])
def update_diet(id):
    try:
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
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('update_diet.html', form=update_form)


@app.route('/delete_diet/<string:id>', methods=['POST'])
def delete_diet(id):
    try:
        username = session["username"]
        Diet_db = root.child('Food/' + username + '/' + id)
        Diet_db.delete()
        flash('Diet deleted', 'Success')
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return redirect(url_for('diet'))


@app.route('/faq')
def faq():
    return render_template('faq.html')


class ActivityForm(Form):
    activity = StringField('Name Of Activity', [validators.Length(min=1, max=20), validators.DataRequired()])
    date = DateField('Date Of Activity', [validators.DataRequired('Date format is DD-MM-YYYY')], format='%d-%m-%Y')
    duration = IntegerField('Duration Of Activity', [validators.DataRequired('Please enter digits')])
    calories = IntegerField('Calories Burnt', [validators.DataRequired('Please enter digits')])


class Activity:
    def __init__(self, activity, date, duration, calories):
        self.__actID = ''
        self.__activity = activity
        self.__date = date
        self.__duration = duration
        self.__calories = calories

    def get_activity(self):
        return self.__activity

    def get_date(self):
        return self.__date

    def get_actID(self):
        return self.__actID

    def get_duration(self):
        return self.__duration

    def get_calories(self):
        return self.__calories

    def set_activity(self, activity):
        self.__activity = activity

    def set_date(self, date):
        self.__date = date

    def set_actID(self, actID):
        self.__actID = actID

    def set_duration(self, duration):
        self.__duration = duration

    def set_calories(self, calories):
        self.__calories = calories


@app.route('/input_activity', methods=['GET', 'POST'])
def input_activity():
    try:
        actform = ActivityForm(request.form)
        username = session["username"]
        if request.method == 'POST' and actform.validate():
            activity = actform.activity.data
            date = str(actform.date.data)
            duration = int(actform.duration.data)
            calories = int(actform.calories.data)
            latest_activity = Activity(activity, date, duration, calories)
            latest_activity.db = root.child('Activities/' + username)
            latest_activity.db.push({'Activity': latest_activity.get_activity(), 'Date': latest_activity.get_date(),
                                     'Duration': latest_activity.get_duration(),
                                     'Calories Burnt': latest_activity.get_calories()})
            flash('New activity updated successfully', 'success')
            return redirect(url_for('record'))
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('input_activity.html', actform=actform)


@app.route('/delete_activity/<string:id>', methods=['POST'])
def delete_activity(id):
    try:
        username = session["username"]
        Act_db = root.child('Activities/' + username + '/' + id)
        Act_db.delete()
        flash('Activity was deleted', 'success')
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return redirect(url_for('record'))


@app.route('/update_activity/<string:actID>', methods=['GET', 'POST'])
def update_activity(actID):
    try:
        username = session["username"]
        url = 'Activities/' + username + '/' + actID
        update_form = ActivityForm(request.form)
        if request.method == 'POST' and update_form.validate():
            activity = update_form.activity.data
            date = str(update_form.date.data)
            duration = int(update_form.duration.data)
            calories = int(update_form.calories.data)
            latest_activity = Activity(activity, date, duration, calories)
            Act_db = root.child('Activities/' + username + '/' + actID)
            Act_db.update({'Activity': latest_activity.get_activity(),
                            'Date': latest_activity.get_date(),
                            'Duration': latest_activity.get_duration(),
                            'Calories Burnt': latest_activity.get_calories()})

            flash('Activity updated successfully', 'success')

            return redirect(url_for('record'))
        else:
            eachact = root.child(url).get()
            activities = Activity(eachact['Activity'], eachact['Date'], eachact['Duration'],
                                      eachact['Calories Burnt'])
            activities.set_actID(actID)
            update_form.activity.data = activities.get_activity()
            date = activities.get_date()
            update_form.date.data = datetime.date(int(date[0:4]), int(date[5:7]),int(date[8:10]))
            update_form.duration.data = activities.get_duration()
            update_form.calories.data = activities.get_calories()
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('update_activity.html', actform=update_form)


@app.route('/record')
def record():
    try:
        username = session["username"]
        Act_db = root.child('Activities/' + username).get()
        act_list = []
        act_list_today = []
        diet_today = []
        diet_list = []
        overall_calories_out = 0
        overall_calories_in = 0
        total_calories_in = 0
        total_calories_out = 0
        message_today = 'You have not recorded any activities today! Get moving!'
        Diet_db = root.child('Food').get()
        try:
            for actID in Act_db:
                eachact = Act_db[actID]
                activities = Activity(eachact['Activity'], eachact['Date'], eachact['Duration'],
                                      eachact['Calories Burnt'])
                overall_calories_out += activities.get_calories()
                activities.set_actID(actID)
                act_list.append(activities)
                # if list is not empty, do the sorting by date
                # act_list.sort(key=xxxxx, reverse=True)
                act_list.sort(key=lambda activity: activity.get_date(), reverse=True)

                # check if the date of activity matches today's date
                if eachact['Date'] == str(datetime.date.today()):
                    activities_today = Activity(eachact['Activity'], eachact['Date'], eachact['Duration'],
                                                eachact['Calories Burnt'])
                    activities_today.set_actID(actID)
                    act_list_today.append(activities_today)
                    message_today = ''
                    # no message if there is an activity done today
                    for i in act_list_today:
                        total_calories_out += activities_today.get_calories()
                        # print(total_calories_out)

            for dietID in Diet_db[username]:
                eachdiet = Diet_db[username][dietID]
                food = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'], eachdiet['Fats Value'],
                            eachdiet['Carbohydrates Value'], eachdiet['Protein Value'], eachdiet['Diet Date'])
                overall_calories_in += food.get_calories()
                diet_list.append(food)
                diet_date = eachdiet['Diet Date'][6:10] + '-' + eachdiet['Diet Date'][3:5] + '-' + eachdiet[
                                                                                                       'Diet Date'][0:2]
                # print(str(datetime.date.today()))

                if diet_date == str(datetime.date.today()):
                    food_today = Diet(eachdiet['Name'], eachdiet['Type'], eachdiet['Calories Value'],
                                      eachdiet['Fats Value'],
                                      eachdiet['Carbohydrates Value'], eachdiet['Protein Value'], eachdiet['Diet Date'])
                    diet_today.append(food_today)
                    for i in diet_today:
                        total_calories_in += food_today.get_calories()
                        # print(total_calories_in)

        except TypeError:
            return redirect(url_for('input_activity'))
        except KeyError:
            return redirect(url_for('input_activity'))

        today_date = datetime.datetime.now().strftime("%A, %d %B %Y")
    except KeyError:
        flash('Please Login First to use our Services', 'primary')
        return redirect(url_for('login'))
    return render_template('track_and_record.html', activity=act_list, activity_today=act_list_today, date=today_date,
                           display_msg_today=message_today, cal_in=total_calories_in, cal_out=total_calories_out,
                           overall_in=overall_calories_in, overall_out=overall_calories_out)

@app.route('/rewards', methods=["GET","POST"])
def rewards():
    listofrewards={"500":{"Name":"Shirt","Redeem":False},
                   "1500":{"Name":"WaterBottle","Redeem":False},
                   "10000":{"Name":"Treadmill","Redeem":False},
                  "2500":{"Name":"Basketball","Redeem":False},
                  "4000":{"Name":"Shoe","Redeem":False},
                  "6000":{"Name":"Cap","Redeem":False}}
    selecteditems=[]
    rewardform = RewardsForm(request.form)
    username = session["username"]

    healthpoints_db = root.child("Rewards/"+username).get()
    redeemed_items_db=root.child("Redeemeditems/"+username).get()
    healthpointss = Rewards(healthpoints_db["healthpoints"])

    if request.method == 'POST' and rewardform.validate():
        if rewardform.redeemitem.data==True:

            selecteditems.append("NObesity T-Shirt")

            if healthpointss.get_healthpoints()<500:
                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(500)

        if rewardform.redeemitem2.data==True:
            selecteditems.append(
                "Water Bottle")

            if healthpointss.get_healthpoints()<1500:
                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(1500)
                healthpointss.get_healthpoints()
        if rewardform.redeemitem3.data==True:
            selecteditems.append(
                "Treadmill")

            if healthpointss.get_healthpoints()<10000:
                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(10000)
                healthpointss.get_healthpoints()
        if rewardform.redeemitem4.data==True:
            selecteditems.append(
                "Basketball")
            if healthpointss.get_healthpoints()<2500:

                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(2500)
                healthpointss.get_healthpoints()
        if rewardform.redeemitem5.data==True:
            selecteditems.append(
                 "Shoe")

            if healthpointss.get_healthpoints()<4000:
                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(4000)
                healthpointss.get_healthpoints()
        if rewardform.redeemitem6.data==True:
            selecteditems.append(
                "Cap")

            if healthpointss.get_healthpoints()<6000:
                flash('Not enough healthpoints', 'danger')
                return redirect(url_for('rewards'))
            else:
                healthpointss.minus_healthpoints(6000)
                healthpointss.get_healthpoints()

        root.child("Redeemeditems/" + username).set(selecteditems)

        root.child("Rewards/" + username).set({'Item': listofrewards, 'healthpoints': healthpointss.get_healthpoints()})
        flash('Successfully redeemed', 'success')
        return redirect(url_for('rewardconfirmation'))
    return render_template('rewards.html', healthpoints_db=healthpoints_db, healthpointss=healthpointss,rewardform=rewardform)

@app.route('/rewardconfirmation')
def rewardconfirmation():
    username = session["username"]
    healthpoints = root.child("Rewards/" + username+'/healthpoints').get()
    itemsredeemed= root.child("Redeemeditems/" + username).get()

    return render_template('rewardconfirmation.html',healthpoints=healthpoints, itemsredeemed=itemsredeemed)

class RewardsForm(Form):
    redeemitem=BooleanField("Redeem?")
    redeemitem2 = BooleanField("Redeem?")
    redeemitem3 = BooleanField("Redeem?")
    redeemitem4 = BooleanField("Redeem?")
    redeemitem5 = BooleanField("Redeem?")
    redeemitem6 = BooleanField("Redeem?")



class Rewards:

    def __init__(self,healthpoints=0):
        self.__healthpoints = healthpoints

    def get_healthpoints(self):
        return self.__healthpoints

    def set_healthpoints(self, healthpoints):
        self.__healthpoints = healthpoints

    def add_healthpoints(self, healthpoints):
        self.__healthpoints = self.__healthpoints + healthpoints

    def minus_healthpoints(self, healthpoints):
        self.__healthpoints = self.__healthpoints - healthpoints





@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    new_form = leaderboardform(request.form)
    if request.method == 'POST' and new_form.validate():
        count = 0
        score = new_form.score.data
        username = session["username"]
        userscore = Leaderboard(username, score)
        userscore.db = root.child('Leaderboard')  # map current userscore to firebase
        userscore.db.child(username).set({"Score": userscore.get_score()})  # push means to update score

        if count==0:
            if int(userscore.get_score()) > 2:
                root.child("Rewards/" + username).set(
                { 'healthpoints':20000,'count':count+1})
        else:
            root.child("Leaderboard/" + username).update(
                {'count': count + 1})
        flash('New score inserted successfully.First time doers will get 10000 healthpoints', 'success')
        return redirect(url_for('leaderboards'))


    return render_template('quiz.html', new_form=new_form)


@app.route('/leaderboards')
def leaderboards():
    leaderboard_db = root.child('Leaderboard').get()
    leaderboards_list = []  # create a list to store all the quiz results
    if leaderboard_db!=None:
        for eachusername in leaderboard_db:
            leaderboard = Leaderboard(eachusername, leaderboard_db[eachusername]["Score"])
            leaderboards_list.append(leaderboard)

    leaderboards_list.sort(key=lambda leaderboard: leaderboard.get_score(), reverse=True)
    for eachusername in leaderboards_list:
        rank = leaderboards_list.index(eachusername) + 1
        eachusername.set_rank(rank)

    return render_template('leaderboards.html', leaderboards_list=leaderboards_list)


class Leaderboard:
    def __init__(self, username, score, rank=0):
        self.__username = username
        self.__score = score
        self.__rank = rank

    def set_score(self, score):
        self.__score = score

    def set_username(self, username):
        self.__username = username

    def get_score(self):
        return self.__score

    def get_username(self):
        return self.__username

    def set_rank(self, rank):
        self.__rank = rank

    def get_rank(self):
        return self.__rank


class leaderboardform(Form):
    score = StringField("Score")

if __name__ == '__main__':
    app.run()

