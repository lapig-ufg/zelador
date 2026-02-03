# Zelador

Ferramenta CLI para gerenciar e fazer deploy de aplicações em Docker Stack.

## Descrição

Zelador é uma ferramenta de linha de comando que automatiza o processo de atualizar e fazer deploy de serviços Docker Stack. Ela gerencia:

- Atualização de imagens Docker
- Remoção de imagens antigas
- Deploy/atualização de stacks Docker
- Logging e rastreamento de operações

## Requisitos

- Python 3.13+
- Docker (daemon rodando)
- Acesso ao socket Docker (`/var/run/docker.sock`)

## Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd zelador

# Instale as dependências usando uv
uv sync

# Ou usando pip
pip install -e .
```

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# Registry Docker (padrão: lapig)
REGISTRY=seu-registry
```

## Uso

### Comando Principal

```bash
python main.py process <app_name> <app_type> [--tag <tag>]
```

### Parâmetros

- `<app_name>` - Nome da aplicação (ex: minha-app, api)
- `<app_type>` - Tipo de aplicação (ex: web, api, worker) - define qual arquivo compose usar
- `--tag` - Tag da imagem Docker (padrão: latest)

### Exemplos

```bash
# Deploy com tag latest (padrão)
python main.py process minha-app web

# Deploy com tag específica
python main.py process minha-app api --tag v1.2.3

# Deploy com tag específica (usando =)
python main.py process minha-app worker --tag production
```

## Estrutura de Diretórios

```
/services/
├── minha-app/
│   ├── web.compose.yml
│   ├── api.compose.yml
│   └── worker.compose.yml
└── outra-app/
    ├── web.compose.yml
    └── api.compose.yml
```

Cada aplicação deve ter seus arquivos de compose no diretório `/services/<app_name>/` com a nomenclatura `<app_type>.compose.yml`.

## Como Funciona

1. **Validação**: Verifica se o diretório e arquivo compose existem
2. **Atualização de Imagens**:
   - Busca services da stack pelo label Docker
   - Remove imagens antigas
   - Faz pull da nova imagem
3. **Deploy**: Executa `docker stack deploy` com o arquivo compose
4. **Logging**: Registra todas as operações em `/service/logs/<app_name>.log`

## Logs

Os logs são armazenados em `/service/logs/<app_name>.log` com nível WARNING ou superior.

## Troubleshooting

### Erro: "A pasta não existe"
Certifique-se que o diretório `/services/<app_name>` existe.

### Erro: "O arquivo compose não está definido"
Verifique se o arquivo `/services/<app_name>/<app_type>.compose.yml` existe.

### Erro: Permissão negada ao Docker
Certifique-se que seu usuário tem permissão de acesso ao socket Docker:
```bash
# Linux
sudo usermod -aG docker $USER
```

## Dependências

- **typer** - Framework CLI
- **docker** - Client Docker
- **loguru** - Logging
- **python-dotenv** - Variáveis de ambiente
