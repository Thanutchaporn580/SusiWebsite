from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets, validators, fields
import models
from flask_wtf import FlaskForm, file

# ฟอร์มการลงทะเบียนและเข้าสู่ระบบ
BaseUserForm = model_form(
    models.User,
    base_class=FlaskForm,
    exclude=["created_date", "updated_date", "status", "_password_hash"],
    db_session=models.db.session,
)


class LoginForm(FlaskForm):
    username = fields.StringField("Username", [validators.DataRequired()])
    password = fields.PasswordField("Password", [validators.DataRequired()])


class RegisterForm(BaseUserForm):
    username = fields.StringField(
        "Username", [validators.DataRequired(), validators.Length(min=6)]
    )
    password = fields.PasswordField(
        "Password", [validators.DataRequired(), validators.Length(min=6)]
    )
    name = fields.StringField(
        "Name", [validators.DataRequired(), validators.Length(min=6)]
    )


# ฟอร์มสำหรับโน้ต
class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        data = []
        if valuelist:
            data = [x.strip() for x in valuelist[0].split(",")]
        if not self.remove_duplicates:
            self.data = data
            return
        self.data = []
        for d in data:
            if d not in self.data:
                self.data.append(d)

    def _value(self):
        if self.data:
            return ", ".join(self.data)
        else:
            return ""


BaseNoteForm = model_form(
    models.Note,
    base_class=FlaskForm,
    exclude=["created_date", "updated_date"],
    db_session=models.db.session,
)

BaseTagsForm = model_form(
    models.Tag,
    base_class=FlaskForm,
    exclude=["created_date", "updated_date"],
    db_session=models.db.session,
)


class NoteForm(BaseNoteForm):
    tags = TagListField("Tags")


class TagsForm(BaseTagsForm):
    tags = TagListField("Tags")


BaseUploadForm = model_form(
    models.Upload,
    base_class=FlaskForm,
    db_session=models.db.session,
    exclude=["created_date", "updated_date", "status", "filename"],
)


class UploadForm(BaseUploadForm):
    file = fields.FileField(
        "Upload team image (png or jpg) , Recommended image size:250(px) x 230(px)",
        validators=[
            file.FileAllowed(["png", "jpg", "jpeg"], "You can use onlyjpg , png"),
        ],
    )
