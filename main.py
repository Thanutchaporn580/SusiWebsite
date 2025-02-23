import flask
import models
import forms
from forms import DiaryEntryForm
from flask_login import login_required, login_user, logout_user, LoginManager
from flask import render_template, redirect, url_for, flash, abort
import acl
from flask import Response, send_file, abort

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
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

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    if flask.request.method == "POST":
        logout_user()
        return redirect(url_for("index"))
    return render_template("logout.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        user = models.User(
            username=form.username.data,
            name=form.name.data,
        )
        user.set_password(form.password.data)
        role = models.Role.query.filter_by(name="user").first()
        if not role:
            role = models.Role(name="user")
            models.db.session.add(role)
        user.roles.append(role)
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
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return render_template("note.html", notes=notes)

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
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    if not tag:
        abort(404, description="Tag not found")
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()
    return render_template("tag_view.html", tag_name=tag_name, notes=notes)

@app.route("/tags/<tag_id>/update_tags", methods=["GET", "POST"])
def update_tags(tag_id):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    form = forms.TagsForm()
    form_name = tag.name
    if form.validate_on_submit():
        form.populate_obj(tag)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("update_tags.html", form=form, form_name=form_name)

@app.route("/tags/<tag_id>/delete_tags", methods=["GET", "POST"])
def delete_tags(tag_id):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/create_note", methods=["GET", "POST"])
@login_required
def create_note():
    db = models.db
    form = forms.NoteForm()
    if form.validate_on_submit():
        note = models.Note()
        form.populate_obj(note)
        note.tags = []
        for tag_name in form.tags.data:
            tag = (
                db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                .scalars()
                .first()
            )
            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)
            note.tags.append(tag)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("note"))
    return render_template("create_note.html", form=form)

@app.route("/tags/<tag_id>/update_note", methods=["GET", "POST"])
def update_note(tag_id):
    db = models.db
    note = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    form = forms.NoteForm()
    if form.validate_on_submit():
        form.populate_obj(note)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("update_note.html", form=form, note=note)

@app.route("/tags/<tag_id>/delete_note", methods=["GET", "POST"])
def delete_note(tag_id):
    db = models.db
    note = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/tags/<tag_id>/delete", methods=["GET", "POST"])
def delete(tag_id):
    db = models.db
    note = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/images")
def images():
    db = models.db
    images = db.session.execute(
        db.select(models.Upload).order_by(models.Upload.filename)
    ).scalars()
    return render_template("images.html", images=images)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    form = forms.UploadForm()
    db = models.db
    file_ = models.Upload()
    if form.validate_on_submit():
        file_ = models.Upload(
            filename=form.file.data.filename,
            data=form.file.data.read(),
        )
        db.session.add(file_)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("upload.html", form=form)

@app.route("/upload/<int:file_id>", methods=["GET"])
def get_image(file_id):
    file_ = models.Upload.query.get(file_id)
    if not file_ or not file_.data:
        abort(404, description="File not found")
    return Response(
        file_.data,
        headers={
            "Content-Disposition": f'inline;filename="{file_.filename}"',
            "Content-Type": "application/octet-stream",
        },
    )

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/description")
def description():
    return render_template("description.html")

if __name__ == "__main__":
    app.run(debug=True)