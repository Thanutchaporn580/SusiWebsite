import flask
import models
import forms
from forms import DiaryEntryForm
from flask_login import login_required, login_user, logout_user, LoginManager
from flask import render_template, redirect, url_for, flash
import acl
from flask import Response, send_file, abort
from flask_mail import Mail, Message

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

# Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "your-email@gmail.com"
app.config["MAIL_PASSWORD"] = "your-email-password"
app.config["MAIL_DEFAULT_SENDER"] = "your-email@gmail.com"

mail = Mail(app)
models.init_app(app)

@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return render_template("index.html", notes=notes)

@app.route("/detail")
@login_required
def detail():
    return render_template("detail.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "error")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        user = models.User(
            username=form.username.data,
            email=form.email.data,
            name=form.name.data,
            password_hash=form.password.data,
        )
        models.db.session.add(user)
        models.db.session.commit()
        flash("Registration successful", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/diary/create", methods=["GET", "POST"])
@login_required
def create_diary_entry():
    form = DiaryEntryForm()
    if form.validate_on_submit():
        entry = models.Note(
            title=form.title.data,
            description=form.description.data,
            tags=form.tags.data,
        )
        models.db.session.add(entry)
        models.db.session.commit()
        flash("Diary entry created", "success")
        return redirect(url_for("index"))
    return render_template("create_diary_entry.html", form=form)

@app.route("/note")
def note():
    return render_template("note.html")

@app.route("/page")
@acl.roles_required("admin")
def page():
    return render_template("page.html")

@app.route("/page2")
@login_required
def page2():
    return render_template("page2.html")

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    return render_template("tags_view.html", tag_name=tag_name)

@app.route("/tags/<tag_id>/update_tags", methods=["GET", "POST"])
def update_tags(tag_id):
    return render_template("update_tags.html", tag_id=tag_id)

@app.route("/tags/<tag_id>/delete_tags", methods=["GET", "POST"])
def delete_tags(tag_id):
    return render_template("delete_tags.html", tag_id=tag_id)

@app.route("/create_note", methods=["GET", "POST"])
@login_required
def create_note():
    return render_template("create_note.html")

@app.route("/tags/<tag_id>/update_note", methods=["GET", "POST"])
def update_note(tag_id):
    return render_template("update_note.html", tag_id=tag_id)

@app.route("/tags/<tag_id>/delete_note", methods=["GET", "POST"])
def delete_note(tag_id):
    return render_template("delete_note.html", tag_id=tag_id)

@app.route("/tags/<tag_id>/delete", methods=["GET", "POST"])
def delete(tag_id):
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    db.session.delete(notes)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/images")
def images():
    db = models.db
    images = db.session.execute(
        db.select(models.Upload).order_by(models.Upload.filename)
    ).scalars()
    return flask.render_template(
        "images.html",
        images=images,
    )

@app.route("/upload", methods=["GET", "POST"])
def upload():
    form = forms.UploadForm()
    db = models.db
    file_ = models.Upload()
    if not form.validate_on_submit():
        return flask.render_template(
            "upload.html",
            form=form,
        )
    if form.file.data:
        file_ = models.Upload(
            filename=form.file.data.filename,
            data=form.file.data.read(),  # Read binary data
        )
    db.session.add(file_)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/upload/<int:file_id>", methods=["GET"])
def get_image(file_id):
    # Query the database for the file with the given file_id
    file_ = models.Upload.query.get(file_id)
    if not file_ or not file_.data:
        # Return 404 if file is not found
        abort(404, description="File not found")
    # Serve the binary data as a file
    return Response(
        file_.data,
        headers={
            "Content-Disposition": f'inline;filename="{file_.filename}"',
            "Content-Type": "application/octet-stream",
        },
    )

if __name__ == "__main__":
    app.run(debug=True)
