import uuid, json
from copy import deepcopy

from flask import Blueprint, request, url_for, flash, redirect, abort, make_response
from flask import render_template
from flask.ext.login import login_user, logout_user, current_user
from flask.ext.wtf import Form, TextField, TextAreaField, SelectField, PasswordField, validators, ValidationError

from portality import auth
from portality.core import app
import portality.models as models
import portality.util as util

blueprint = Blueprint('account', __name__)

jsite_config = deepcopy(app.config['JSITE_OPTIONS'])
jsite_config['data'] = False
jsite_config['editable'] = False
jsite_config['facetview']['initialsearch'] = False

@blueprint.route('/')
def index():
    if current_user.is_anonymous():
        abort(401)
    users = models.Account.query() #{"sort":{'id':{'order':'asc'}}},size=1000000
    if users['hits']['total'] != 0:
        accs = [models.Account.pull(i['_source']['id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {'id':acc.id}
            if 'created_date' in acc.data:
                user['created_date'] = acc.data['created_date']
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/all.html', users=users, superuser=current_user.is_super, jsite_options=json.dumps(jsite_config))


@blueprint.route('/<username>', methods=['GET','POST', 'DELETE'])
def username(username):
    acc = models.Account.pull(username)

    if request.method == 'DELETE':
        if not auth.user.update(acc,current_user):
            abort(401)
        if acc: acc.delete()
        return ''
    elif request.method == 'POST':
        if not auth.user.update(acc,current_user):
            abort(401)
        info = request.json
        if info.get('id',False):
            if info['id'] != username:
                acc = models.Account.pull(info['id'])
            else:
                info['api_key'] = acc.data['api_key']
        acc.data = info
        if 'password' in info and not info['password'].startswith('sha1'):
            acc.set_password(info['password'])
        acc.save()
        resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        if not acc:
            abort(404)
        if util.request_wants_json():
            if not auth.user.update(acc,current_user):
                abort(401)
            resp = make_response( json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            admin = True if auth.user.update(acc,current_user) else False
            return render_template('account/view.html', 
                current_user=current_user, 
                record=acc.json, 
                admin=admin,
                account=acc,
                superuser=auth.user.is_super(current_user), 
                jsite_options=json.dumps(jsite_config)
            )


class LoginForm(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = models.Account.pull(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back.', 'success')
            return redirect('/')
        else:
            flash('Incorrect username/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')
    return render_template('account/login.html', form=form, jsite_options=json.dumps(jsite_config))


@blueprint.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect('/')


def existscheck(form, field):
    test = models.Account.pull(form.w.data)
    if test:
        raise ValidationError('Taken! Please try another.')

class RegisterForm(Form):
    w = TextField('Username', [validators.Length(min=3, max=25),existscheck])
    n = TextField('Email Address', [validators.Length(min=3, max=35), validators.Email(message='Must be a valid email address')])
    s = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('c', message='Passwords must match')
    ])
    c = PasswordField('Repeat Password')

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if not app.config.get('PUBLIC_REGISTER',False) and not auth.user.is_super(current_user):
        abort(401)
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        api_key = str(uuid.uuid4())
        account = models.Account(
            id=form.w.data, 
            email=form.n.data,
            api_key=api_key
        )
        account.set_password(form.s.data)
        account.save()
        flash('Account created for ' + account.id + '. If not listed below, refresh the page to catch up.', 'success')
        return redirect('/account')
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html', form=form, jsite_options=json.dumps(jsite_config))

