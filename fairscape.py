import typer
import validator
import rocrate

app = typer.Typer()

app.add_typer(rocrate.app, name="rocrate")
app.add_typer(validator.app, name="validate")

if __name__ == "__main__":
    app()