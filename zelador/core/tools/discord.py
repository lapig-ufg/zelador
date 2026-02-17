import os
import requests
from datetime import datetime
import pytz
import tempfile
from loguru import logger


class DiscordReporter:
    """Envia relatórios de deploy para Discord via webhook"""

    def __init__(self):
        discord_key = os.getenv("DISCORD_KEY")
        self.image_success = os.getenv("IMAGE_SUCCESS")
        self.image_error = os.getenv("IMAGE_ERROR")

        if not discord_key:
            self.webhook_url = None
            self.enabled = False
        else:
            # Se for apenas ID/TOKEN, construir URL completa
            if discord_key.startswith("http://") or discord_key.startswith("https://"):
                self.webhook_url = discord_key
            else:
                # Formato: ID/TOKEN
                self.webhook_url = f"https://discordapp.com/api/webhooks/{discord_key}"
            self.enabled = True

    def _build_embed(self, success: bool, app_name: str, app_type: str, message: str = None,
                     title: str = None, commit: str = None, repo: str = None):
        """Constrói um embed Discord para o relatório"""
        tz_sp = pytz.timezone('America/Sao_Paulo')
        timestamp = datetime.now(tz_sp).strftime("%d/%m/%Y %H:%M:%S")

        if success:
            color = 0x00ff00  # Verde
            status = "✅ SUCESSO"
            image = self.image_success
        else:
            color = 0xff0000  # Vermelho
            status = "❌ ERRO"
            image = self.image_error

        # Título customizado ou padrão
        embed_title = title if title else f"Deploy {app_name}"

        embed = {
            "title": f"{status} - {embed_title}",
            "color": color,
            "author": {
                "name": "Zelador Deploy",
                "icon_url": image
            },
            "fields": [
                {
                    "name": "Aplicação",
                    "value": app_name,
                    "inline": True
                },
                {
                    "name": "Tipo",
                    "value": app_type,
                    "inline": True
                },
                {
                    "name": "Data/Hora",
                    "value": timestamp,
                    "inline": False
                }
            ],
            "thumbnail": {
                "url": image
            },
            "image": {
                "url": image
            },
            "footer": {
                "text": f"Zelador • {timestamp}"
            }
        }

        # Adicionar links (commit e repositório)
        links = []
        if repo:
            # Normalizar o repo
            repo_url = repo.replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            if not repo_url.startswith("http"):
                repo_full_url = f"https://github.com/{repo_url}"
            else:
                repo_full_url = repo
            links.append(f"[Repositório]({repo_full_url})")

        if commit and repo:
            # Normalizar o repo (remover https://github.com/ se presente)
            repo_url = repo.replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            commit_url = f"https://github.com/{repo_url}/commit/{commit}"
            commit_short = commit[:7]
            links.append(f"[Commit {commit_short}]({commit_url})")

        # Adicionar campo de links se houver
        if links:
            embed["fields"].append({
                "name": "Links",
                "value": " • ".join(links),
                "inline": False
            })

        if message:
            embed["fields"].append({
                "name": "Detalhes",
                "value": message,
                "inline": False
            })

        return embed

    def send_report(self, success: bool, app_name: str, app_type: str, message: str = None,
                    title: str = None, commit: str = None, repo: str = None, logs: str = None):
        """Envia relatório para Discord com arquivo de logs opcional"""
        if not self.enabled:
            return False

        try:
            embed = self._build_embed(success, app_name, app_type, message=message, title=title, commit=commit, repo=repo)
            embeds = [embed]

            # Preparar dados multipart
            data = {
                "payload_json": __import__("json").dumps({"embeds": embeds})
            }

            # Se houver logs, adicionar arquivo .txt
            files = {}
            if logs:
                # Criar arquivo temporário com os logs
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(logs)
                    temp_file = f.name

                # Abrir e enviar o arquivo
                files['file'] = ('logs.txt', open(temp_file, 'rb'), 'text/plain')

            # Enviar com multipart/form-data se houver arquivo
            if files:
                response = requests.post(
                    self.webhook_url,
                    data=data,
                    files=files,
                    timeout=10
                )
                # Fechar arquivo
                files['file'][1].close()
                os.unlink(temp_file)
            else:
                # Enviar apenas embed se não houver logs
                response = requests.post(
                    self.webhook_url,
                    json={"embeds": embeds},
                    timeout=10
                )

            return response.status_code == 204

        except Exception as e:
            logger.error(f"Erro ao enviar relatório para Discord: {e}")
            return False

    def send_services_status(self, stack_name: str, services: list):
        """Envia status dos serviços em formato de tabela"""
        if not self.enabled or not services:
            return False

        try:
            # Construir tabela de serviços
            table = "```\n"
            table += f"{'Serviço':<30} {'Status':<15}\n"
            table += "-" * 45 + "\n"

            for service in services:
                service_name = service['name'].split('_')[-1][:28]
                status = "🟢 Online" if service['running'] else "🔴 Offline"
                table += f"{service_name:<30} {status:<15}\n"

            table += "```"

            tz_sp = pytz.timezone('America/Sao_Paulo')
            timestamp_sp = datetime.now(tz_sp).isoformat()

            embed = {
                "title": f"📊 Status da Stack: {stack_name}",
                "color": 0x0099ff,
                "description": table,
                "timestamp": timestamp_sp
            }

            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 204

        except Exception as e:
            logger.error(f"Erro ao enviar status dos serviços para Discord: {e}")
            return False
