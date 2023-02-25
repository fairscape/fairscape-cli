import typer

app = typer.Typer()


@app.command("ROcrate")
def list_rocrate(id: str = typer.Option("", help="rocrate id"),
                 name: str = typer.Option("", help="rocrate name")):
    pass
