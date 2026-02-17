from typer import Typer, Argument, Option
import typer
import time
from loguru import logger

from zelador.core.context import ContextService
from zelador.core.tools.docker import aplicar_stack, get_services_status
from zelador.core.tools.discord import DiscordReporter
from zelador.core.tools.discord_logger import DiscordLogCapture
from zelador.core.logging_config import setup_logging, cleanup_logging

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
    force: bool = Option(
        False,
        "--force",
        "-f",
        help="Força remoção da stack antes do deploy"
    ),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Mostra logs no console durante a execução"
    ),
    title: str = Option(
        None,
        "--title",
        help="Título customizado para o relatório"
    ),
    commit: str = Option(
        None,
        "--commit",
        help="Hash do commit para gerar link do GitHub"
    ),
    repo: str = Option(
        None,
        "--repo",
        help="URL do repositório GitHub (ex: owner/repo ou https://github.com/owner/repo)"
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
    discord = DiscordReporter()
    log_capture = DiscordLogCapture()
    sucesso = False
    erro_msg = None
    ctx = None

    # Configurar todos os handlers de logging
    handler_ids = setup_logging(app_name, verbose=verbose)

    # Iniciar captura de logs para Discord
    log_capture.start()

    try:
        ctx = ContextService(app_name=app_name, app_type=app_type)
        with ctx:
            sucesso = aplicar_stack(ctx, force=force)
    except Exception as e:
        erro_msg = str(e)
        logger.error(f"Erro durante deploy: {e}")
        sucesso = False

    # Se deploy foi bem-sucedido, aguardar 15s e enviar status dos serviços
    if sucesso and ctx:
        logger.info("Aguardando 15 segundos para verificar status dos serviços...")
        time.sleep(15)

        try:
            with ContextService(app_name=app_name, app_type=app_type) as ctx:
                services = get_services_status(ctx)
                if services:
                    logger.info(f"Serviços encontrados: {len(services)}")
                    discord.send_services_status(ctx.stack_name, services)
        except Exception as e:
            logger.error(f"Erro ao verificar status dos serviços: {e}")

    # Parar captura de logs (DEPOIS de tudo)
    log_capture.stop()

    # Obter todos os logs capturados
    logs_text = log_capture.get_all_logs()

    # Enviar relatório para Discord
    discord.send_report(
        success=sucesso,
        app_name=app_name,
        app_type=app_type,
        message=erro_msg,
        title=title,
        commit=commit,
        repo=repo,
        logs=logs_text
    )

    # Limpar handlers ao final
    cleanup_logging(handler_ids)

    if not sucesso:
        raise typer.Exit(code=1)



if __name__ == "__main__":
    app()



