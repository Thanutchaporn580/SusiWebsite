import flask
import models
import forms
from flask_login import login_required, login_user, logout_user, LoginManager
from flask import render_template, redirect, url_for
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
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/detail")
@login_required
def detail():

    return render_template("detail.html")


# หน้าเข้าสู่ระบบ
@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()
    if not form.validate_on_submit():

        return render_template("login.html", form=form)

    user = models.User.query.filter_by(username=form.username.data).first()
    if user and user.authenticate(form.password.data):
        login_user(user)
        return redirect(url_for("index"))

    return redirect(url_for("login", error="Invalid username or password"))


# หน้าออกจากระบบ
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# หน้าเปิดใช้งานการลงทะเบียนผู้ใช้ใหม่
@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if not form.validate_on_submit():
        return render_template("register.html", form=form)

    user = models.User()  # Initialize the user here
    form.populate_obj(user)  # Populate the user object with form data

    # สร้าง role user ถ้ายังไม่มี
    role = models.Role.query.filter_by(name="user").first()
    if not role:
        role = models.Role(name="user")
        models.db.session.add(role)

    user.roles.append(role)
    user.password_hash = form.password.data
    models.db.session.add(user)
    models.db.session.commit()

    return redirect(url_for("index"))


@app.route("/page")
@acl.roles_required("admin")
def page():
    return flask.render_template("page.html")


@app.route("/page2")
@login_required
def page2():
    return flask.render_template("page_2.html")


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()
    return flask.render_template(
        "tags_view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route("/tags/<tag_id>/update_tags", methods=["GET", "POST"])
def update_tags(tag_id):  # แก้ไข Tags ได้
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    form = forms.TagsForm()
    form_name = tag.name
    if not form.validate_on_submit():
        print(form.errors)
        return flask.render_template("update_tags.html", form=form, form_name=form_name)
    note = models.Note(id=tag_id)
    form.populate_obj(note)
    tag.name = form.name.data
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete_tags", methods=["GET", "POST"])
def delete_tags(tag_id):  # ลบ Tags ได้อย่างเดียว
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id))
        .scalars()
        .first()
    )
    tag.name = ""
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/notes/create_note", methods=["GET", "POST"])
def create_note():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "create_note.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []
    db = models.db
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
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/update_note", methods=["GET", "POST"])
def update_note(tag_id):  # แก้ไข Note และสามารถเปลี่ยนชื่อ Title ได้
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    form = forms.NoteForm()
    form_title = notes.title
    form_description = notes.description
    if not form.validate_on_submit():
        print(form.errors)
        return flask.render_template(
            "update_note.html",
            form=form,
            form_title=form_title,
            form_description=form_description,
        )
    note = models.Note(id=tag_id)
    form.populate_obj(note)
    notes.description = form.description.data
    notes.title = form.title.data
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete_note", methods=["GET", "POST"])
def delete_note(tag_id):  # ลบ Note เพียงอย่างเดียวไม่ได้ลบ Title
    db = models.db
    notes = (
        db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag_id))
        )
        .scalars()
        .first()
    )
    notes.description = ""
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_id>/delete", methods=["GET", "POST"])
def delete(tag_id):  # ลบทั้งหมดที่เกี่ยวกับ Tags
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
