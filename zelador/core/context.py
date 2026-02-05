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
            app_type:str,
            tag: str
    ):
        logger.add(f'/services/logs/{app_name}.log',level='WARNING')

        self.logger = logger
        self.client = docker.DockerClient(base_url=DOCKER_SOCKET)
        self.app_name:str = app_name
        self.app_type:str = app_type
        self.tag:str = tag
        self.stack_name:str = f"{app_type}_{app_name}"
        self.registry:str = REGISTRY
        self.path: Path = Path(f'/services/{self.app_name}')
        self._compose_sufix: str = '.compose.yml'

        self.image = f'{REGISTRY}/{self.app_name}'

    def __enter__(self):
        if not self.path.is_dir():
            raise Exception(f'A pasta {self.app_name} não existe')

        if not (self.path / f'{self.app_type}{self._compose_sufix}').is_file():
            raise Exception(f'O arquivo compose não esta definido para tipo {self.app_type} para o projeto {self.app_name}')
        self.compose_file = self.path / f'{self.app_type}{self._compose_sufix}'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if exc_type is not None:
            self.logger.error(f"Exceção capturada: {exc_type.__name__}")
            self.logger.error(f"Mensagem: {exc_val}")
        return False

