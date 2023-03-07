from pathlib import Path
import typer
import json
from urllib.parse import urlparse
from urllib.request import urlopen
import hashlib
from os.path import basename
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError


def valid_path(path: Path):
    message_failure = "Failed to validate JSON document "
    if not path.exists():
        typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
        typer.secho(f"Unable to find document at: \"{path}\"", fg=typer.colors.BRIGHT_RED)
        #raise typer.Exit(1)
    elif path.is_dir():
        typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
        typer.secho("Expecting a document but got a directory", fg=typer.colors.BRIGHT_RED)
        #raise typer.Exit(1)
    elif not path.is_file():
        typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
        typer.secho("Not a document", fg=typer.colors.BRIGHT_RED)
        #raise typer.Exit(1)
    else: # is a document
        # content = path.read_text();
        # print(f"File content: {content}")
        return True


def valid_url(url):
    req = Request(url)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            typer.secho(f"Failed to reach a server.", fg=typer.colors.BRIGHT_RED)
            typer.secho(f"Reason: {e.filename} {e.reason}", fg=typer.colors.BRIGHT_RED)
        elif hasattr(e, 'code'):
            typer.secho(f"The server couldn\'t fulfill the request.", fg=typer.colors.BRIGHT_RED)
            typer.secho(f"Error code: {e.code}", fg=typer.colors.BRIGHT_RED)
    else:
        return True

def valid_file_format(path: Path):
    message_failure = "Failed to validate JSON document "
    file_extensions = [".json", ".jsonld"]
    # abort if correct file format is not submitted
    if path.suffix not in file_extensions:
        typer.secho(f"{message_failure} {path}", fg=typer.colors.RED)
        typer.secho(f"Only {file_extensions} documment formats are allowed", fg=typer.colors.BRIGHT_RED)
        #raise typer.Exit(1)
    else:
        return True


def compute_sha256(file_name):
    return hashlib.sha256(open(file_name, 'rb').read()).hexdigest()


# Reference: https://gist.github.com/lboulard/efa1f8b0a0c62dce3f0e7fd832d1257f
def get_sha256_from_remote_document(url):
    with urlopen(url) as response:
        if False and url != response.geturl():
            print("# {} -> {}\n".format(url, response.geturl()))
        sha256 = hashlib.new("SHA256")
        if response.status == 200:
            size, n = 0, 16484
            buf = bytearray(n)
            while n != 0:
                n = response.readinto(buf)
                size += n
                if n > 0:
                    sha256.update(buf[:n])
            o = urlparse(url)
            if not basename(o.path):
                o = urlparse(response.geturl())
            filename = basename(o.path) or "index.html"
            #print("# {}\n{}:\n{} bytes read".format(url, filename, size))
            #print("sha256:%s" % sha256.hexdigest().lower())
            if len(sha256.hexdigest()) == 64 and size > 0:
                return True
            else:
                return False
        else:
            print(
                "ERROR: %s returned %d (%s)" % (url, response.status, response.reason),
                file=sys.stderr,
            )
            return False


def valid_remote_repo_prefix(content_url):
    remote_repo_uri_prefix = ["https://github.com"]
    if content_url.startswith(tuple(remote_repo_uri_prefix)):
        o = urlparse(content_url)
        if not (o.scheme and o.netloc):
            raise ValueError(f"Malformed contentUrl \"{content_url}\". ")
        return True
    else:
        return False


def url_has_content(content_url):

    github_prefix = "https://github.com"
    if content_url.startswith(github_prefix):
        url_wihtout_blob = content_url.replace("blob/", "")
        url_raw_content = url_wihtout_blob.replace("github", "raw.githubusercontent")
        if valid_url(url_raw_content):
            return get_sha256_from_remote_document(url_raw_content)
    else:
        raise ValueError(f"Only Github content is allowed \"{content_url}\".")