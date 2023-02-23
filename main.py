import typer
import apps.fairscape

app = typer.Typer()

# enable command apps
app.add_typer(apps.fairscape.app, name="fairscape")

if __name__ == "__main__":
    app()
