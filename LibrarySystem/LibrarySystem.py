from flask import Flask, render_template, request
from wtforms import Form, StringField, TextAreaField, RadioField, SelectField

app = Flask(__name__)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/viewpublications')
def viewpublications():
    return render_template('view_all_publications.html')


class PublicationForm(Form):
    title = StringField('Title')
    pubtype = RadioField('Type Of Publication', choices=[('sbook', 'Book'), ('smag', 'Magazine')], default='sbook')
    category = SelectField('Caterory', choices=[('', 'Select'), ('FANTASY', 'Fantasy'), ('FASHION', 'Fashion'),
                                                ('THRILLER', 'Thriller'), ('CRIME', 'Crime'), ('BUSINESS', 'Business')],
                           default='')

    publisher = StringField('Publisher')
    status = SelectField('status', choices=[('', 'Select'), ('P', 'Pending'), ('A', 'Available For Borrowing'),
                                            ('R', 'Only For Reference')], default='')
    isbn = StringField('ISBN No')
    author = StringField('Author')
    synopsis = TextAreaField('Synopsis')
    frequency = RadioField('Frequency', choices=[('D', 'Daily'), ('W', 'Weekly'), ('M', 'Monthly')])


@app.route('/newpublication')
def new():
    form = PublicationForm(request.form)
    return render_template('create_publication.html', form=form)


@app.route('/update')
def update_publication():
    # Setting values to the update_publication.html
    form = PublicationForm(request.form)
    form.title.data = 'Harry Potter and The Half Blood Prince'
    form.pubtype.data = 'sbook'
    form.category.data = 'FANTASY'
    form.publisher.data = 'Bloomsbury'
    form.status.data = 'A'
    form.isbn.data = '0-7475-8108-8'
    form.author.data = 'J. K. Rowling'
    form.synopsis.data = 'Severus Snape, a member of the Order of the Phoenix, meets with Narcissa Malfoy, Draco''s mother, and Lord Voldemort''s faithful supporter Bellatrix Lestrange. Narcissa expresses concern that her son might not survive a dangerous mission given to him by Lord Voldemort. Bellatrix feels Snape will be of no help until he surprises her by making an Unbreakable Vow with Narcissa, swearing on his life that he will protect and assist Draco in his mission.'
    return render_template('update_publication.html', form=form)


if __name__ == '__main__':
    app.run()