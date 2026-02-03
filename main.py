import typer

from core.context import ContextService
from core.tools.docker import aplicar_stack

app = typer.Typer()

@app.command()
def process(app_name: str, app_type: str, tag:str = 'latest'):
    with ContextService(app_name=app_name, app_type=app_type, tag=tag) as ctx:
        aplicar_stack(ctx)


