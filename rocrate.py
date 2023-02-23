import typer
from pathlib import Path
import objects

app = typer.Typer()
app.add_typer(objects.app, name="add")


@app.command("create")
def create_crate(id: str = typer.Option(...),
                 name: str = typer.Option(...),
                 organization: str = typer.Option(...),
                 project: str = typer.Option(...),
                 path: Path = typer.Option(...)):
    pass




@app.command("dump-metadata")
def dump_metadata():
    pass


@app.command("hash")
def compute_hash(crateid: str = typer.Option(...)):
    pass


@app.command("package")
def package_rocrate(output_path: Path = typer.Option(...)):
    pass


if __name__ == "__main__":
    app()