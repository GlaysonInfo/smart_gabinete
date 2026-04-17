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

```text
chefe@gabineteia.local / Senha@123
assessor@gabineteia.local / Senha@123
```

## Rodar localmente

```powershell
.\scripts\run_api.ps1
```

Depois abra:

```text
http://127.0.0.1:8010/app/
http://127.0.0.1:8010/mobile/
http://127.0.0.1:8010/docs
```

## Testar no celular na mesma rede

O script sobe a API em `0.0.0.0`, entao ela fica acessivel na sua rede local.

1. Descubra o IP da sua maquina na rede local, por exemplo com `ipconfig` no Windows.
2. Inicie a API com `./scripts/run_api.ps1`.
3. No navegador do celular, abra `http://SEU_IP:8010/app/` para o sistema de gestao.
4. No navegador do celular, abra `http://SEU_IP:8010/mobile/` para o app mobile.
5. Se nao abrir, libere a porta `8010` no Firewall do Windows para redes privadas.

Exemplo:

```text
http://192.168.0.15:8010/app/
http://192.168.0.15:8010/mobile/
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

## Validar

```powershell
python scripts/smoke_api.py
```

## Estrutura

```text
apps/api/app/      Backend FastAPI
apps/web/          Frontend web estatico
data/              Base JSON local e uploads
scripts/           Scripts de execucao e validacao
```

## Banco definitivo

O arquivo `ddl_sql_gabinete_ia.sql` permanece como referencia para PostgreSQL. A persistencia JSON atual existe para acelerar o MVP executavel; a proxima evolucao natural e trocar `JsonStore` por repositorios SQLAlchemy/PostgreSQL mantendo os mesmos endpoints.
