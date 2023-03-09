from pathlib import Path
import typer
import json
from urllib.parse import urlparse
from urllib.request import urlopen
import hashlib
from os.path import basename
import sys


def is_path_valid(path: Path):
    if path.is_file():
        # content = path.read_text();
        # print(f"File content: {content}")
        file_extensions = [".json", ".jsonld"]
        # abort if correct file format is not submitted
        if path.suffix not in file_extensions:
            typer.secho(f"Only {file_extensions} formats are allowed", fg=typer.colors.BRIGHT_RED)
            return False 
        else:
            return True
    elif path.is_dir():
        typer.secho("Expecting a file but got a directory", fg=typer.colors.BRIGHT_RED)
        return False
    elif not path.exists():
        typer.secho(f"Unable to find document at: \"{path}\"", fg=typer.colors.BRIGHT_RED)
        return False


def compute_sha256(file_name):
    return hashlib.sha256(open(file_name, 'rb').read()).hexdigest()

# Reference: https://gist.github.com/lboulard/efa1f8b0a0c62dce3f0e7fd832d1257f
def get_sha256_remote(url):

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
            #url_wihtout_blob = url.replace("blob/", "")
            #url_raw_content = url_wihtout_blob.replace("github", "raw.githubusercontent")
            #f = urlopen(url_raw_content)
            #myfile = f.read()
            #print(myfile)
            print("# {}\n{}:\n{} bytes read".format(url, filename, size))
            print("sha256:%s" % sha256.hexdigest().lower())
        else:
            print(
                "ERROR: %s returned %d (%s)" % (url, response.status, response.reason),
                file=sys.stderr,
            )
