from docker import  DockerClient
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

from loguru import Logger

REGISTRY = os.environ.get("REGISTRY", 'lapig')


from loguru import logger
import docker


class ContextService:

    def __init__(
            self,
            app_name:str,
            app_type:str,
            tag: str
    ):
        logger.add(f'/service/logs/{app_name}.log',level='WARNING')
        self.logger: Logger = logger
        self.client: DockerClient = docker.DockerClient(base_url='unix://var/run/docker.sock')
        self.app_name = app_name
        self.app_type = app_type
        self.tag = tag
        self.stack_name = f"{app_type}_{app_name}"
        self.registry = REGISTRY
        self.path: Path = Path(f'/servecis/{self.app_name}')
        self._compose_sufix: str = '.compose.yml'

        self.image = f'{REGISTRY}/{self.stack_name}'

    def __enter__(self):
        if not self.path.is_dir():
            raise Exception(f'A pasta {self.app_name} não existe')

        if not (self.path / f'{self.app_type}{self._compose_sufix}').is_file():
            raise Exception(f'O arquivo compose não esta definido para tipo {self.app_type} para o projeto {self.app_name}')
        self.compose_file = self.path / f'{self.app_type}{self._compose_sufix}'

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if exc_type is not None:
            self.logger.error(f"Exceção capturada: {exc_type.__name__}")
            self.logger.error(f"Mensagem: {exc_val}")

