import typer

rocrate_app = typer.Typer()

@rocrate_app.command()
def create(name: str, path: str):
    print(f"creating ro crate {name} at path {path}")


@rocrate_app.command()
def describe(path: str):
    pass


@rocrate_app.command()
def zip(path: str):
    pass


@rocrate_app.command()
def hash(path: str):
    pass


@rocrate_app.command()
def validate(path: str):
    pass


@rocrate_app.command()
def delete(
    path: str, 
    force: bool = typer.Option(..., prompt="Confirm to delete RO crate")
):
    if force:
        print(f"deleting ro crate: {path}")
    else:
        print("cancelling deletion")


@rocrate_app.command()
def publish(path: str):
    pass


@rocrate_app.command()
def add_dataset():
    pass


@rocrate_app.command()
def add_software():
    pass


@rocrate_app.command()
def add_computation():
    pass

