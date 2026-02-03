from core.context import ContextService
import subprocess
from docker.errors import ImageNotFound

def aplicar_stack(ctx: ContextService) -> bool:
    """Aplica/atualiza stack (funciona para tudo: primeira vez, updates, mudanças no compose)."""
    logger = ctx.logger
    stack_name = ctx.stack_name
    client = ctx.client
    compose_file = ctx.compose_file
    new_image = ctx.image
    new_tag = ctx.tag
    try:
        # Atualizar imagens da stack
        logger.info(f"Atualizando imagens da stack '{stack_name}'...")
        servicos = client.services.list(filters={'label': f'com.docker.stack.namespace={stack_name}'})

        for servico in servicos:
            imagem = servico.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split('@')[0]
            try:
                client.images.remove(imagem, force=True)
            except ImageNotFound:
                pass

            logger.info(f"Pulling: {imagem}")
            client.images.pull(new_image, tag=new_tag)

        # Aplicar stack
        logger.info(f"Aplicando stack: {stack_name}")
        resultado = subprocess.run(
            ["docker", "stack", "deploy", "-c", str(compose_file), stack_name],
            capture_output=True,
            text=True
        )

        if resultado.returncode == 0:
            logger.success(f"✓ Stack '{stack_name}' aplicada")
            return True

        logger.error(f"Erro: {resultado.stderr}")
        return False

    except Exception as e:
        logger.error(f"Erro: {e}")
        return False