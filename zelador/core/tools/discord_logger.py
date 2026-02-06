import sys
from loguru import logger
from io import StringIO


class DiscordLogCapture:
    """Captura logs do loguru e armazena para enviar ao Discord"""

    def __init__(self):
        self.logs = []
        self.handler_id = None

    def start(self):
        """Inicia captura de logs"""
        self.logs = []
        # Remover handler anterior se existir
        if self.handler_id is not None:
            logger.remove(self.handler_id)

        # Adicionar novo handler que captura os logs
        self.handler_id = logger.add(self._capture_log, level="DEBUG")

    def stop(self):
        """Para captura de logs"""
        if self.handler_id is not None:
            logger.remove(self.handler_id)
            self.handler_id = None

    def _capture_log(self, message):
        """Callback que captura cada log"""
        # Extrair texto formatado da mensagem
        record = message.record
        level = record["level"].name
        time = record["time"].strftime("%H:%M:%S")
        text = message.rstrip()

        # Armazenar log formatado
        log_entry = f"[{time}] {level:<8} {text}"
        self.logs.append(log_entry)

    def get_logs(self, limit: int = 20) -> str:
        """Retorna os últimos N logs formatados"""
        if not self.logs:
            return "Sem logs disponíveis"

        # Pegar últimos N logs
        recent_logs = self.logs[-limit:]
        return "\n".join(recent_logs)

    def get_all_logs(self) -> str:
        """Retorna todos os logs"""
        if not self.logs:
            return "Sem logs disponíveis"

        return "\n".join(self.logs)
