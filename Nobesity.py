from flask import Flask, render_template, request
#from wtforms import Form, StringField, TextAreaField, RadioField, SelectField, validators

app = Flask(__name__)


@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()
