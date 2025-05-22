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
    FileField,
    DateField,
    SelectMultipleField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo

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
    farm_size  = IntegerField('Farm Size (ha)', validators=[Optional()])  # ← make optional
    location   = StringField('Location', validators=[Optional(), Length(0,100)])

    def validate(self, extra_validators=None):
        # Call parent first
        if not super().validate(extra_validators=extra_validators):
            return False

        # Now add conditional logic
        if self.user_type.data == 'farmer' and not self.farm_size.data:
            self.farm_size.errors.append('Farm size is required for farmers.')
            return False

        return True

class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Grains', 'Grains'),
        ('Vegetables', 'Vegetables'),
        ('Fruits', 'Fruits')
    ])
    price = FloatField('Price (R)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=1)])
    image = FileField('Product Image')
    certifications = SelectMultipleField('Certifications', choices=[
        ('organic', 'Organic'),
        ('fairtrade', 'Fair Trade'),
        ('sustainable', 'Sustainable')
    ])
    description = TextAreaField('Description')
    submit = SubmitField('Add Product')

class FundingApplicationForm(FlaskForm):
    program = SelectField('Program', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount Requested (R)', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Project Description', validators=[DataRequired()])
    documents = FileField('Supporting Documents')
    submit = SubmitField('Submit Application')

class SupportTicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('technical', 'Technical'),
        ('billing', 'Billing'),
        ('general', 'General')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    message = TextAreaField('Message', validators=[DataRequired()])
    attachments = FileField('Attachments')
    submit = SubmitField('Submit Ticket')

class InspectionForm(FlaskForm):
    farm = SelectField('Farm', coerce=int, validators=[DataRequired()])
    inspector = SelectField('Inspector', coerce=int, validators=[DataRequired()])
    date = DateField('Inspection Date', validators=[DataRequired()])
    type = SelectField('Type', choices=[
        ('routine', 'Routine'),
        ('compliance', 'Compliance'),
        ('special', 'Special')
    ])
    notes = TextAreaField('Notes')
    submit = SubmitField('Schedule Inspection')

