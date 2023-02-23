import typer
import apps.validator
import apps.rocrate

app = typer.Typer()
# subcommands
app.add_typer(apps.rocrate.app, name="rocrate")
app.add_typer(apps.validator.app, name="validate")

if __name__ == "__main__":
    app()