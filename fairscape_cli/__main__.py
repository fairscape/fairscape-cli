import typer
import fairscape_cli.apps.fairscape

app = typer.Typer()

# enable command apps
app.add_typer(fairscape_cli.apps.fairscape.app, name="fairscape")

if __name__ == "__main__":
    app()
