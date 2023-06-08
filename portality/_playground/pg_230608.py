import os

import requests


def main():
    REPO = "https://api.github.com/repos/DOAJ/doajPM/"
    PROJECTS = REPO + "projects"
    PROJECT_NAME = "DOAJ Kanban"
    DEFAULT_COLUMNS = ["Review", "In progress", "To Do"]
    HEADERS = {
        "Accept": "application/vnd.github+json",
        'Authorization': f'Bearer {os.environ["GITHUB_API_KEY"]}',
    }
    resp = requests.get(PROJECTS, headers=HEADERS)
    print(resp)
    for p in resp.json():
        print(p)


if __name__ == '__main__':
    main()
