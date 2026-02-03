from typer import Typer, Argument, Option
import typer

from core.context import ContextService
from core.tools.docker import aplicar_stack

app = Typer(
    name="zelador",
    help="Ferramenta CLI para gerenciar e fazer deploy de aplicações em Docker Stack",
    rich_markup_mode="markdown"
)

@app.command()
def process(
    app_name: str = Argument(
        ...,
        help="Nome da aplicação (ex: minha-app, api)"
    ),
    app_type: str = Argument(
        ...,
        help="Tipo da aplicação (ex: web, api, worker) - define qual arquivo compose usar"
    ),
    tag: str = Option(
        "latest",
        "--tag",
        "-t",
        help="Tag da imagem Docker a ser utilizada no deploy"
    )
):
    """
    Faz deploy/atualização de uma aplicação Docker Stack.

    Processa o deploy de uma aplicação fazendo:
    - Atualização de imagens Docker
    - Remoção de imagens antigas
    - Deploy da stack usando docker-compose
    - Logging de todas as operações

    Exemplos:

    ```
    # Deploy com tag latest (padrão)
    python main.py process minha-app web

    # Deploy com tag específica
    python main.py process minha-app api --tag v1.2.3

    # Deploy usando forma curta
    python main.py process minha-app worker -t production
    ```
    """
    with ContextService(app_name=app_name, app_type=app_type, tag=tag) as ctx:
        sucesso = aplicar_stack(ctx)
        if not sucesso:
            raise typer.Exit(code=1)



if __name__ == "__main__":
    app()



