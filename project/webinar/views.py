import datetime

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask.ext.login import login_required, current_user

from project import app, db, opentok_sdk
from opentok import MediaModes
from project.models import User, Category, Webinar
from .forms import WebinarCreateForm, WebinarEditForm

webinar_blueprint = Blueprint('webinar', __name__,)


@webinar_blueprint.route('/webinar/new', methods=['GET', 'POST'])
@login_required
def new():
    form = WebinarCreateForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            session = opentok_sdk.create_session(media_mode=MediaModes.routed)
            cat = Category.query.filter_by(title=form.category.data).first()
            webinar = Webinar(
                title=form.title.data,
                description=form.description.data,
                session=session.session_id,
                token=opentok_sdk.generate_token(session.session_id),
                category_id=cat.id,
                teacher_id=current_user.id
            )
            db.session.add(webinar)
            db.session.commit()
            flash('Webinar successfully created.', 'success')
            return redirect(url_for("user.profile"))
        else:
            flash('Webinar was not successfully created.', 'danger')
            return redirect(url_for('webinar.new'))
    else:
        return render_template('webinar/new.html', form=form)


@webinar_blueprint.route('/webinar/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    form = WebinarEditForm(request.form)
    webinar = Webinar.query.get(id)
    if current_user.id == webinar.teacher_id:
        if request.method == 'POST':
            if form.validate_on_submit():
                webinar.title = form.title.data
                webinar. description = form.description.data
                db.session.commit()
                flash('Webinar successfully updated.', 'success')
                return redirect(url_for("webinar.show", id=webinar.id))
            else:
                flash('Webinar was not successfully updated.', 'danger')
                return redirect(url_for("webinar.edit", id=webinar.id))
        else:
            form = WebinarEditForm(obj=webinar)
            return render_template('webinar/edit.html', form=form)
    else:
        return render_template('errors/404.html', 404)


@webinar_blueprint.route('/webinar/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def destroy(id):
    webinar = Webinar.query.get(id)
    if current_user.id == webinar.teacher_id:
        if request.method == 'POST':
            db.session.delete(webinar)
            db.session.commit()
            flash('Webinar successfully deleted.', 'success')
            return redirect(url_for('user.profile'))
        else:
            return render_template('webinar/destroy.html', webinar=webinar)
    else:
        return render_template('errors/404.html', 404)


@webinar_blueprint.route('/webinar/<int:id>')
def show(id):
    webinar = Webinar.query.get(id)
    return render_template('webinar/show.html', webinar=webinar)


@webinar_blueprint.route('/webinar/<int:id>/register', methods=['POST'])
@login_required
def register(id):
    webinar = Webinar.query.get(id)
    user = User.query.get(current_user.id)
    if user not in webinar.students and user.id != webinar.teacher_id:
        webinar.students.append(user)
        db.session.commit()
        flash('You have successfully registered for this Webinar.', 'success')
        return redirect(url_for("webinar.show", id=webinar.id))
    else:
        flash('You are already registered for this Webinar.', 'info')
        return redirect(url_for('webinar.show', id=webinar.id))


@webinar_blueprint.route('/webinar/<session_id>/attend')
@login_required
def attend(session_id):
    webinar = Webinar.query.filter_by(session=session_id).first()
    if current_user in webinar.students or webinar.teacher_id == current_user.id:
        return render_template('webinar/attend.html', api_key=app.config['OT_API_KEY'], webinar=webinar)
    else:
        return redirect(url_for('webinar.show', id=webinar.id))


@webinar_blueprint.route('/webinar/<session_id>/lecture')
@login_required
def lecture(session_id):
    webinar = Webinar.query.filter_by(session=session_id).first()
    if current_user.id == webinar.teacher_id:
        return render_template('webinar/lecture.html', api_key=app.config['OT_API_KEY'], webinar=webinar)
    else:
        return redirect(url_for('webinar.show', id=webinar.id))
