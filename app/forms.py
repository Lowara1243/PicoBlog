from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from app.models import User, Tag


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email (optional)", validators=[Optional(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        if email.data:  # Only validate if email is provided
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError("Please use a different email address.")


class AdminRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email (optional)", validators=[Optional(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    allowed_tags = QuerySelectMultipleField(
        "Allowed Tags", query_factory=lambda: Tag.query.all(), get_label="name"
    )
    submit = SubmitField("Register User")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        if email.data:  # Only validate if email is provided
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError("Please use a different email address.")


class AdminEditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email (optional)", validators=[Optional(), Email()])
    allowed_tags = QuerySelectMultipleField(
        "Allowed Tags", query_factory=lambda: Tag.query.all(), get_label="name"
    )
    submit = SubmitField("Update User")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        if (
            email.data and email.data != self.original_email
        ):  # Only validate if email is provided and changed
            user = User.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError("Please use a different email address.")


class AdminChangePasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat New Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Change Password")


class TagForm(FlaskForm):
    name = StringField("Tag Name", validators=[DataRequired()])
    is_master = BooleanField("Master Tag")
    submit = SubmitField("Submit")

    def __init__(self, original_name=None, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        if name.data != self.original_name:
            tag = Tag.query.filter_by(name=self.name.data).first()
            if tag is not None:
                raise ValidationError("Please use a different tag name.")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("Body (Markdown)", validators=[DataRequired()])
    tags = QuerySelectMultipleField(
        "Tags",
        query_factory=lambda: Tag.query.order_by(Tag.name).all(),
        get_label=lambda tag: f"{tag.name} [M]" if tag.is_master else tag.name,
    )
    comments_enabled = BooleanField("Enable Comments", default=True)
    save_draft = SubmitField("Save as Draft")
    publish = SubmitField("Publish")


class CommentForm(FlaskForm):
    body = TextAreaField("Comment (Markdown supported)", validators=[DataRequired()])
    submit = SubmitField("Post Comment")
