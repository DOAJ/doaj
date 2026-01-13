from jinja2 import Template
from markupsafe import Markup

WARNING = """<p>This application has been rejected. We found a related older journal record. <strong>You may want to withdraw it.</strong><br />
            <a href="{{ url }}" target="_blank">{{ title }}</a>
        </p>"""

def render_copy(template_str, **context):
    return Markup(Template(template_str).render(**context))
