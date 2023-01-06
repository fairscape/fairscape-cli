import typer
import rocrate.cli as rocrate

app = typer.Typer()

# add ro crate as a subcommand
app.add_typer(
    rocrate.rocrate_app, 
    name="ro-crate", 
    help="create evidence graphs in RO crate"
)



if __name__ == "__main__":
    app()
