import typer

app = typer.Typer()


@app.command("ROcrate")
def list_rocrate(id: str = typer.Option("", help="rocrate id"),
                 name: str = typer.Option("", help="rocrate name")):
    pass

@app.command("id")
def describe_id(
    id: str = typer.Argument("", help="Describe identifier metadata from id e.g. ark:5982/UVA/b2ai")
):
    pass


@app.command("name")
def describe_name(
    name: str = typer.Argument("", help="Describe identifier metadata from name e.g. b2ai computation")
):
    pass
