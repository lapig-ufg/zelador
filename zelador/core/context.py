import os
from pathlib import Path

from dotenv import load_dotenv
import docker
from loguru import logger

load_dotenv()

REGISTRY = os.environ.get("REGISTRY", 'lapig')
DOCKER_SOCKET=os.environ.get("DOCKER_SOCKET",'unix:///var/run/docker.sock')

class ContextService:

    def __init__(
            self,
            app_name:str,
            app_type:str
    ):
        self.client = docker.DockerClient(base_url=DOCKER_SOCKET)
        self.app_name:str = app_name
        self.app_type:str = app_type
        self.stack_name:str = f"{app_type}_{app_name}"
        self.registry:str = REGISTRY
        self.path: Path = Path(f'/services/{self.app_name}')
        self._compose_sufix: str = '.compose.yml'

    def __enter__(self):
        if not self.path.is_dir():
            erro = f'A pasta {self.app_name} não existe'
            logger.error(erro)
            raise Exception(erro)

        if not (self.path / f'{self.app_type}{self._compose_sufix}').is_file():
            erro = f'O arquivo compose não esta definido para tipo {self.app_type} para o projeto {self.app_name}'
            logger.error(erro)
            raise Exception(erro)
        self.compose_file = self.path / f'{self.app_type}{self._compose_sufix}'
        logger.info(f"Compose file carregado: {self.compose_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if exc_type is not None:
            logger.error(f"Exceção capturada: {exc_type.__name__}")
            logger.error(f"Mensagem: {exc_val}")
        return False

