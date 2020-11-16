# GitHub Action Artifact Downloader

GitHub does currently not provide an easy way to download an artifact from the
lastest successful GitHub Action build. This tool is meant to fill that gap.

## Requirements

Python 3.4+, no other dependencies


## Installation

Simply clone this repository and call the `github-artifact-download.py`


## Usage Guide

GitHub currently restricts download of artifacts to authenticated users. That
means that you need to create a [Personal Access Token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) to use this tool. The
token can either be supplied via an environment variable `GITHUB_TOKEN`, or
using the `--token` argument. For public repositories, only the "public_repo"
scope is required for this access token.

Only a single asset can be downloaded in one invokation of the tool.  There are
two modes of operation:
1. Find the latest artifact by name in all artifacts of the repository,
2. Find the latest successful run of a particular workflow and download a named
   artifact from that run.

After an artifact has been downloaded, it's full path on the local filesystem
is printed to stdout. This is designed to help in additional (shell) scripts
that further process the downloaded file.

To prevent re-downloading the same file again, you can specify a `--cache-file`
filepath to which the asset id of the last downloaded file will be written. If
the found asset matches the id in that file, it is skipped and the skript
exists without outputting the filename.

## Usage Examples

Note: in the following examples, `owner/repo` is a placeholder for your target
repositories owner and name. So to download artifacts from this repository for
example, you would use `mawe42/github-artifact-download` (don't do this, there
are not Actions set up here :-).

All examples below assume that your GitHub token is set in the environment:
```
export GITHUB_TOKEN=a345fd8e93...
```

**Download latest artifact called "stuff" to a local file called stuff.zip**
```
github-artifact-download.py owner/repo --artifact stuff
```

**Download latest artifact called "stuff" into a file called artifact.zip**
```
github-artifact-download.py owner/repo --artifact stuff --filename artifact.zip
```

**Download latest artifact called "stuff" and make sure we don't download it again**
```
github-artifact-download.py owner/repo --artifact stuff --cache-file id.txt
```

**Download the artifact "stuff" from the last successful build of workflow "My Test Build"**
```
github-artifact-download.py owner/repo --artifact stuff --workflow "My Test Build"
```

**Download the artifact "stuff" from the last successful build of workflow "My Test Build", but only for builds on branch "test-build"**
```
github-artifact-download.py owner/repo --artifact stuff --workflow "My Test Build" --branch test-build
```

**Get help**
```
github-artifact-download.py --help
```
