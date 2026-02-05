from zelador.core.context import ContextService
import subprocess
import time
from docker.errors import ImageNotFound

def get_services_status(ctx: ContextService) -> list:
    """Retorna lista de serviços com seu status (running ou não)"""
    try:
        stack_name = ctx.stack_name
        client = ctx.client
        servicos = client.services.list(filters={'label': f'com.docker.stack.namespace={stack_name}'})

        status_list = []
        for servico in servicos:
            name = servico.name
            # Contar tasks running vs total
            tasks = client.tasks.list(filters={'service': name})
            running = sum(1 for task in tasks if task.attrs['Status']['State'] == 'running')
            total = len(tasks)

            status_list.append({
                'name': name,
                'running': running > 0,
                'tasks': f"{running}/{total}"
            })

        return status_list
    except Exception:
        return []

def aplicar_stack(ctx: ContextService) -> bool:
    """Aplica/atualiza stack (funciona para tudo: primeira vez, updates, mudanças no compose)."""
    logger = ctx.logger
    stack_name = ctx.stack_name
    client = ctx.client
    compose_file = ctx.compose_file
    new_image = ctx.image
    new_tag = ctx.tag
    try:
        # Verificar se a stack existe
        servicos = client.services.list(filters={'label': f'com.docker.stack.namespace={stack_name}'})

        if servicos:
            # Stack existe - atualizar imagens e remover para redeployar com mudanças
            logger.info(f"Atualizando imagens da stack '{stack_name}'...")
            for servico in servicos:
                imagem = servico.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split('@')[0]
                try:
                    client.images.remove(imagem, force=True)
                except ImageNotFound:
                    pass

                logger.info(f"Pulling: {imagem}")
                client.images.pull(new_image, tag=new_tag)

            # Remover stack antiga para garantir que o compose atualizado seja aplicado
            logger.info(f"Removendo stack antiga: {stack_name}...")
            subprocess.run(
                ["docker", "stack", "rm", stack_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            # Aguardar remoção completa
            time.sleep(15)
        else:
            # Stack não existe - primeira vez
            logger.info(f"Stack '{stack_name}' não existe. Criando nova stack...")
        # Aplicar stack nova com compose atualizado
        logger.info(f"Aplicando stack: {stack_name}")
        resultado = subprocess.run(
            ["docker", "stack", "deploy", "-c", str(compose_file), stack_name],
            capture_output=True,
            text=True
        )

        if resultado.returncode == 0:
            logger.success(f"✓ Stack '{stack_name}' aplicada {resultado.stdout}")
            return True

        logger.error(f"Erro: {resultado.stderr}")
        return False

    except Exception as e:
        logger.error(f"Erro: {e}")
        return False