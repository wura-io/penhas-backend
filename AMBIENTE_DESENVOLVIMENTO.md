# Ambiente de Desenvolvimento - PenhaS Backend

Guia completo para configurar e rodar o backend do PenhaS localmente usando Docker.

## Pre-requisitos

- **Docker Desktop 4+** (macOS ou Windows) ou **Docker Engine 20+** (Linux)
- **docker compose** (V2, incluido no Docker Desktop)
- **git**
- **4 GB de RAM livres** para os containers
- ~5 GB de disco para imagens Docker

> No macOS com Apple Silicon (M1/M2/M3/M4), o Docker Desktop roda as imagens x86 via emulacao Rosetta. Funciona, mas o startup sera mais lento.

## Inicio Rapido

```bash
# 1. Clonar o repositorio
git clone https://github.com/institutoazmina/penhas-backend.git
cd penhas-backend

# 2. Criar diretorios de dados
mkdir -p data/redis data/postgresql

# 3. Subir o ambiente
docker compose -f docker-compose.dev.yaml up -d

# 4. Acompanhar o startup (primeira vez instala dependencias Perl)
docker compose -f docker-compose.dev.yaml logs -f penhas_api

# 5. Quando aparecer "Redirecting STDERR/STDOUT to /data/log/...", testar:
curl http://localhost:8080/
# Resposta esperada: {"error":"Page not found","message":"Página ou item não existe"}
```

O primeiro startup demora mais porque o container:
1. Instala dependencias Perl via `cpanm`
2. Roda migrations do banco via `sqitch deploy`
3. Inicia o servidor Hypnotoad

Startups subsequentes sao mais rapidos porque as dependencias ficam em cache no volume.

## Arquitetura do Ambiente Dev

```
docker-compose.dev.yaml
├── db (postgis/postgis:13-3.1)          -> 127.0.0.1:5432
├── redis (bitnami/redis:latest)         -> interno (porta 6379)
└── penhas_api (penhas-backend:latest)   -> 127.0.0.1:8080
    ├── volume: ./api -> /src
    ├── volume: ./data -> /data
    └── volume: ./dev/SHELL -> /etc/container_environment/SHELL
```

### Componentes

| Servico | Imagem | Funcao |
|---------|--------|--------|
| **db** | `postgis/postgis:13-3.1` | PostgreSQL 13 com extensao PostGIS |
| **redis** | `bitnami/redis:latest` | Cache e filas (sem senha) |
| **penhas_api** | `ghcr.io/institutoazmina/penhas-backend:latest` | API Perl/Mojolicious + Minion workers |

### Como a Conectividade Funciona

Todos os containers estao nas mesmas Docker networks (`db_network` e `cache`). O `envfile_local.sh` configura:

- `POSTGRESQL_HOST="db"` — usa o hostname do servico Docker diretamente
- `SQITCH_DEPLOY` — passa a URI completa `db:pg://postgres:trustable@db:5432/touchbase_dev` para o sqitch, evitando o target "docker" do `sqitch.conf` (que aponta para `172.17.0.1`, o gateway Docker do Linux)
- `REDIS_SERVER="redis:6379"` — definido via environment no compose

### Detalhes Tecnicos

O container `penhas_api` usa a imagem base **phusion/baseimage** que gerencia servicos via **runit**. Um detalhe importante: o perlbrew instalado na imagem detecta a shell via `$SHELL` para decidir o formato de saida dos comandos. O arquivo `dev/SHELL` e montado em `/etc/container_environment/SHELL` para garantir que todos os processos runit recebam `SHELL=/bin/bash`. Sem isso, o perlbrew gera comandos no formato csh (`unsetenv`/`setenv`) que falham em bash.

As imagens `db` e `penhas_api` usam `platform: linux/amd64` pois nao possuem builds ARM64 nativos. No Apple Silicon, o Docker Desktop emula via Rosetta.

### Credenciais

Todas as credenciais sao de desenvolvimento:

| Parametro | Valor | Usado por |
|-----------|-------|-----------|
| DB Host | `db` (Docker service) | `envfile_local.sh`, sqitch URI |
| DB Name | `touchbase_dev` | compose, `envfile_local.sh`, sqitch URI |
| DB User | `postgres` | todos |
| DB Password | `trustable` | compose, `envfile_local.sh`, sqitch URI |

## Sequencia de Startup

Quando o container `penhas_api` inicia, o runit executa `script/start-server.sh`:

1. **Carrega perlbrew**: `source /home/app/perl5/perlbrew/etc/bashrc`
2. **Carrega variaveis**: Prioriza `envfile_local.sh` sobre `envfile.sh`
3. **Instala dependencias**: `cpanm -nv . --installdeps` (Perl/CPAN)
4. **Roda migrations**: `sqitch deploy -t $SQITCH_DEPLOY` (cria/atualiza schema)
5. **Inicia servidor**: `hypnotoad script/penhas-api` (porta 8080)
6. **Mantem container vivo**: `sleep infinity`

## Comandos Uteis

### Logs

```bash
# Todos os servicos
docker compose -f docker-compose.dev.yaml logs -f

# Apenas a API
docker compose -f docker-compose.dev.yaml logs -f penhas_api

# Apenas o banco
docker compose -f docker-compose.dev.yaml logs -f db

# Log da aplicacao (dentro do container, apos o Hypnotoad redirecionar)
docker compose -f docker-compose.dev.yaml exec penhas_api tail -f /data/log/penhas-api.$(date +%Y-%m-%d).log
```

### Terminal no Container

```bash
# Como usuario app (padrao para desenvolvimento)
docker compose -f docker-compose.dev.yaml exec -u app penhas_api bash

# Como root (para instalar pacotes do sistema)
docker compose -f docker-compose.dev.yaml exec -u root penhas_api bash
```

### Reiniciar Servicos

```bash
# Reiniciar apenas a API (sem derrubar o banco)
docker compose -f docker-compose.dev.yaml restart penhas_api

# Reload graceful do Hypnotoad (dentro do container)
docker compose -f docker-compose.dev.yaml exec -u app penhas_api /src/script/restart-services.sh

# Derrubar tudo e subir novamente
docker compose -f docker-compose.dev.yaml down
docker compose -f docker-compose.dev.yaml up -d
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL via psql
docker compose -f docker-compose.dev.yaml exec db psql -U postgres touchbase_dev

# Rodar migrations manualmente (dentro do container da API)
docker compose -f docker-compose.dev.yaml exec -u app penhas_api bash -c \
  'source /home/app/perl5/perlbrew/etc/bashrc && cd /src && source envfile_local.sh && sqitch deploy -t "$SQITCH_DEPLOY"'

# Ver status das migrations
docker compose -f docker-compose.dev.yaml exec -u app penhas_api bash -c \
  'source /home/app/perl5/perlbrew/etc/bashrc && cd /src && source envfile_local.sh && sqitch status -t "$SQITCH_DEPLOY"'
```

### Parar o Ambiente

```bash
# Parar containers (dados persistem nos volumes)
docker compose -f docker-compose.dev.yaml down

# Parar e remover volumes (limpa banco e redis)
docker compose -f docker-compose.dev.yaml down -v
rm -rf data/postgresql data/redis
```

## Rodando Testes

Os testes usam o framework `yath` com o plugin Penhas. Para rodar dentro do container:

```bash
# Entrar no container
docker compose -f docker-compose.dev.yaml exec -u app penhas_api bash

# Dentro do container:
cd /src
yath test -j 4 -PPenhas -Ilib t/
```

Variaveis uteis para debug:

```bash
# Mostrar queries SQL executadas pelo ORM
DBIC_TRACE=1 yath test -j 4 -PPenhas -Ilib t/

# Mostrar request/response dos testes
TRACE=1 yath test -j 4 -PPenhas -Ilib t/

# Ambos
DBIC_TRACE=1 TRACE=1 yath test -j 4 -PPenhas -Ilib t/
```

## Troubleshooting

### Apple Silicon (ARM64) - Container muito lento

A imagem do backend e x86_64. No Apple Silicon, o Docker usa emulacao Rosetta/QEMU. O primeiro `cpanm` pode levar bastante tempo.

**Solucao**: Certifique-se de que "Use Rosetta for x86_64/amd64 emulation" esta habilitado nas configuracoes do Docker Desktop (Settings > General).

### Erros "unsetenv: command not found" no log

Esses erros vem do perlbrew quando `$SHELL` nao esta configurado como `/bin/bash`. O arquivo `dev/SHELL` montado em `/etc/container_environment/SHELL` resolve isso. Se os erros aparecerem, verifique que o volume mount existe no compose:

```yaml
- ./dev/SHELL:/etc/container_environment/SHELL:ro
```

### Porta 5432 ja em uso

Se voce tem PostgreSQL local rodando na porta 5432:

```bash
# Verificar o que usa a porta
lsof -i :5432

# Opcao 1: Parar o PostgreSQL local
brew services stop postgresql    # macOS com Homebrew
sudo systemctl stop postgresql   # Linux

# Opcao 2: Mudar a porta no docker-compose.dev.yaml
```

### Porta 8080 ja em uso

```bash
lsof -i :8080
# Pare o servico conflitante ou altere a porta no docker-compose.dev.yaml
```

### Container da API reiniciando em loop

```bash
# Ver os logs para entender o erro
docker compose -f docker-compose.dev.yaml logs penhas_api

# Ver o log da aplicacao (erros do Hypnotoad)
docker compose -f docker-compose.dev.yaml exec penhas_api cat /data/log/penhas-api.$(date +%Y-%m-%d).log

# Causas comuns:
# 1. Banco ainda nao esta pronto -> aguardar healthcheck
# 2. Variavel de ambiente faltando -> verificar envfile_local.sh
# 3. Falta de memoria -> aumentar RAM do Docker Desktop
```

### Erro "missing PUBLIC_API_URL"

A aplicacao requer `PUBLIC_API_URL` definido. O `envfile_local.sh` ja inclui essa variavel. Se aparecer esse erro, verifique que o arquivo existe e contem:

```bash
export PUBLIC_API_URL="http://localhost:8080/"
```

### Erro de conexao com o banco (sqitch/API)

```bash
# Verificar se o banco esta rodando e saudavel
docker compose -f docker-compose.dev.yaml ps
docker compose -f docker-compose.dev.yaml exec db pg_isready -U postgres

# Testar conexao manualmente
docker compose -f docker-compose.dev.yaml exec db psql -U postgres -d touchbase_dev -c "SELECT 1"
```

### Timeout no download da imagem Docker

A imagem `ghcr.io/institutoazmina/penhas-backend:latest` pode ser grande. Se o download falhar:

```bash
# Tentar pull isolado
docker pull --platform linux/amd64 ghcr.io/institutoazmina/penhas-backend:latest

# Se persistir, verificar conexao e tentar novamente
```

### Limpar tudo e comecar do zero

```bash
docker compose -f docker-compose.dev.yaml down -v
rm -rf data/postgresql data/redis
mkdir -p data/redis data/postgresql
docker compose -f docker-compose.dev.yaml up -d
```

## Estrutura de Pastas

```
penhas-backend/
├── api/                          # Codigo fonte da API
│   ├── deploy_db/                # Migrations do banco (sqitch)
│   │   ├── deploy/               # Arquivos SQL de cada migration
│   │   │   ├── 0001-db-init.sql
│   │   │   └── ...
│   │   └── sqitch.plan           # Controle de migrations
│   ├── docker/                   # Arquivos para montar a imagem Docker
│   ├── envfile.sh                # Configuracao padrao (producao)
│   ├── envfile_local.sh          # Configuracao local (dev) - priorizado pelo start-server.sh
│   ├── lib/
│   │   ├── Penhas/               # Codigo principal
│   │   │   ├── Controller/       # Controllers das rotas
│   │   │   ├── Helpers/          # Funcoes auxiliares
│   │   │   ├── Minion/Tasks/     # Jobs em background
│   │   │   ├── Routes.pm         # Definicao de rotas
│   │   │   ├── Schema*/          # ORM (DBIx::Class) - gerado automaticamente
│   │   │   ├── SchemaConnected.pm # Conexao com banco
│   │   │   ├── Types.pm          # Validacoes (CPF, Nome, etc)
│   │   │   └── Utils.pm          # Funcoes utilitarias
│   │   └── Penhas.pm             # Bootstrap da aplicacao
│   ├── public/                   # Arquivos estaticos (templates de email, assets)
│   ├── script/
│   │   ├── penhas-api            # Entrypoint da aplicacao
│   │   ├── start-server.sh       # Script de inicializacao
│   │   └── restart-services.sh   # Reload graceful
│   ├── sqitch.conf               # Configuracao do sqitch (targets de banco)
│   ├── t/                        # Testes
│   └── xt/                       # Testes de autor
├── dev/                          # Arquivos auxiliares de desenvolvimento
│   └── SHELL                     # Define SHELL=/bin/bash para phusion baseimage
├── docker-compose.yaml           # Compose de producao (sem PostgreSQL)
├── docker-compose.dev.yaml       # Compose de desenvolvimento (auto-contido)
├── data/                         # Dados persistentes (gitignored)
│   ├── postgresql/               # Dados do PostgreSQL
│   └── redis/                    # Dados do Redis
└── .env                          # Variaveis de ambiente para docker-compose
```

## Diferenca entre Ambiente Dev e Producao

| Aspecto | Dev (`docker-compose.dev.yaml`) | Producao (`docker-compose.yaml`) |
|---------|------|----------|
| PostgreSQL | Incluido como servico | Externo (RDS, host, etc) |
| Redis | Sem senha | Configuravel |
| Portas | `127.0.0.1` (loopback) | `172.17.0.1` (bridge Docker Linux) |
| DB Host na API | `db` (Docker service name) | `172.17.0.1` (bridge gateway) |
| API workers | 1 | Configuravel |
| Directus | Nao incluido | Incluido |
| Imagem API | `latest` | Tag fixa (commit SHA) |
| Platform | `linux/amd64` explicito | Nativo do host |

## Admin

Apos as migrations rodarem, o usuario admin padrao e:

- **URL**: http://localhost:8080/admin
- **Email**: `admin@sample.com`
- **Senha**: `admin@sample.com`
