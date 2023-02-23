import typer
import fairscape

app = typer.Typer()

# enable command fairscape
app.add_typer(fairscape.app, name="fairscape")

if __name__ == "__main__":
    app()
