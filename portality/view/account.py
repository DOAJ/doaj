import uuid, json

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.wtf import TextField, TextAreaField, SelectField, HiddenField
from flask.ext.wtf import Form, PasswordField, validators, ValidationError

from portality.core import app, ssl_required
from portality import models
from portality import util

blueprint = Blueprint('account', __name__)

"""
if len(app.config.get('SUPER_USER',[])) > 0:
    firstsu = app.config['SUPER_USER'][0]
    if models.Account.pull(firstsu) is None:
        su = models.Account(id=firstsu)
        su.set_password(firstsu)
        su.save()
        print 'superuser account named - ' + firstsu + ' created.'
        print 'default password matches username. Change it.'
"""

@blueprint.route('/')
@login_required
@ssl_required
def index():
    if not current_user.has_role("list_users"):
        abort(401)
    """
    users = models.Account.query() #{"sort":{'id':{'order':'asc'}}},size=1000000
    if users['hits']['total'] != 0:
        accs = [models.Account.pull(i['_source']['id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {'id':acc.id, "email":acc.email, "role" : acc.role}
            if 'created_date' in acc.data:
                user['created_date'] = acc.data['created_date']
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/users.html', users=users)
    """
    return render_template("account/users.html", search_page=True, facetviews=["users"])


@blueprint.route('/<username>', methods=['GET','POST', 'DELETE'])
@login_required
@ssl_required
def username(username):
    acc = models.Account.pull(username)

    if acc is None:
        abort(404)
    elif ( request.method == 'DELETE' or 
            ( request.method == 'POST' and 
            request.values.get('submit',False) == 'Delete' ) ):
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        else:
            conf = request.values.get("confirm")
            if conf is None or conf != "confirm":
                flash('check the box to confirm you really mean it!', "error")
                return render_template('account/view.html', account=acc)
            acc.delete()
            flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))
    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        newdata = request.json if request.json else request.values
        if newdata.get('id',False):
            if newdata['id'] != username:
                acc = models.Account.pull(newdata['id'])
            else:
                newdata['api_key'] = acc.data['api_key']
        for k, v in newdata.items():
            if k not in ['submit','password', 'role', 'confirm']:
                acc.data[k] = v
        if 'password' in newdata and not newdata['password'].startswith('sha1'):
            acc.set_password(newdata['password'])
        # only super users can re-write roles
        if "role" in newdata and current_user.is_super:
            new_roles = [r.strip() for r in newdata.get("role").split(",")]
            acc.set_role(new_roles)
            
        acc.save()
        flash("Record updated")
        return render_template('account/view.html', account=acc)
    else:
        if util.request_wants_json():
            resp = make_response( 
                json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            # do an mget on the journals, so that we can present them to the user
            return render_template('account/view.html', account=acc)


def get_redirect_target(form=None):
    form_target = ''
    if form and hasattr(form, 'next') and getattr(form, 'next'):
        form_target = form.next.data

    for target in form_target, request.args.get('next',[]):
        if not target:
            continue
        if target == util.is_safe_url(target):
            return target
    return url_for('doaj.home')

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if self.next.data == util.is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

class LoginForm(RedirectForm):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@blueprint.route('/login', methods=['GET', 'POST'])
@ssl_required
def login():
    current_info = {'next':request.args.get('next', '')}
    form = LoginForm(request.form, csrf_enabled=False, **current_info)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = models.Account.pull(username)
        if user is None:
            user = models.Account.pull_by_email(username)
        if user is not None and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back.', 'success')
            # return form.redirect('index')
            # return redirect(url_for('doaj.home'))
            return redirect(get_redirect_target(form=form))
        else:
            flash('Incorrect username/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid credentials', 'error')
    return render_template('account/login.html', form=form)

@blueprint.route('/forgot', methods=['GET', 'POST'])
@ssl_required
def forgot():
    CONTACT_INSTR = ' Please <a href="{url}">contact us.</a>'.format(url=url_for('doaj.contact'))
    if request.method == 'POST':
        # get hold of the user account
        un = request.form.get('un',"")
        account = models.Account.pull(un)
        if account is None: 
            account = models.Account.pull_by_email(un)
        if account is None:
            util.flash_with_url('Hm, sorry, your account username / email address is not recognised.' + CONTACT_INSTR, 'error')
            return render_template('account/forgot.html')
        
        if not account.data.get('email'):
            util.flash_with_url('Hm, sorry, your account does not have an associated email address.' + CONTACT_INSTR, 'error')
            return render_template('account/forgot.html')

        # if we get to here, we have a user account to reset
        #newpass = util.generate_password()
        #account.set_password(newpass)
        reset_token = uuid.uuid4().hex
        account.set_reset_token(reset_token, app.config.get("PASSWORD_RESET_TIMEOUT", 86400))
        account.save()
        
        sep = "/"
        if request.url_root.endswith("/"):
            sep = ""
        reset_url = request.url_root + sep + "account/reset/" + reset_token
        
        to = [account.data['email'],app.config['ADMIN_EMAIL']]
        fro = app.config['ADMIN_EMAIL']
        subject = app.config.get("SERVICE_NAME","") + " - password reset"
        text = "A password reset request for account '" + account.id + "' has been received and processed.\n\n"
        text += "Please visit " + reset_url + " and enter your new password.\n\n"
        text += "If you are the user '" + account.id + "' and you requested this change, please visit that link now and set the password to something of your preference.\n\n"
        text += "If you are the user '" + account.id + "' and you did not request this change, you can ignore this email.\n\n"
        text += "Regards, The DOAJ Team"
        try:
            util.send_mail(to=to, fro=fro, subject=subject, text=text)
            flash('Instructions to reset your password have been sent to you. Please check your emails.')
            if app.config.get('DEBUG',False):
                flash('Debug mode - url for reset is ' + reset_url)
        except Exception as e:
            util.flash_with_url('Hm, sorry - sending the password reset email didn\'t work.' + CONTACT_INSTR, 'error')
            if app.config.get('DEBUG',False):
                flash('Debug mode - url for reset is' + reset_url)
            app.logger.error(str(uuid.uuid1()) + "\n" + repr(e))

    return render_template('account/forgot.html')

@blueprint.route("/reset/<reset_token>", methods=["GET", "POST"])
@ssl_required
def reset(reset_token):
    account = models.Account.get_by_reset_token(reset_token)
    if account is None:
        abort(404)
    
    if request.method == "GET":
        return render_template("account/reset.html", account=account)
        
    elif request.method == "POST":
        # check that the passwords match, and bounce if not
        pw = request.values.get("password")
        conf = request.values.get("confirm")
        if pw != conf:
            flash("Passwords do not match - please try again", "error")
            return render_template("account/reset.html", account=account)
            
        # update the user's account
        account.set_password(pw)
        account.remove_reset_token()
        account.save()
        flash("Password has been reset", "success")
        
        # log the user in
        login_user(account, remember=True)
        return redirect(url_for('doaj.home'))

@blueprint.route('/logout')
@ssl_required
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
    n = TextField('Email Address', [
        validators.Length(min=3, max=35), 
        validators.Email(message='Must be a valid email address')
    ])
    s = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('c', message='Passwords must match')
    ])
    c = PasswordField('Repeat Password')

@blueprint.route('/register', methods=['GET', 'POST'])
@login_required
@ssl_required
def register():
    if not app.config.get('PUBLIC_REGISTER',False) and not current_user.has_role("create_user"):
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
    return render_template('account/register.html', form=form)

