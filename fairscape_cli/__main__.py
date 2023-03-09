import typer
import fairscape_cli.apps.fairscape

fairscape_cli_app = typer.Typer()

if __name__ == "__main__":
    fairscape_cli.apps.fairscape.app()
