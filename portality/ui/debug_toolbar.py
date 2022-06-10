from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar.panels import DebugPanel

from portality.lib import paths


class BranchNamePanel(DebugPanel):
    name = 'branch_name'
    has_content = True

    def get_branch_name(self):
        _git_head_file = paths.get_project_root().joinpath('.git/HEAD')
        if _git_head_file.is_file():
            return (_git_head_file.read_text()
                    .strip().replace('ref: refs/heads/', '')
                    .replace('ref: ', ''))
        return 'Unknown, git HEAD not found '

    def nav_title(self):
        return 'Branch name'

    def title(self):
        return 'Branch name'

    def nav_subtitle(self):
        return self.get_branch_name()

    def url(self):
        return ''

    def content(self):
        return f'<h1 style="font-size: 30px;">{self.get_branch_name()}</h1>'


class DoajDebugToolbar(DebugToolbarExtension):

    def _default_config(self, app):
        config = super()._default_config(app)
        config['DEBUG_TB_PANELS'] += (f'{BranchNamePanel.__module__}.{BranchNamePanel.__name__}',)
        return config
