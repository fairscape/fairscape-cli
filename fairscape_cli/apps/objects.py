import typer
from pathlib import Path

app = typer.Typer()


@app.command("dataset")
def add_dataset(crateid: str = typer.Option(...),
                id: str = typer.Option(...),
                name: str = typer.Option(...),
                source: Path = typer.Option(...)):
    pass


@app.command("software")
def add_software(crateid: str = typer.Option(...),
                 id: str = typer.Option(...),
                 name: str = typer.Option(...),
                 source: str = typer.Option(...)):
    pass


@app.command("computation")
def add_computation(crateid: str = typer.Option(...),
                    id: str = typer.Option(...),
                    name: str = typer.Option(...),
                    usedSoftware: str = typer.Option(...),
                    usedDataset: str = typer.Option(...),
                    generated: str = typer.Option(...)):
    pass


if __name__ == "__main__":
    app()
