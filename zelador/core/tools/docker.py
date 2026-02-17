from zelador.core.context import ContextService
import subprocess
import time
from docker.errors import ImageNotFound
from loguru import logger

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
    except Exception as e:
        logger.error(f"Erro ao listar serviços: {e}")
        return []

def aplicar_stack(ctx: ContextService, force: bool = False) -> bool:
    """Aplica/atualiza stack (funciona para tudo: primeira vez, updates, mudanças no compose)."""
    stack_name = ctx.stack_name
    client = ctx.client
    compose_file = ctx.compose_file
    try:
        # Verificar se a stack existe
        servicos = client.services.list(filters={'label': f'com.docker.stack.namespace={stack_name}'})

        if servicos:
            # Stack existe - coletar imagens únicas
            logger.info(f"Atualizando imagens da stack '{stack_name}'...")
            imagens_unicas = set()
            for servico in servicos:
                imagem = servico.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split('@')[0]
                imagens_unicas.add(imagem)

            # Remover e fazer pull de cada imagem UMA VEZ
            for imagem_completa in imagens_unicas:
                try:
                    client.images.remove(imagem_completa, force=True)
                    logger.info(f"Imagem removida: {imagem_completa}")
                except ImageNotFound:
                    logger.info(f"Imagem não encontrada: {imagem_completa}")

                # Fazer pull da imagem nova
                if ':' in imagem_completa:
                    imagem, tag = imagem_completa.rsplit(':', 1)
                    logger.info(f"Pulling: {imagem}:{tag}")
                    client.images.pull(imagem, tag=tag)
                else:
                    logger.info(f"Pulling: {imagem_completa}")
                    client.images.pull(imagem_completa)

        # Remover stack apenas se --force foi ativado
        if force:
            logger.info(f"Removendo stack: {stack_name}...")
            resultado_rm = subprocess.run(
                ["docker", "stack", "rm", stack_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if resultado_rm.stdout:
                logger.info(f"Stack removida: {resultado_rm.stdout}")
            if resultado_rm.stderr:
                logger.warning(f"Aviso na remoção: {resultado_rm.stderr}")
            # Aguardar remoção completa
            time.sleep(15)

        # Aplicar stack nova com compose atualizado
        logger.info(f"Aplicando stack: {stack_name}")
        resultado = subprocess.run(
            ["docker", "stack", "deploy", "-c", str(compose_file), stack_name],
            capture_output=True,
            text=True
        )

        if resultado.returncode == 0:
            logger.success(f"✓ Stack '{stack_name}' aplicada com sucesso")
            if resultado.stdout:
                logger.info(f"Output: {resultado.stdout}")
            return True

        logger.error(f"Erro ao aplicar stack: {resultado.stderr}")
        if resultado.stdout:
            logger.info(f"Output: {resultado.stdout}")
        return False

    except Exception as e:
        logger.error(f"Erro: {e}")
        return False