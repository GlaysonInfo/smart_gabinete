# Gabinete IA

Base codificada do projeto **GESTAO DE MANDATOS / GABINETE IA** a partir dos contratos, DDL, modelo relacional e wireframe fornecidos.

## O que esta implementado

- API FastAPI em `/api/v1`
- OpenAPI oficial servido em `/openapi.json` e `/docs`
- Autenticacao JWT com `access_token` e `refresh_token`
- Respostas no padrao `{ data, meta }` e erros no padrao `{ error, meta }`
- Persistencia local em JSON para rodar o MVP sem banco externo
- Seed inicial com gabinete, usuarios, equipe, territorios, contato, demanda, agenda, documento, protocolo, tarefa e projeto
- Frontend web em `/app/`
- Smoke test de login, demanda, historico e dashboard

## Usuarios demo

Credenciais de demonstracao para ambiente local ou validacao controlada do MVP:

```text
chefe@gabineteia.local / Senha@123
assessor@gabineteia.local / Senha@123
```

Evite reutilizar essas credenciais em ambiente publico sem troca imediata de senha.

## Rodar localmente

```powershell
.\scripts\run_api.ps1
```

Depois abra:

```text
http://127.0.0.1:8010/app/
http://127.0.0.1:8010/mobile/
http://127.0.0.1:8010/mandato/
http://127.0.0.1:8010/docs
```

## Testar no celular na mesma rede

O script sobe a API em `0.0.0.0`, entao ela fica acessivel na sua rede local.

1. Descubra o IP da sua maquina na rede local, por exemplo com `ipconfig` no Windows.
2. Inicie a API com `./scripts/run_api.ps1`.
3. No navegador do celular, abra `http://SEU_IP:8010/app/` para o sistema de gestao.
4. No navegador do celular, abra `http://SEU_IP:8010/mobile/` para o app mobile.
5. No navegador do celular, abra `http://SEU_IP:8010/mandato/` para o app executivo do vereador.
6. Se nao abrir, libere a porta `8010` no Firewall do Windows para redes privadas.

Exemplo:

```text
http://192.168.0.15:8010/app/
http://192.168.0.15:8010/mobile/
http://192.168.0.15:8010/mandato/
```

## Publicacao

### GitHub Pages

O campo `Custom domain` do GitHub Pages aceita apenas dominios reais, como `app.seudominio.com`.

Nao use a URL do repositorio, por exemplo:

```text
github.com/GlaysonInfo/smart_gabinete
```

Se quiser usar o dominio padrao do GitHub Pages, deixe `Custom domain` em branco.
O endereco padrao do projeto sera:

```text
https://glaysoninfo.github.io/smart_gabinete/
```

### Limite importante

Este projeto nao e apenas frontend estatico. O web app e o app mobile dependem da API FastAPI em `/api/v1`.
GitHub Pages nao executa Python/FastAPI, entao ele nao publica o sistema completo sozinho.

Para publicar o sistema funcional, use uma hospedagem de aplicacao, por exemplo Render, Railway, Fly.io ou VPS.
GitHub Pages pode servir apenas uma pagina estatica, documentacao ou demo desacoplada da API.

### Publicar no Render

O repositorio ja inclui o arquivo `render.yaml` para subir a aplicacao completa no Render.

Passos:

1. Acesse o dashboard do Render.
2. Escolha `New +` -> `Blueprint`.
3. Conecte o repositorio `GlaysonInfo/smart_gabinete`.
4. Confirme a criacao do servico `smart-gabinete`.
5. Aguarde o deploy inicial.

Configuracao aplicada pelo blueprint:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn apps.api.app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Disco persistente montado em `/opt/render/project/data`
- Segredos gerados automaticamente para JWT e pepper
- CORS restrito por padrao para localhost e dominios `*.onrender.com`

Depois do deploy, use:

```text
https://SEU-SERVICO.onrender.com/app/
https://SEU-SERVICO.onrender.com/mobile/
https://SEU-SERVICO.onrender.com/mandato/
https://SEU-SERVICO.onrender.com/docs
```

Observacao:

- O projeto usa persistencia local em JSON. Sem disco persistente, os dados podem ser perdidos a cada novo deploy.
- O blueprint ja prepara esse armazenamento em `/opt/render/project/data`.
- Ao subir uma nova versao, o backend aplica migracoes leves no boot para manter o JSON persistido compativel, incluindo a conversao do modulo de emendas para `pleiteada/aprovada/empenhada`.
- Se voce usar dominio proprio no frontend, ajuste `GABINETE_IA_CORS_ORIGINS` e, se necessario, `GABINETE_IA_CORS_ORIGIN_REGEX` no Render.

### Reset de senha

O endpoint `POST /api/v1/usuarios/{usuario_id}/reset-senha` nao define mais uma senha fixa.
Agora ele exige payload explicito com `nova_senha_temporaria`.

Exemplo:

```json
{
	"nova_senha_temporaria": "SenhaTemp@2026"
}
```

## Validar

```powershell
pip install -r requirements.txt
python scripts/smoke_api.py
```

O smoke usa `fastapi.testclient` com base dedicada em `data/smoke_gabinete_ia.json`.
Ele valida login, leitura de perfil, listagens principais, criacao de demanda, historico e o overview executivo sem mexer na base operacional principal.

## Estrutura

```text
apps/api/app/      Backend FastAPI
apps/web/          Frontend web estatico
data/              Base JSON local e uploads
scripts/           Scripts de execucao e validacao
```

## Banco definitivo

O arquivo `ddl_sql_gabinete_ia.sql` permanece como referencia para PostgreSQL. A persistencia JSON atual existe para acelerar o MVP executavel; a proxima evolucao natural e trocar `JsonStore` por repositorios SQLAlchemy/PostgreSQL mantendo os mesmos endpoints.
