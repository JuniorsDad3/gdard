# app/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SelectField,
    FloatField,
    DecimalField,
    IntegerField,
    TextAreaField,
    SubmitField,
    FileField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters")  # Remove "validators." prefix
    ])
    remember = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('Account Type',
        choices=[
            ('farmer', 'Farmer'),
            ('buyer', 'Buyer'),
            ('agent', 'Government Agent')
        ],
        validators=[DataRequired()]
    )
    location = StringField('Location', validators=[DataRequired()])
    farm_size = FloatField('Farm Size (hectares)',
        validators=[
            NumberRange(min=0, message='Farm size cannot be negative'),
            DataRequired()
        ]
    )

class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[('Grains', 'Grains'), ('Vegetables', 'Vegetables')])
    price = DecimalField('Price (R)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=1)])
    image = FileField('Product Image')  
    description = TextAreaField('Description')
    submit = SubmitField('Add Product')
