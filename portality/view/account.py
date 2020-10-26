import uuid, json

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask_login import login_user, logout_user, current_user, login_required
from wtforms import StringField, HiddenField, PasswordField, validators, Form

from portality import util
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.models import Account
from portality.forms.validate import DataOptional, EmailAvailable, ReservedUsernames, IdAvailable, IgnoreUnchanged
from portality.notifications.application_emails import send_account_created_email, send_account_password_reset_email

blueprint = Blueprint('account', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def index():
    if not current_user.has_role("list_users"):
        abort(401)
    return render_template("account/users.html")


class UserEditForm(Form):

    # Let's not allow anyone to change IDs - there lies madness and destruction (referential integrity)
    # id = StringField('ID', [IgnoreUnchanged(), ReservedUsernames(), IdAvailable()])

    name = StringField('Account name', [DataOptional(), validators.Length(min=3, max=64)])
    email = StringField('Email Address', [
        IgnoreUnchanged(),
        validators.Length(min=3, max=254),
        validators.Email(message='Must be a valid email address'),
        EmailAvailable(),
        validators.EqualTo('email_confirm', message='Email confirmation must match'),
    ])
    email_confirm = StringField('Confirm email address')
    roles = StringField('User roles')
    password_change = PasswordField('Change password', [
        validators.EqualTo('password_confirm', message='Passwords must match'),
    ])
    password_confirm = PasswordField('Confirm password')


@blueprint.route('/<username>', methods=['GET', 'POST', 'DELETE'])
@login_required
@ssl_required
@write_required()
def username(username):
    acc = Account.pull(username)

    if acc is None:
        abort(404)
    if (request.method == 'DELETE' or
            (request.method == 'POST' and request.values.get('submit', False) == 'Delete')):
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        else:
            conf = request.values.get("delete_confirm")
            if conf is None or conf != "delete_confirm":
                flash('Check the box to confirm you really mean it!', "error")
                return render_template('account/view.html', account=acc, form=UserEditForm(obj=acc))
            acc.delete()
            flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))

    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)

        form = UserEditForm(obj=acc, formdata=request.form)

        if not form.validate():
            return render_template('account/view.html', account=acc, form=form)

        newdata = request.json if request.json else request.values
        if request.values.get('submit', False) == 'Generate a new API Key':
            acc.generate_api_key()

        # if 'id' in newdata and len(newdata['id']) > 0:
        #     if newdata['id'] != current_user.id == acc.id:
        #         flash('You may not edit the ID of your own account', 'error')
        #         return render_template('account/view.html', account=acc, form=form)
        #     else:
        #         acc.delete()        # request for the old record to be deleted from ES
        #         acc.set_id(newdata['id'])

        if 'name' in newdata:
            acc.set_name(newdata['name'])
        if 'password_change' in newdata and len(newdata['password_change']) > 0 and not newdata['password_change'].startswith('sha1'):
            acc.set_password(newdata['password_change'])

        # only super users can re-write roles
        if "roles" in newdata and current_user.is_super:
            new_roles = [r.strip() for r in newdata.get("roles").split(",")]
            acc.set_role(new_roles)

        if "marketing_consent" in newdata:
            acc.set_marketing_consent(newdata["marketing_consent"] == "true")

        if 'email' in newdata and len(newdata['email']) > 0 and newdata['email'] != acc.email:
            acc.set_email(newdata['email'])

            # If the user updated their own email address, invalidate the password and require verification again.
            if current_user.id == acc.id:
                acc.clear_password()
                reset_token = uuid.uuid4().hex
                acc.set_reset_token(reset_token, app.config.get("PASSWORD_RESET_TIMEOUT", 86400))
                try:
                    send_account_password_reset_email(acc)
                    flash("Email address updated. You have been logged out for email address verification.")
                except Exception:
                    flash('Error - Could not send verification, aborting email change', 'error')
                    return render_template('account/view.html', account=acc, form=form)
                acc.save()
                logout_user()

                if app.config.get('DEBUG', False):
                    reset_url = url_for('account.reset', reset_token=acc.reset_token)
                    util.flash_with_url('Debug mode - url for reset is <a href={0}>{0}</a>'.format(reset_url))

                return redirect(url_for('doaj.home'))

        acc.save()
        flash("Record updated")
        return render_template('account/view.html', account=acc, form=form)

    else:  # GET
        if util.request_wants_json():
            resp = make_response(
                json.dumps(acc.data, sort_keys=True, indent=4))
            resp.mimetype = "application/json"
            return resp
        else:
            form = UserEditForm(obj=acc)
            return render_template('account/view.html', account=acc, form=form)


def get_redirect_target(form=None):
    form_target = ''
    if form and hasattr(form, 'next') and getattr(form, 'next'):
        form_target = form.next.data

    for target in form_target, request.args.get('next', []):
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
    user = StringField('E-mail Address', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])


@blueprint.route('/login', methods=['GET', 'POST'])
@ssl_required
def login():
    current_info = {'next': request.args.get('next', '')}
    form = LoginForm(request.form, csrf_enabled=False, **current_info)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.user.data

        # If our settings allow, try getting the user account by ID first, then by email address
        if app.config.get('LOGIN_VIA_ACCOUNT_ID', False):
            user = Account.pull(username) or Account.pull_by_email(username)
        else:
            user = Account.pull_by_email(username)

        # If we have a verified user account, proceed to attempt login
        try:
            if user is not None and user.check_password(password):
                login_user(user, remember=True)
                flash('Welcome back.', 'success')
                return redirect(get_redirect_target(form=form))
            else:
                form.password.errors.append('The password you entered is incorrect. Try again or <a href="{0}">reset your password</a>.'.format(url_for(".forgot")))
        except KeyError:
            # Account has no password set, the user needs to reset or use an existing valid reset link
            FORGOT_INSTR = '<a href="{url}">&lt;click here&gt;</a> to send a new reset link.'.format(url=url_for('.forgot'))
            util.flash_with_url('Account verification is incomplete. Check your emails for the link or ' + FORGOT_INSTR,
                                'error')
            return redirect(url_for('doaj.home'))

    if request.args.get("redirected") == "apply":
        form['next'].data = url_for("apply.public_application")
        return render_template('account/login_to_apply.html', form=form)
    return render_template('account/login.html', form=form)


@blueprint.route('/forgot', methods=['GET', 'POST'])
@ssl_required
@write_required()
def forgot():
    CONTACT_INSTR = ' Please <a href="{url}">contact us.</a>'.format(url=url_for('doaj.contact'))
    if request.method == 'POST':
        # get hold of the user account
        un = request.form.get('un', "")
        if app.config.get('LOGIN_VIA_ACCOUNT_ID', False):
            account = Account.pull(un) or Account.pull_by_email(un)
        else:
            account = Account.pull_by_email(un)

        if account is None:
            util.flash_with_url('Error - your account username / email address is not recognised.' + CONTACT_INSTR,
                                'error')
            return render_template('account/forgot.html')

        if not account.data.get('email'):
            util.flash_with_url('Error - your account does not have an associated email address.' + CONTACT_INSTR,
                                'error')
            return render_template('account/forgot.html')

        # if we get to here, we have a user account to reset
        reset_token = uuid.uuid4().hex
        account.set_reset_token(reset_token, app.config.get("PASSWORD_RESET_TIMEOUT", 86400))
        account.save()

        try:
            send_account_password_reset_email(account)
            flash('Instructions to reset your password have been sent to you. Please check your emails.')
        except Exception as e:
            magic = str(uuid.uuid1())
            util.flash_with_url('Error - sending the password reset email didn\'t work.' + CONTACT_INSTR + ' It would help us if you also quote this magic number: ' + magic + ' . Thank you!', 'error')
            app.logger.error(magic + "\n" + repr(e))

        if app.config.get('DEBUG', False):
            util.flash_with_url('Debug mode - url for reset is <a href={0}>{0}</a>'.format(
                url_for('account.reset', reset_token=account.reset_token)))

    return render_template('account/forgot.html')


class ResetForm(Form):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@blueprint.route("/reset/<reset_token>", methods=["GET", "POST"])
@ssl_required
@write_required()
def reset(reset_token):
    form = ResetForm(request.form, csrf_enabled=False)
    account = Account.get_by_reset_token(reset_token)
    if account is None:
        abort(404)

    if request.method == "POST" and form.validate():
        # check that the passwords match, and bounce if not
        pw = request.values.get("password")
        conf = request.values.get("confirm")
        if pw != conf:
            flash("Passwords do not match - please try again", "error")
            return render_template("account/reset.html", account=account, form=form)

        # update the user's account
        account.set_password(pw)
        account.remove_reset_token()
        account.save()
        flash("New password has been set and you're now logged in.", "success")

        # log the user in
        login_user(account, remember=True)
        return redirect(url_for('doaj.home'))

    return render_template("account/reset.html", account=account, form=form)


@blueprint.route('/logout')
@ssl_required
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect('/')


class RegisterForm(RedirectForm):
    identifier = StringField('ID', [ReservedUsernames(), IdAvailable()])
    name = StringField('Name', [validators.Optional(), validators.Length(min=3, max=64)])
    email = StringField('Email Address', [
        validators.DataRequired(),
        validators.Length(min=3, max=254),
        validators.Email(message='Must be a valid email address'),
        EmailAvailable()
    ])
    roles = StringField('Roles')


@blueprint.route('/register', methods=['GET', 'POST'])
@ssl_required
@write_required()
def register():
    # 3rd-party registration only for those with create_user role, only allow public registration when configured
    if current_user.is_authenticated and not current_user.has_role("create_user") \
            or current_user.is_anonymous and app.config.get('PUBLIC_REGISTER', False) is False:
        abort(401)      # todo: we may need a template to explain this since it's linked from the application form

    form = RegisterForm(request.form, csrf_enabled=False, roles='api,publisher', identifier=Account.new_short_uuid())
    if request.method == 'POST' and form.validate():
        account = Account.make_account(email=form.email.data, username=form.identifier.data, name=form.name.data,
                                       roles=[r.strip() for r in form.roles.data.split(',')])
        account.save()

        send_account_created_email(account)

        if app.config.get('DEBUG', False):
            util.flash_with_url('Debug mode - url for verify is <a href={0}>{0}</a>'.format(url_for('account.reset', reset_token=account.reset_token)))

        if current_user.is_authenticated:
            util.flash_with_url('Account created for {0}. View Account: <a href={1}>{1}</a>'.format(account.email, url_for('.username', username=account.id)))
            return redirect(url_for('.index'))
        else:
            flash('Thank you, please verify email address ' + form.email.data + ' to set your password and login.',
                  'success')

        # We must redirect home because the user now needs to verify their email address.
        return redirect(url_for('doaj.home'))

    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html', form=form)
