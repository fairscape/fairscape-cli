import typer
import fairscape_cli.apps.validator as validator
import fairscape_cli.apps.rocrate as rocrate
import fairscape_cli.apps.list as list_objects
import fairscape_cli.apps.describe as describe


app = typer.Typer()
# subcommands
app.add_typer(rocrate.app, name="rocrate")
app.add_typer(validator.app, name="validate")
app.add_typer(list_objects.app, name="list")
app.add_typer(describe.app, name="describe")


@app.command("describe-id")
def describe_id(id: str = typer.Option("", help="Describe identifier metadata from id e.g. ark:5982/UVA/b2ai")):
    pass


@app.command("describe-name")
def describe_id(name: str = typer.Option("", help="Describe identifier metadata from name e.g. b2ai computation")):
    pass


if __name__ == "__main__":
    app()
