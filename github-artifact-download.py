#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = 'https://api.github.com'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download the latest GitHub Actions artifact from a GitHub repository')

    parser.add_argument('repository', help='The GitHub owner/repo path, e.g. mawe42/github-artifact-download')
    parser.add_argument('--token', help='The GitHub personal access token. Can also be '
                        'supplied via GITHUB_TOKEN env variable')

    parser.add_argument('--artifact', help='The name of the artifact to download, e.g. api_docs')
    parser.add_argument('--filename', help='Local filename for the downloaded artifact, '
                        'leave empty to use <artifact name>.zip')

    parser.add_argument('--workflow', help='Workflow name to download the artifact from')
    parser.add_argument('--branch', help='Branch name to download the artifact from, only checked '
                        'if --workflow is also specified')

    parser.add_argument('--cache-file', help='Path to filename in which to store the latest downloaded '
                        'artifact id to prevent download the same file again. Caution: This file will '
                        'get overwritten after a successful download!')

    parser.add_argument('--traceback', action='store_true', help='Show Python traceback on error')
    parser.add_argument('-v', '--verbose', action='store_true', help='Output some debugging information')

    return parser.parse_args()


def main(args):
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('Please specify a GitHub personal access token')

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token ' + token,
    }

    cache_file = Path(args.cache_file) if args.cache_file else None

    if args.workflow:
        run = find_latest_successful_workflow_run(args.repository, args.workflow, args.branch, headers=headers)
        if not run:
            raise RuntimeError('No successful workflow run found')

        if args.verbose:
            print('Successful run found: %s on %s, %s started on: %s' % (
                run['event'], run['head_branch'], run['name'], run['created_at']))

        artifact = find_workflow_run_artifact(args.repository, run['id'], args.artifact, headers=headers)
    else:
        artifact = find_latest_repo_artifact(args.repository, args.artifact, headers=headers)

    if not artifact:
        raise RuntimeError('Artifact not found!')

    if args.verbose:
        print('Artifact found: %s (%s bytes), created on: %s' % (
            artifact['name'], artifact['size_in_bytes'], artifact['created_at']))

    if cache_file and cache_file.exists() and cache_file.read_text() == str(artifact['id']):
        if args.verbose:
            print('Artifact already downladed, exiting')
        return

    download_url = artifact['archive_download_url']
    if args.verbose:
        print('Downloading', download_url)

    filename = args.filename or (artifact.get('name', 'artifact') + '.zip')
    download_file(download_url, filename, headers=headers, verbose=args.verbose)

    if cache_file:
        cache_file.write_text(str(artifact['id']))

    if args.verbose:
        print('File downloaded to', filename)

    print(Path(filename).resolve())


def find_latest_repo_artifact(repo, name, headers=None):
    url = mkurl('repos', repo, 'actions', 'artifacts', params={'per_page': 50})
    for result in get_paged(url, headers):
        for artifact in result.get('artifacts', []):
            if name is None or artifact['name'] == name:
                return artifact


def find_latest_successful_workflow_run(repo, name, branch=None, headers=None):
    url = mkurl('repos', repo, 'actions', 'runs', params={'per_page': 50})
    for result in get_paged(url, headers):
        for run in result.get('workflow_runs', []):
            if (run['conclusion'] != 'success' or
                    (name and run['name'] != name) or
                    (branch and run['head_branch'] != branch)):
                continue
            return run


def find_workflow_run_artifact(repo, run_id, name, headers=None):
    url = mkurl('repos', repo, 'actions', 'runs', run_id, 'artifacts', params={'per_page': 50})
    for result in get_paged(url, headers):
        for artifact in result.get('artifacts', []):
            if name is None or artifact['name'] == name:
                return artifact


def download_file(url, filename, headers=None, verbose=False):
    with urlopen(Request(url, headers=headers)) as res, open(filename, 'wb') as out:
        while True:
            chunk = res.read(1024 * 8)
            if verbose:
                print('.', end='', sep='', flush=True)
            if not chunk:
                break
            out.write(chunk)
        if verbose:
            print('')


def get_paged(url, headers):
    while True:
        res = urlopen(Request(url, headers=headers))
        yield json.loads(res.read().decode())
        url = rel_next_link(res)
        if not url:
            break


def rel_next_link(response):
    links = response.getheader('link') or ''
    match = re.search(r'<([^>]+)>;\srel="next"', links)
    if match:
        return match.group(1)


def mkurl(*args, params=None):
    parts = [API_URL]
    parts.extend(args)
    url = '/'.join(str(p) for p in parts)
    if params:
        url += '?' + urlencode(params)
    return url


if __name__ == '__main__':
    args = parse_args()
    try:
        main(args)
    except Exception as e:
        if args.traceback:
            raise
        print('Error: %s' % e, file=sys.stderr)
        sys.exit(1)
