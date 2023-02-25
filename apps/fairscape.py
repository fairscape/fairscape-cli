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

if __name__ == "__main__":
    app()