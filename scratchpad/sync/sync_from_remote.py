import esprit
from portality.core import app

remote = esprit.raw.Connection("http://ooz.cottagelabs.com:9200", "doaj")
local = esprit.raw.Connection("http://localhost:9200", "doaj")

esprit.tasks.copy(remote, "journal", local, "journal")
esprit.tasks.copy(remote, "account", local, "account")
esprit.tasks.copy(remote, "article", local, "article")
esprit.tasks.copy(remote, "suggestion", local, "suggestion")
esprit.tasks.copy(remote, "upload", local, "upload")
esprit.tasks.copy(remote, "cache", local, "cache")
esprit.tasks.copy(remote, "lcc", local, "lcc")
esprit.tasks.copy(remote, "editor_group", local, "editor_group")
esprit.tasks.copy(remote, "news", local, "news")
esprit.tasks.copy(remote, "lock", local, "lock")
esprit.tasks.copy(remote, "background_job", local, "background_job")

