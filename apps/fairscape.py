import typer
import apps.validator
import apps.rocrate
import apps.list
import apps.describe


app = typer.Typer()
# subcommands
app.add_typer(apps.rocrate.app, name="rocrate")
app.add_typer(apps.validator.app, name="validate")
app.add_typer(apps.list.app, name="list")
app.add_typer(apps.describe.app, name="describe")


@app.command("describe-id")
def describe_id(id: str = typer.Option("", help="Describe identifier metadata from id e.g. ark:5982/UVA/b2ai")):
    pass


@app.command("describe-name")
def describe_id(name: str = typer.Option("", help="Describe identifier metadata from name e.g. b2ai computation")):
    pass


if __name__ == "__main__":
    app()