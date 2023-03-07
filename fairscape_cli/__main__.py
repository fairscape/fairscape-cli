import typer
import fairscape_cli.apps.fairscape

fairscape_cli_app = typer.Typer()

# enable command apps
fairscape_cli_app.add_typer(fairscape_cli.apps.fairscape.app, name="fairscape")

if __name__ == "__main__":
    fairscape_cli_app()
