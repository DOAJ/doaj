import argparse

import requests
from portality.lib.paths import get_project_root


def download_file(url, local_path, chunk_size=8192, show_progress=True):
    cur_size = 0
    with requests.get(url, stream=True) as r:
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                cur_size += len(chunk) / 1024 / 1024
                if show_progress:
                    print(f'download: {cur_size:.2f}MB', end='\r')
                if chunk:
                    f.write(chunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', default='5.11.6', help='swagger-ui version')

    args = parser.parse_args()

    version = args.version
    dest_path = get_project_root() / f'portality/static/vendor'
    if not dest_path.is_dir():
        raise ValueError(f'dest path not found: {dest_path}')

    dest_path = dest_path / f'swagger-ui-{version}'
    dest_path.mkdir(parents=True, exist_ok=True)

    download_file(f"https://unpkg.com/swagger-ui-dist@{version}/swagger-ui.css",
                  dest_path / "swagger-ui.css")
    download_file(f"https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-bundle.js",
                  dest_path / "swagger-ui-bundle.js")

    try:
        download_file(f"https://raw.githubusercontent.com/swagger-api/swagger-ui/v{version}/docs/usage/installation.md",
                      dest_path / "installation.md")
    except Exception as e:
        print(f'failed to doc from github')

    print(f'downloaded to {dest_path.as_posix()}')


if __name__ == '__main__':
    main()
