import random
import uuid, json

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask_login import login_user, logout_user, current_user, login_required
from wtforms import StringField, HiddenField, PasswordField, DecimalField, validators, Form

from portality import util
from portality import constants
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.models import Account, Event
from portality.forms.validate import DataOptional, EmailAvailable, ReservedUsernames, IdAvailable, IgnoreUnchanged
from portality.bll import DOAJ
from portality.bll import exceptions as bll_exc
from portality.ui.messages import Messages

from portality.ui import templates

blueprint = Blueprint('account', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def index():
    if not current_user.has_role("list_users"):
        abort(401)
    return render_template(templates.USER_LIST)


class UserEditForm(Form):

    # Let's not allow anyone to change IDs - there lies madness and destruction (referential integrity)
    # id = StringField('ID', [IgnoreUnchanged(), ReservedUsernames(), IdAvailable()])

    name = StringField('Account name', [DataOptional(), validators.Length(min=3, max=64)])
    email = StringField('Email address', [
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

    template = templates.PUBLIC_EDIT_USER
    if current_user.is_super:
        template = templates.ADMIN_EDIT_USER
    elif current_user.has_role(constants.ROLE_ASSOCIATE_EDITOR) or current_user.has_role(constants.ROLE_EDITOR):
        template = templates.EDITOR_EDIT_USER

    if acc is None:
        abort(404)
    if (request.method == 'DELETE' or
            (request.method == 'POST' and request.values.get('submit', False) == 'Delete')):
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        else:
            conf = request.values.get("delete_confirm")
            if conf is None or conf != "delete_confirm":
                Messages.flash(Messages.ACCOUNT__CONFIRM_CHECKBOX_REQUIRED)
                return render_template(template, account=acc, form=UserEditForm(obj=acc))
            acc.delete()
            Messages.flash(Messages.ACCOUNT__DELETED.format(id=acc.id))
            return redirect(url_for('.index'))

    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)

        form = UserEditForm(obj=acc, formdata=request.form)

        if not form.validate():
            return render_template(template, account=acc, form=form)

        newdata = request.values
        try:
            newdata = request.json
        except:
            pass

        # newdata = request.json if request.json else request.values
        if request.values.get('submit', False) == 'Generate a new API Key':
            acc.generate_api_key()

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
                acc.save()

                events_svc = DOAJ.eventsService()
                events_svc.trigger(Event(constants.EVENT_ACCOUNT_PASSWORD_RESET, acc.id, context={"account" : acc.data}))
                Messages.flash(Messages.ACCOUNT__EMAIL_UPDATED_LOGGED_OUT)

                logout_user()

                if app.config.get('DEBUG', False):
                    reset_url = url_for('account.reset', reset_token=acc.reset_token)
                    util.flash_with_url('Debug mode - url for reset is <a href={0}>{0}</a>'.format(reset_url))

                return redirect(url_for('doaj.home'))

        acc.save()
        Messages.flash(Messages.ACCOUNT__RECORD_UPDATED)
        return render_template(template, account=acc, form=form)

    else:  # GET
        if util.request_wants_json():
            resp = make_response(
                json.dumps(acc.data, sort_keys=True, indent=4))
            resp.mimetype = "application/json"
            return resp
        else:
            form = UserEditForm(obj=acc)
            return render_template(template, account=acc, form=form)


def get_redirect_target(form=None, acc=None):
    form_target = ''
    if form and hasattr(form, 'next') and getattr(form, 'next'):
        form_target = form.next.data

    for target in form_target, request.args.get('next', []):
        if not target:
            continue
        if target == util.is_safe_url(target):
            return target

    if acc is None:
        return ""

    destinations = app.config.get("ROLE_LOGIN_DESTINATIONS")
    for role, dest in destinations:
        if acc.has_role(role):
            return url_for(dest)

    return url_for(app.config.get("DEFAULT_LOGIN_DESTINATION"))


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
    user = StringField('Email address or username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.Optional()])
    action = StringField('Action', [validators.DataRequired()])

class LoginCodeForm(RedirectForm):
    code = StringField('Code', [validators.DataRequired()])
    user = HiddenField('User')

def _get_param(param_name):
    """Get parameter value from either GET or POST request"""
    return request.args.get(param_name) or request.form.get(param_name)

def _complete_verification(account):
    """Complete the verification process and log in the user"""
    account.remove_login_code()
    account.save()
    login_user(account)


def get_wait_period(secs: int) -> str:
    secs = int(secs or 0)
    if secs >= 7200:
        return f"{(secs + 3599) // 3600} hours"
    if secs >= 3600:
        return "1 hour"
    if secs >= 120:
        return f"{(secs + 59) // 60} minutes"
    if secs >= 60:
        return "1 minute"
    return f"{secs} seconds"


def _handle_pwless_login(user, form, redirected: str = ""):
    """ Handler for passwordless login backoff + email sending.

    Returns a rendered verify_code template with appropriate resend_wait.
    """
    cps = DOAJ.concurrencyPreventionService()
    allowed, wait_remaining, interval = cps.record_pwless_resend(user.email)

    if not allowed:
        tpl = Messages.ACCOUNT__PWLESS__RESEND_RATE_LIMIT
        Messages.flash((tpl[0].format(wait=get_wait_period(wait_remaining)), tpl[1]))
        return render_template(templates.LOGIN_VERIFY_CODE, email=user.email, form=form, resend_wait=wait_remaining)

    try:
        svc = DOAJ.accountService()
        code = svc.initiate_login_code(user)
        svc.send_login_code_email(user, code, redirected or "")
        Messages.flash(Messages.ACCOUNT__PWLESS__EMAIL_SENT)
    except bll_exc.ArgumentException:
        Messages.flash(Messages.ACCOUNT__PWLESS__EMAIL_ERROR)

    return render_template(templates.LOGIN_VERIFY_CODE, email=user.email, form=form, resend_wait=interval)

@blueprint.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    form = LoginForm(request.form, csrf_enabled=False)

    # Handle resend requests posted from the code entry page
    if request.method == 'POST' and (request.form.get('action') == 'resend'):
        email = _get_param('email')
        if not email:
            Messages.flash(Messages.ACCOUNT__EMAIL_REQUIRED_FOR_RESEND)
            return redirect(url_for('account.login'))

        user = Account.pull_by_email(email)
        if not user:
            Messages.flash(Messages.ACCOUNT__NOT_RECOGNISED)
            return redirect(url_for('account.login'))

        return _handle_pwless_login(user, form, _get_param('redirected') or '')

    svc = DOAJ.accountService()

    try:
        account, _redirected = svc.verify_login_code(
            encrypted_token=_get_param('token'),
            email=_get_param('email'),
            code=_get_param('code'),
        )
    except bll_exc.ArgumentException:
        Messages.flash(Messages.ACCOUNT__REQUIRED_PARAMS_NOT_AVAILABLE)
        return redirect(url_for('account.login'))
    except bll_exc.NoSuchObjectException:
        Messages.flash(Messages.ACCOUNT__NOT_RECOGNISED)
        return redirect(url_for('account.login'))
    except bll_exc.IllegalStatusException:
        Messages.flash(Messages.ACCOUNT__INVALID_OR_EXPIRED_CODE)
        return redirect(url_for('account.login'))

    # Preserve existing UI behavior for application redirect
    redirected_page = request.args.get("redirected") or _redirected
    if redirected_page == "apply":
        form['next'].data = url_for("apply.public_application")

    _complete_verification(account)
    return redirect(get_redirect_target(form=form, acc=account))



def get_user_account(username):
    # If our settings allow, try getting the user account by ID first, then by email address
    if app.config.get('LOGIN_VIA_ACCOUNT_ID', False):
        return Account.pull(username) or Account.pull_by_email(username)
    return Account.pull_by_email(username)


def handle_login_code_request(user, form):
    LOGIN_CODE_LENGTH = 6
    LOGIN_CODE_TIMEOUT = 600  # 10 minutes

    code = ''.join(str(random.randint(0, 9)) for _ in range(LOGIN_CODE_LENGTH))
    user.set_login_code(code, timeout=LOGIN_CODE_TIMEOUT)
    user.save()

    svc = DOAJ.accountService()
    svc.send_login_code_email(user, code, request.args.get("redirected", ""))
    Messages.flash(Messages.ACCOUNT__PWLESS__EMAIL_SENT)

    return render_template(templates.LOGIN_VERIFY_CODE, email=user.email, form=form)

def handle_password_login(user, form):
    if user.check_password(form.password.data):
        login_user(user, remember=True)
        Messages.flash(Messages.ACCOUNT__WELCOME_BACK)
        return redirect(get_redirect_target(form=form, acc=user))
    else:
        forgot_url = url_for(".forgot")
        form.password.errors.append(
            f'The password you entered is incorrect. Try again or <a href="{forgot_url}">reset your password</a>.'
        )

def handle_incomplete_verification():
    forgot_url = url_for('.forgot')
    forgot_instructions = f'<a href="{forgot_url}">&lt;click here&gt;</a> to send a new reset link.'
    util.flash_with_url(
        'Account verification is incomplete. Check your emails for the link or ' + forgot_instructions,
        'error'
    )

def handle_login_template_rendering(form):
    if request.args.get("redirected") == "apply":
        form['next'].data = url_for("apply.public_application")
        return render_template(templates.LOGIN_TO_APPLY, form=form)
    return render_template(templates.GLOBAL_LOGIN, form=form)

@blueprint.route('/login', methods=['GET', 'POST'])
@ssl_required
def login():
    current_info = {'next': request.args.get('next', '')}
    form = LoginForm(request.form, csrf_enabled=False, **current_info)
    if request.method == 'POST' and form.validate():
        username = form.user.data
        action = request.form.get('action')

        svc = DOAJ.accountService()
        try:
            user = svc.resolve_user(username)
            if user is None:
                raise bll_exc.NoSuchObjectException()

            if action == 'get_link':
                return _handle_pwless_login(user, form, request.args.get("redirected", ""))

            elif action == 'password_login':
                account = svc.verify_password_login(user, form.password.data)
                login_user(account, remember=True)
                Messages.flash(Messages.ACCOUNT__WELCOME_BACK)
                return redirect(get_redirect_target(form=form, acc=account))

            else:
                # Unknown action
                raise bll_exc.ArgumentException("Unknown login action")

        except bll_exc.NoSuchObjectException:
            form.user.errors.append('Account not recognised. If you entered an email address, try your username instead.')
        except bll_exc.IllegalStatusException as e:
            msg = str(e) if e.args else ""
            if msg == 'incomplete_verification':
                handle_incomplete_verification()
                return redirect(url_for('doaj.home'))
            elif msg == 'incorrect_password':
                forgot_url = url_for(".forgot")
                form.password.errors.append(
                    f'The password you entered is incorrect. Try again or <a href="{forgot_url}">reset your password</a>.'
                )
            else:
                # Generic illegal status
                Messages.flash(Messages.ACCOUNT__STATUS_LOGIN_FAILED)
        except bll_exc.ArgumentException:
            Messages.flash(Messages.ACCOUNT__REQUEST_PROBLEM)

    return handle_login_template_rendering(form)

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
            return render_template(templates.FORGOT_PASSWORD)

        if not account.data.get('email'):
            util.flash_with_url('Error - your account does not have an associated email address.' + CONTACT_INSTR,
                                'error')
            return render_template(templates.FORGOT_PASSWORD)

        # if we get to here, we have a user account to reset
        reset_token = uuid.uuid4().hex
        account.set_reset_token(reset_token, app.config.get("PASSWORD_RESET_TIMEOUT", 86400))
        account.save()

        events_svc = DOAJ.eventsService()
        events_svc.trigger(Event(constants.EVENT_ACCOUNT_PASSWORD_RESET, account.id, context={"account": account.data}))
        Messages.flash(Messages.ACCOUNT__RESET_EMAIL_SENT)

        if app.config.get('DEBUG', False):
            util.flash_with_url('Debug mode - url for reset is <a href={0}>{0}</a>'.format(
                url_for('account.reset', reset_token=account.reset_token)))

    return render_template(templates.FORGOT_PASSWORD)


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
            Messages.flash(Messages.ACCOUNT__PASSWORDS_NOT_MATCH)
            return render_template(templates.RESET_PASSWORD, account=account, form=form)

        # update the user's account
        account.set_password(pw)
        account.remove_reset_token()
        account.save()
        Messages.flash(Messages.ACCOUNT__PASSWORD_SET_AND_LOGGED_IN)

        # log the user in
        login_user(account, remember=True)
        return redirect(url_for('doaj.home'))

    return render_template(templates.RESET_PASSWORD, account=account, form=form)


@blueprint.route('/logout')
@ssl_required
def logout():
    logout_user()
    Messages.flash(Messages.ACCOUNT__LOGGED_OUT)
    return redirect('/')


class RegisterForm(RedirectForm):
    identifier = StringField('ID', [ReservedUsernames(), IdAvailable()])
    name = StringField('Name', [validators.Optional(), validators.Length(min=3, max=64)])
    sender_email = StringField('Email address', [
        validators.DataRequired(),
        validators.Length(min=3, max=254),
        validators.Email(message='Must be a valid email address'),
        EmailAvailable(message="That email address is already in use. Please <a href='/account/forgot'>reset your password</a>. If you still cannot login, <a href='/contact'>contact us</a>.")
    ])
    roles = StringField('Roles')
    # These are honeypot (bot-trap) fields
    email = StringField('email')
    hptimer = DecimalField('hptimer', [validators.Optional()])

    def is_bot(self):
        """
        Checks honeypot fields and determines whether the form was submitted by a bot
        :return: True, if bot suspected; False, if human
        """
        return self.email.data != "" or self.hptimer.data is None or self.hptimer.data < app.config.get("HONEYPOT_TIMER_THRESHOLD", 5000)

@blueprint.route('/register', methods=['GET', 'POST'])
@ssl_required
@write_required()
def register(template=templates.REGISTER):
    # ~~-> Honeypot:Feature ~~
    # 3rd-party registration only for those with create_user role, only allow public registration when configured
    if current_user.is_authenticated and not current_user.has_role("create_user") \
            or current_user.is_anonymous and app.config.get('PUBLIC_REGISTER', False) is False:
        abort(401)      # todo: we may need a template to explain this since it's linked from the application form

    form = RegisterForm(request.form, csrf_enabled=False, roles='api,publisher', identifier=Account.new_short_uuid())

    if request.method == 'POST':

        if not current_user.is_authenticated and form.is_bot():
            flash(Messages.ARE_YOU_A_HUMAN, "error")
            return render_template(template, form=form)

        if form.validate():
            account = Account.make_account(email=form.sender_email.data, username=form.identifier.data, name=form.name.data,
                                           roles=[r.strip() for r in form.roles.data.split(',')])
            account.save()

            event_svc = DOAJ.eventsService()
            event_svc.trigger(Event(constants.EVENT_ACCOUNT_CREATED, account.id, context={"account" : account.data}))
            # send_account_created_email(account)

            if app.config.get('DEBUG', False):
                util.flash_with_url('Debug mode - url for verify is <a href={0}>{0}</a>'.format(url_for('account.reset', reset_token=account.reset_token)))

            if current_user.is_authenticated:
                util.flash_with_url('Account created for {0}. View Account: <a href={1}>{1}</a>'.format(account.email, url_for('.username', username=account.id)))
                return redirect(url_for('.index'))
            else:
                tpl = Messages.ACCOUNT__VERIFY_EMAIL_TO_SET_PASSWORD
                Messages.flash((tpl[0].format(email=form.sender_email.data), tpl[1]))

            # We must redirect home because the user now needs to verify their email address.
            return redirect(url_for('doaj.home'))
        else:
            Messages.flash(Messages.ACCOUNT__PLEASE_CORRECT_ERRORS)

    return render_template(template, form=form)

@blueprint.route('/create/', methods=['GET', 'POST'])
@write_required()
def create():
    return register(template=templates.CREATE_USER)