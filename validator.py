import typer
from pathlib import Path


app = typer.Typer()


@app.command("json")
def validate_json(path: Path):
    pass


@app.command("dataset")
def validate_dataset(path: Path):
    pass


@app.command("software")
def validate_software(path: Path):
    pass


@app.command("computation")
def validate_computation(path: Path):
    pass


if __name__ == "__main__":
    app()