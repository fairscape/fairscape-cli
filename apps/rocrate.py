import typer
from pathlib import Path
import apps.objects

app = typer.Typer()
# subcommand
app.add_typer(apps.objects.app, name="add")


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


@app.command()
def delete(
    path: str,
    force: bool = typer.Option(..., prompt="Confirm to delete RO crate")
):
    if force:
        print(f"deleting ro crate: {path}")
    else:
        print("cancelling deletion")


if __name__ == "__main__":
    app()