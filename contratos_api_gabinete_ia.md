# Contratos de API por módulo — GESTÃO DE MANDATOS / GABINETE IA

## 1. Objetivo

Definir os contratos de API do **GABINETE IA** por domínio funcional, cobrindo:
- padrões gerais
- autenticação
- payloads principais
- respostas esperadas
- erros padrão
- filtros, paginação e ordenação
- regras de autorização por perfil

Este documento foi desenhado para um backend **FastAPI** com APIs REST, podendo evoluir depois para eventos assíncronos, webhooks e integração externa.

---

# 2. Convenções gerais

## 2.1 Base URL
```text
/api/v1
```

## 2.2 Formato padrão de resposta
### Sucesso com recurso único
```json
{
  "data": {},
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Sucesso com lista paginada
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 135,
    "total_pages": 7,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Erro padrão
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Campos inválidos no payload.",
    "details": [
      {
        "field": "email_login",
        "message": "Formato inválido."
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

## 2.3 Headers recomendados
```text
Authorization: Bearer <token>
Content-Type: application/json
X-Request-Id: <uuid opcional>
X-Client-App: mobile|web
X-Client-Version: <versão opcional>
```

## 2.4 Códigos HTTP
- `200` leitura/atualização bem-sucedida
- `201` criação bem-sucedida
- `202` processamento aceito
- `204` sem conteúdo
- `400` erro de validação
- `401` não autenticado
- `403` sem permissão
- `404` recurso não encontrado
- `409` conflito de estado ou duplicidade
- `422` regra de negócio violada
- `429` rate limit
- `500` erro interno

## 2.5 Paginação padrão
Query params:
```text
?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

## 2.6 Filtro padrão
Sempre que possível:
- filtros por período com `date_from` e `date_to`
- filtros por `status`
- filtros por `territorio_id`
- filtros por `responsavel_usuario_id`
- filtros por `search`

## 2.7 Segurança
- JWT com access token + refresh token
- RBAC por perfil
- escopo por território/equipe/gabinete
- validação de ownership no mobile

---

# 3. Módulo Auth

## 3.1 POST `/auth/login`
### Objetivo
Autenticar usuário.

### Request
```json
{
  "email_login": "usuario@gabinete.com",
  "senha": "Senha@123"
}
```

### Response 200
```json
{
  "data": {
    "access_token": "jwt",
    "refresh_token": "jwt_refresh",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "nome": "Maria Souza",
      "perfil": "CHEFE_GABINETE",
      "gabinete_id": "uuid",
      "equipe_id": null,
      "escopos": [
        {
          "id": "uuid",
          "escopo_tipo": "TERRITORIO",
          "territorio_id": "uuid"
        }
      ]
    }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- bloqueia usuário inativo
- bloqueia perfil sem acesso ao cliente chamador, se necessário
- registra último login

---

## 3.2 POST `/auth/refresh`
### Request
```json
{
  "refresh_token": "jwt_refresh"
}
```

### Response 200
```json
{
  "data": {
    "access_token": "novo_jwt",
    "refresh_token": "novo_refresh",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 3.3 POST `/auth/logout`
### Request
```json
{
  "refresh_token": "jwt_refresh"
}
```

### Response 204
Sem corpo.

---

## 3.4 GET `/auth/me`
### Objetivo
Retornar contexto do usuário autenticado.

### Response 200
```json
{
  "data": {
    "id": "uuid",
    "nome": "Maria Souza",
    "perfil": "CHEFE_GABINETE",
    "gabinete_id": "uuid",
    "equipe_id": null,
    "mfa_habilitado": false,
    "escopos": []
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 4. Módulo Administração

# 4.1 Usuários

## 4.1.1 GET `/usuarios`
### Perfis
- `CHEFE_GABINETE`

### Query params
```text
?search=&perfil=&equipe_id=&ativo=&page=1&page_size=20
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Carlos Lima",
      "email_login": "carlos@gabinete.com",
      "telefone": "31999999999",
      "perfil": "ASSESSOR_NIVEL_1",
      "equipe_id": "uuid",
      "ativo": true,
      "ultimo_login": "2026-04-15T18:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 4.1.2 POST `/usuarios`
### Request
```json
{
  "nome": "Carlos Lima",
  "email_login": "carlos@gabinete.com",
  "telefone": "31999999999",
  "perfil": "ASSESSOR_NIVEL_1",
  "foto_upload_id": "uuid-opcional",
  "foto_url": "/uploads-public/foto-carlos.jpg",
  "equipe_id": "uuid",
  "ativo": true,
  "escopos": [
    {
      "escopo_tipo": "TERRITORIO",
      "territorio_id": "uuid"
    },
    {
      "escopo_tipo": "EQUIPE",
      "equipe_id": "uuid"
    }
  ]
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "nome": "Carlos Lima",
    "email_login": "carlos@gabinete.com",
    "perfil": "ASSESSOR_NIVEL_1",
    "foto_url_publica": "/uploads-public/foto-carlos.jpg",
    "ativo": true
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- `email_login` único
- `perfil` obrigatório
- `escopos` obrigatórios conforme perfil
- senha inicial enviada por fluxo separado ou provisionada temporariamente

---

## 4.1.3 GET `/usuarios/{usuario_id}`
### Response 200
```json
{
  "data": {
    "id": "uuid",
    "nome": "Carlos Lima",
    "email_login": "carlos@gabinete.com",
    "telefone": "31999999999",
    "perfil": "ASSESSOR_NIVEL_1",
    "equipe_id": "uuid",
    "ativo": true,
    "escopos": [
      {
        "id": "uuid",
        "escopo_tipo": "TERRITORIO",
        "territorio_id": "uuid"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 4.1.4 PUT `/usuarios/{usuario_id}`
### Request
```json
{
  "nome": "Carlos Lima Atualizado",
  "telefone": "31988888888",
  "perfil": "SUPERVISOR_EQUIPE",
  "foto_upload_id": "uuid-opcional",
  "foto_url": "/uploads-public/foto-carlos-atualizada.jpg",
  "equipe_id": "uuid",
  "ativo": true,
  "escopos": [
    {
      "escopo_tipo": "EQUIPE",
      "equipe_id": "uuid"
    }
  ]
}
```

### Response 200
Mesmo formato do GET por id.

---

## 4.1.5 PATCH `/usuarios/{usuario_id}/status`
### Request
```json
{
  "ativo": false
}
```

### Response 200
```json
{
  "data": {
    "id": "uuid",
    "ativo": false
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 4.1.6 POST `/usuarios/{usuario_id}/reset-senha`
### Request
```json
{
  "motivo": "Solicitação do usuário"
}
```

### Response 202
```json
{
  "data": {
    "status": "RESET_ENFILEIRADO"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 4.2 Equipes

## 4.2.1 GET `/equipes`
## 4.2.2 POST `/equipes`
## 4.2.3 GET `/equipes/{equipe_id}`
## 4.2.4 PUT `/equipes/{equipe_id}`

### Exemplo Request POST
```json
{
  "nome": "Equipe Centro",
  "descricao": "Equipe territorial do centro",
  "supervisor_usuario_id": "uuid",
  "ativo": true
}
```

### Exemplo Response
```json
{
  "data": {
    "id": "uuid",
    "nome": "Equipe Centro",
    "supervisor_usuario_id": "uuid",
    "ativo": true
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 4.3 Auditoria

## GET `/auditoria`
### Perfis
- `CHEFE_GABINETE`

### Query params
```text
?date_from=&date_to=&usuario_id=&entidade=&acao=&page=1&page_size=20
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "usuario_id": "uuid",
      "entidade": "usuario",
      "entidade_id": "uuid",
      "acao": "UPDATE",
      "payload_anterior": {},
      "payload_novo": {},
      "created_at": "2026-04-16T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 5. Módulo Territórios e Cadastros Base

# 5.1 Territórios

## 5.1.1 GET `/territorios/tree`
### Objetivo
Retornar árvore territorial completa.

### Response 200
```json
{
  "data": [
    {
      "id": "uuid-regiao",
      "nome": "Região Centro",
      "tipo": "REGIAO",
      "children": [
        {
          "id": "uuid-bairro",
          "nome": "Centro",
          "tipo": "BAIRRO",
          "children": [
            {
              "id": "uuid-micro",
              "nome": "Microárea 1",
              "tipo": "MICROAREA",
              "children": []
            }
          ]
        }
      ]
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 5.1.2 GET `/territorios`
### Query params
```text
?tipo=BAIRRO&parent_id=uuid&ativo=true&page=1&page_size=20
```

---

## 5.1.3 POST `/territorios`
### Request
```json
{
  "parent_id": "uuid-regiao",
  "nome": "Novo Bairro",
  "tipo": "BAIRRO",
  "codigo_externo": "B001",
  "ativo": true
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "parent_id": "uuid-regiao",
    "nome": "Novo Bairro",
    "tipo": "BAIRRO",
    "ativo": true
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- `REGIAO` não pode ter `parent_id`
- `BAIRRO` deve ter `parent_id` de `REGIAO`
- `MICROAREA` deve ter `parent_id` de `BAIRRO`

---

## 5.1.4 PUT `/territorios/{territorio_id}`
## 5.1.5 PATCH `/territorios/{territorio_id}/status`

---

# 5.2 Organizações

## GET `/organizacoes`
## POST `/organizacoes`
## GET `/organizacoes/{organizacao_id}`
## PUT `/organizacoes/{organizacao_id}`

### Exemplo POST
```json
{
  "territorio_id": "uuid",
  "nome": "Associação do Bairro Centro",
  "tipo": "ASSOCIACAO",
  "telefone": "31999999999",
  "email": "contato@assoc.org",
  "endereco": "Rua A, 100",
  "observacoes": "Atuação comunitária",
  "status": "ATIVO"
}
```

---

# 5.3 Lideranças Comunitárias

## GET `/liderancas`
## POST `/liderancas`
## GET `/liderancas/{lideranca_id}`
## PUT `/liderancas/{lideranca_id}`

### Exemplo POST
```json
{
  "territorio_id": "uuid",
  "organizacao_id": "uuid",
  "nome": "João da Comunidade",
  "telefone": "31999999999",
  "email": "joao@email.com",
  "tema_principal": "Mobilidade urbana",
  "observacoes": "Contato institucional"
}
```

---

# 6. Módulo Contatos / Cidadãos

## 6.1 GET `/contatos`
### Perfis
- `ASSESSOR_NIVEL_1`
- `SUPERVISOR_EQUIPE`
- `CHEFE_GABINETE`
- `ASSESSOR_ADMINISTRATIVO`
- `ASSESSOR_JURIDICO` em leitura quando aplicável

### Query params
```text
?search=&territorio_id=&status=&tipo_contato=&duplicidade_suspeita=&page=1&page_size=20
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Maria da Silva",
      "cpf": null,
      "telefone_principal": "31999999999",
      "email": null,
      "territorio_id": "uuid",
      "territorio_nome": "Centro",
      "tipo_contato": "CIDADAO",
      "status": "ATIVO",
      "duplicidade_suspeita": false,
      "created_at": "2026-04-16T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 6.2 POST `/contatos`
### Request
```json
{
  "territorio_id": "uuid",
  "origem_cadastro": "WEB_INTERNO",
  "nome": "Maria da Silva",
  "cpf": null,
  "data_nascimento": null,
  "telefone_principal": "31999999999",
  "telefone_secundario": null,
  "email": null,
  "logradouro": "Rua A",
  "numero": "10",
  "complemento": null,
  "bairro": "Centro",
  "cidade": "Betim",
  "cep": "32600000",
  "tipo_contato": "CIDADAO",
  "foto_upload_id": "uuid-opcional",
  "foto_url": "/uploads-public/foto-maria.jpg",
  "observacoes": "Contato presencial"
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "nome": "Maria da Silva",
    "status": "ATIVO",
    "duplicidade_suspeita": false
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- nome obrigatório
- CPF único quando informado
- `foto_upload_id` e `foto_url` são opcionais
- pode marcar `duplicidade_suspeita` automaticamente por heurística

---

## 6.3 GET `/contatos/{contato_id}`
### Response 200
```json
{
  "data": {
    "id": "uuid",
    "territorio_id": "uuid",
    "origem_cadastro": "WEB_INTERNO",
    "nome": "Maria da Silva",
    "cpf": null,
    "telefone_principal": "31999999999",
    "email": null,
    "logradouro": "Rua A",
    "bairro": "Centro",
    "cidade": "Betim",
    "tipo_contato": "CIDADAO",
    "status": "ATIVO",
    "duplicidade_suspeita": false,
    "observacoes": "Contato presencial",
    "consentimentos": [],
    "tags": [],
    "resumo": {
      "total_demandas": 2,
      "total_agendas": 1,
      "total_documentos": 0
    }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 6.4 PUT `/contatos/{contato_id}`
### Request
Mesmo formato do POST, acrescido dos campos editáveis.

---

## 6.5 PATCH `/contatos/{contato_id}/status`
### Request
```json
{
  "status": "INATIVO"
}
```

---

## 6.6 GET `/contatos/{contato_id}/demandas`
## 6.7 GET `/contatos/{contato_id}/agenda`
## 6.8 GET `/contatos/{contato_id}/documentos`

---

## 6.9 GET `/contatos/duplicidades`
### Query params
```text
?search=Maria&territorio_id=uuid
```

### Response 200
```json
{
  "data": [
    {
      "grupo": 1,
      "itens": [
        {
          "id": "uuid-1",
          "nome": "Maria da Silva",
          "telefone_principal": "31999999999",
          "cpf": null
        },
        {
          "id": "uuid-2",
          "nome": "Maria da Silva",
          "telefone_principal": "31999999999",
          "cpf": null
        }
      ]
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 7. Módulo Consentimento

## 7.1 GET `/contatos/{contato_id}/consentimentos`
## 7.2 POST `/contatos/{contato_id}/consentimentos`

### Request POST
```json
{
  "canal": "WHATSAPP",
  "consentido": true,
  "finalidade": "atendimento institucional",
  "forma_registro": "verbal",
  "observacao": "Autorizado no atendimento presencial"
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "canal": "WHATSAPP",
    "consentido": true,
    "finalidade": "atendimento institucional",
    "registrado_em": "2026-04-16T10:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 8. Módulo Demandas

## 8.1 GET `/demandas`
### Query params
```text
?search=&status=&prioridade=&categoria_id=&territorio_id=&responsavel_usuario_id=&date_from=&date_to=&page=1&page_size=20
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "titulo": "Solicitação de poda de árvore",
      "cidadao_id": "uuid",
      "cidadao_nome": "Maria da Silva",
      "territorio_id": "uuid",
      "territorio_nome": "Centro",
      "categoria_id": "uuid",
      "categoria_nome": "URBANA",
      "prioridade": "ALTA",
      "status": "EM_TRIAGEM",
      "responsavel_usuario_id": null,
      "sla_data": "2026-04-18T18:00:00Z",
      "criticidade_derivada": "ALTA",
      "created_at": "2026-04-16T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 8.2 POST `/demandas`
### Request
```json
{
  "cidadao_id": "uuid",
  "territorio_id": "uuid",
  "categoria_id": "uuid",
  "titulo": "Solicitação de poda de árvore",
  "descricao": "Árvore com risco em frente à residência.",
  "prioridade": "MEDIA",
  "origem_cadastro": "WEB_INTERNO"
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "titulo": "Solicitação de poda de árvore",
    "status": "ABERTA",
    "prioridade": "MEDIA",
    "responsavel_usuario_id": null,
    "data_abertura": "2026-04-16T10:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- título obrigatório
- descrição obrigatória
- categoria recomendada/obrigatória conforme processo
- histórico inicial deve ser gerado automaticamente

---

## 8.3 GET `/demandas/{demanda_id}`
### Response 200
```json
{
  "data": {
    "id": "uuid",
    "cidadao_id": "uuid",
    "cidadao_nome": "Maria da Silva",
    "territorio_id": "uuid",
    "categoria_id": "uuid",
    "titulo": "Solicitação de poda de árvore",
    "descricao": "Árvore com risco em frente à residência.",
    "prioridade": "ALTA",
    "status": "EM_ATENDIMENTO",
    "responsavel_usuario_id": "uuid",
    "responsavel_nome": "Carlos Lima",
    "sla_data": "2026-04-18T18:00:00Z",
    "data_abertura": "2026-04-16T10:00:00Z",
    "data_conclusao": null,
    "tags": [],
    "anexos": []
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 8.4 PUT `/demandas/{demanda_id}`
### Request
```json
{
  "categoria_id": "uuid",
  "titulo": "Solicitação atualizada",
  "descricao": "Descrição atualizada",
  "prioridade": "ALTA",
  "status": "EM_ATENDIMENTO",
  "responsavel_usuario_id": "uuid",
  "sla_data": "2026-04-18T18:00:00Z"
}
```

### Regras
- mudança relevante deve gerar histórico
- escopo do usuário deve ser validado

---

## 8.5 POST `/demandas/{demanda_id}/assumir`
### Request
```json
{}
```

### Response 200
```json
{
  "data": {
    "id": "uuid",
    "responsavel_usuario_id": "uuid-do-logado",
    "status": "EM_ATENDIMENTO"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 8.6 POST `/demandas/{demanda_id}/atribuir`
### Perfis
- `SUPERVISOR_EQUIPE`
- `CHEFE_GABINETE`

### Request
```json
{
  "responsavel_usuario_id": "uuid",
  "observacao": "Distribuição pela triagem"
}
```

---

## 8.7 POST `/demandas/{demanda_id}/repriorizar`
### Request
```json
{
  "prioridade": "CRITICA",
  "motivo": "Risco imediato relatado"
}
```

---

## 8.8 POST `/demandas/{demanda_id}/encaminhar`
### Request
```json
{
  "tipo": "JURIDICO",
  "destino_usuario_id": "uuid",
  "destino_texto": null,
  "descricao": "Necessário parecer jurídico"
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "demanda_id": "uuid",
    "tipo": "JURIDICO",
    "status": "ABERTO"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 8.9 POST `/demandas/{demanda_id}/concluir`
### Request
```json
{
  "observacao": "Demanda resolvida com encaminhamento externo concluído"
}
```

### Regras
- preenche `data_conclusao`
- gera histórico

---

## 8.10 POST `/demandas/{demanda_id}/reabrir`
### Request
```json
{
  "motivo_reabertura": "Problema retornou após atendimento inicial"
}
```

### Regras
- motivo obrigatório
- gera histórico

---

## 8.11 GET `/demandas/{demanda_id}/historico`
### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "acao": "STATUS_CHANGE",
      "status_anterior": "ABERTA",
      "status_novo": "EM_TRIAGEM",
      "observacao": "Triagem inicial",
      "created_at": "2026-04-16T10:10:00Z",
      "usuario": {
        "id": "uuid",
        "nome": "Carlos Lima"
      }
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 8.12 GET `/demandas/sem-responsavel`
### Perfis
- `SUPERVISOR_EQUIPE`
- `CHEFE_GABINETE`

### Query params
```text
?territorio_id=&categoria_id=&prioridade=
```

---

## 8.13 GET `/demandas/resumo-fila`
### Response 200
```json
{
  "data": {
    "abertas": 12,
    "em_triagem": 8,
    "em_atendimento": 20,
    "criticas": 4,
    "sla_vencido": 3
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 9. Módulo Agenda

## 9.1 GET `/agenda`
### Query params
```text
?date_from=&date_to=&tipo_agenda_id=&status=&territorio_id=&responsavel_usuario_id=&eh_agenda_vereador=
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "titulo": "Reunião com associação",
      "status": "CONFIRMADO",
      "data_inicio": "2026-04-17T14:00:00Z",
      "data_fim": "2026-04-17T15:00:00Z",
      "local_texto": "Associação do Centro",
      "territorio_id": "uuid",
      "responsavel_usuario_id": "uuid",
      "eh_agenda_vereador": true
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 9.2 POST `/agenda-eventos`
### Request
```json
{
  "territorio_id": "uuid",
  "tipo_agenda_id": "uuid",
  "demanda_id": null,
  "titulo": "Reunião com associação",
  "descricao": "Alinhamento institucional",
  "status": "PLANEJADO",
  "data_inicio": "2026-04-17T14:00:00Z",
  "data_fim": "2026-04-17T15:00:00Z",
  "local_texto": "Associação do Centro",
  "responsavel_usuario_id": "uuid",
  "eh_agenda_vereador": true,
  "participantes": [
    {
      "usuario_id": "uuid",
      "tipo_participante": "INTERNO"
    },
    {
      "cidadao_id": "uuid",
      "tipo_participante": "EXTERNO"
    }
  ]
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "titulo": "Reunião com associação",
    "status": "PLANEJADO"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 9.3 GET `/agenda-eventos/{evento_id}`
## 9.4 PUT `/agenda-eventos/{evento_id}`
## 9.5 PATCH `/agenda-eventos/{evento_id}/status`

### Exemplo Request status
```json
{
  "status": "REALIZADO"
}
```

---

## 9.6 POST `/agenda-eventos/{evento_id}/notificar`
### Request
```json
{
  "usuarios_ids": ["uuid-1", "uuid-2"]
}
```

### Response 202
```json
{
  "data": {
    "status": "NOTIFICACAO_ENFILEIRADA"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 9.7 GET `/agenda/vereador`
### Perfis
- `VEREADOR`
- `CHEFE_GABINETE`
- `ASSESSOR_ADMINISTRATIVO`

### Query params
```text
?date_from=&date_to=
```

---

## 9.8 GET `/agenda-eventos/{evento_id}/briefing`
### Response 200
```json
{
  "data": {
    "evento_id": "uuid",
    "titulo": "Reunião com associação",
    "resumo_contexto": "Evento institucional com pauta de mobilidade urbana.",
    "participantes": [
      {
        "nome": "Associação do Centro",
        "tipo": "EXTERNO"
      }
    ],
    "itens_relacionados": [
      {
        "tipo": "demanda",
        "id": "uuid",
        "titulo": "Solicitação sobre trânsito"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 10. Módulo Visitas de Campo

## 10.1 GET `/visitas-campo`
### Query params
```text
?date_from=&date_to=&territorio_id=&usuario_id=&equipe_id=&status=&page=1&page_size=20
```

## 10.2 POST `/visitas-campo`
### Request
```json
{
  "territorio_id": "uuid",
  "cidadao_id": "uuid",
  "usuario_id": "uuid",
  "tipo": "VISITA_DOMICILIAR",
  "status": "REALIZADA",
  "resultado": "ATENDIDO",
  "data_hora": "2026-04-16T09:00:00Z",
  "observacao": "Visita realizada com registro de demanda"
}
```

## 10.3 GET `/visitas-campo/{visita_id}`

---

# 11. Módulo Jurídico e Documental

## 11.1 GET `/documentos-juridicos`
### Query params
```text
?tipo=&status=&demanda_id=&autor_usuario_id=&date_from=&date_to=&page=1&page_size=20
```

### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "tipo": "PARECER",
      "titulo": "Parecer sobre demanda X",
      "status": "EM_REVISAO",
      "versao_atual": 2,
      "autor_usuario_id": "uuid",
      "demanda_id": "uuid"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 11.2 POST `/pareceres`
### Request
```json
{
  "demanda_id": "uuid",
  "protocolo_id": null,
  "projeto_id": null,
  "titulo": "Parecer sobre regularidade do pedido",
  "status": "RASCUNHO",
  "tema": "Regularidade administrativa",
  "ementa": "Análise preliminar",
  "conteudo_texto": "Texto inicial do parecer"
}
```

### Response 201
```json
{
  "data": {
    "id": "uuid-documento",
    "tipo": "PARECER",
    "titulo": "Parecer sobre regularidade do pedido",
    "status": "RASCUNHO",
    "versao_atual": 1
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 11.3 GET `/pareceres/{documento_id}`
## 11.4 PUT `/pareceres/{documento_id}`

### Exemplo PUT
```json
{
  "titulo": "Parecer revisado",
  "status": "EM_ELABORACAO",
  "tema": "Regularidade administrativa",
  "ementa": "Análise atualizada",
  "conteudo_texto": "Texto revisado"
}
```

---

## 11.5 POST `/pareceres/{documento_id}/nova-versao`
### Request
```json
{
  "conteudo_texto": "Nova versão do parecer",
  "resumo_alteracao": "Ajuste na fundamentação"
}
```

### Response 201
```json
{
  "data": {
    "documento_id": "uuid",
    "numero_versao": 2,
    "versao_atual": 2
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 11.6 POST `/pareceres/{documento_id}/enviar-revisao`
### Request
```json
{
  "responsavel_revisao_id": "uuid"
}
```

---

## 11.7 GET `/requerimentos`
## 11.8 POST `/requerimentos`
## 11.9 GET `/requerimentos/{documento_id}`
## 11.10 PUT `/requerimentos/{documento_id}`

### Exemplo POST
```json
{
  "titulo": "Requerimento de informações",
  "assunto": "Solicitação ao órgão X",
  "destinatario": "Secretaria Municipal",
  "status": "RASCUNHO",
  "conteudo_texto": "Texto do requerimento"
}
```

---

## 11.11 GET `/oficios`
## 11.12 POST `/oficios`
## 11.13 GET `/oficios/{documento_id}`
## 11.14 PUT `/oficios/{documento_id}`

### Exemplo POST
```json
{
  "titulo": "Ofício ao órgão Y",
  "destinatario": "Órgão Y",
  "assunto": "Encaminhamento institucional",
  "status": "RASCUNHO",
  "conteudo_texto": "Texto do ofício"
}
```

---

## 11.15 GET `/documentos/{documento_id}/versoes`
### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "numero_versao": 1,
      "resumo_alteracao": "Versão inicial",
      "created_at": "2026-04-16T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "numero_versao": 2,
      "resumo_alteracao": "Revisão de fundamentação",
      "created_at": "2026-04-16T11:00:00Z"
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 11.16 GET `/arquivo-juridico`
### Query params
```text
?search=&tipo=&status=&date_from=&date_to=&page=1&page_size=20
```

---

# 12. Módulo Administrativo

## 12.1 Protocolos

### GET `/protocolos`
### Query params
```text
?tipo_protocolo_id=&status=&responsavel_usuario_id=&date_from=&date_to=&page=1&page_size=20
```

### POST `/protocolos`
#### Request
```json
{
  "tipo_protocolo_id": "uuid",
  "documento_id": null,
  "numero": "2026-001",
  "titulo": "Protocolo administrativo X",
  "status": "REGISTRADO",
  "responsavel_usuario_id": "uuid",
  "prazo_final": "2026-04-20T18:00:00Z",
  "origem": "INTERNA",
  "observacoes": "Acompanhamento administrativo"
}
```

### GET `/protocolos/{protocolo_id}`
### PUT `/protocolos/{protocolo_id}`
### PATCH `/protocolos/{protocolo_id}/status`

#### Exemplo PATCH status
```json
{
  "status": "EM_TRAMITACAO"
}
```

---

## 12.2 Despachos

### POST `/protocolos/{protocolo_id}/despachos`
#### Request
```json
{
  "texto": "Encaminhar para análise complementar"
}
```

### GET `/protocolos/{protocolo_id}/despachos`

---

## 12.3 Tarefas

### GET `/tarefas`
### Query params
```text
?status=&responsavel_usuario_id=&prioridade=&date_from=&date_to=&page=1&page_size=20
```

### POST `/tarefas`
#### Request
```json
{
  "demanda_id": "uuid",
  "protocolo_id": null,
  "projeto_id": null,
  "titulo": "Retornar ligação para cidadã",
  "descricao": "Contato para atualização de andamento",
  "responsavel_usuario_id": "uuid",
  "prioridade": "MEDIA",
  "status": "ABERTA",
  "data_limite": "2026-04-18T18:00:00Z"
}
```

### GET `/tarefas/{tarefa_id}`
### PUT `/tarefas/{tarefa_id}`
### PATCH `/tarefas/{tarefa_id}/status`

#### Exemplo PATCH
```json
{
  "status": "CONCLUIDA"
}
```

---

## 12.4 Checklist

### GET `/tarefas/{tarefa_id}/checklist`
### GET `/protocolos/{protocolo_id}/checklist`
### POST `/checklists`

#### Request
```json
{
  "tarefa_id": "uuid",
  "descricao": "Confirmar retorno do cidadão",
  "ordem": 1
}
```

### PATCH `/checklists/{checklist_id}`
#### Request
```json
{
  "concluido": true
}
```

---

# 13. Módulo Projetos

## 13.1 GET `/projetos`
### Query params
```text
?status=&prioritario=&territorio_id=&responsavel_usuario_id=&page=1&page_size=20
```

### POST `/projetos`
#### Request
```json
{
  "territorio_id": "uuid",
  "nome": "Projeto Mobilidade Centro",
  "descricao": "Iniciativa para acompanhamento de pautas de mobilidade",
  "status": "PLANEJADO",
  "responsavel_usuario_id": "uuid",
  "prioritario": true,
  "data_inicio": "2026-04-20",
  "data_fim_prevista": "2026-06-30"
}
```

### GET `/projetos/{projeto_id}`
### PUT `/projetos/{projeto_id}`

---

## 13.2 POST `/projetos/{projeto_id}/etapas`
### Request
```json
{
  "nome": "Mapeamento inicial",
  "descricao": "Levantamento das demandas",
  "ordem": 1,
  "status": "PLANEJADO",
  "data_inicio": "2026-04-20",
  "data_fim_prevista": "2026-04-30",
  "responsavel_usuario_id": "uuid"
}
```

## 13.3 PATCH `/etapas/{etapa_id}/status`
### Request
```json
{
  "status": "EM_ANDAMENTO"
}
```

---

## 13.4 POST `/projetos/{projeto_id}/entregaveis`
### Request
```json
{
  "etapa_id": "uuid",
  "nome": "Relatório de diagnóstico",
  "descricao": "Documento consolidado",
  "status": "PENDENTE",
  "data_prevista": "2026-04-30"
}
```

---

## 13.5 POST `/projetos/{projeto_id}/riscos`
### Request
```json
{
  "descricao": "Baixa disponibilidade de dados",
  "nivel": "MEDIO",
  "status": "ABERTO",
  "plano_acao": "Solicitar base complementar",
  "responsavel_usuario_id": "uuid"
}
```

---

## 13.6 GET `/projetos/{projeto_id}/indicadores`
### Response 200
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Demandas mapeadas",
      "unidade": "un",
      "meta": 100,
      "valor_atual": 45,
      "data_referencia": "2026-04-16"
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 14. Módulo Territorial

## 14.1 GET `/territorial/dashboard`
### Query params
```text
?date_from=&date_to=&regiao_id=&bairro_id=&microarea_id=&tema=
```

### Response 200
```json
{
  "data": {
    "cards": {
      "quantidade_demandas": 120,
      "quantidade_visitas": 55,
      "quantidade_eventos": 8,
      "tempo_medio_atendimento_horas": 36.5
    },
    "mapa": [
      {
        "territorio_id": "uuid",
        "territorio_nome": "Centro",
        "quantidade_demandas": 50
      }
    ],
    "temas": [
      {
        "tema": "mobilidade urbana",
        "quantidade": 20
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regra crítica
- somente dados agregados
- sem perfilamento individual sensível

---

## 14.2 GET `/territorial/cobertura-equipes`
### Query params
```text
?date_from=&date_to=&territorio_id=&equipe_id=&usuario_id=
```

### Response 200
```json
{
  "data": [
    {
      "territorio_id": "uuid",
      "equipe_id": "uuid",
      "usuario_id": "uuid",
      "quantidade_visitas": 10,
      "quantidade_registros": 25,
      "quantidade_demandas": 8
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 14.3 GET `/territorial/tendencias`
### Query params
```text
?date_from=&date_to=&territorio_id=&tema=
```

### Response 200
```json
{
  "data": [
    {
      "tema": "mobilidade urbana",
      "territorios": ["Centro", "São João"],
      "quantidade_demandas": 32,
      "evolucao_percentual": 12.5
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 14.4 GET `/eventos-territoriais`
## 14.5 POST `/eventos-territoriais`

### Exemplo POST
```json
{
  "territorio_id": "uuid",
  "tipo": "EVENTO_COMUNITARIO",
  "titulo": "Reunião aberta no bairro",
  "descricao": "Evento institucional comunitário",
  "data_evento": "2026-04-21T19:00:00Z",
  "usuario_responsavel_id": "uuid",
  "publico_estimado": 80
}
```

---

# 15. Módulo Relatórios

## 15.1 GET `/relatorios/catalogo`
### Response 200
```json
{
  "data": [
    {
      "codigo": "operacional",
      "nome": "Relatório Operacional",
      "categorias": ["OPERACIONAL"],
      "formatos": ["json", "pdf", "xlsx"]
    },
    {
      "codigo": "executivo",
      "nome": "Relatório Executivo",
      "categorias": ["EXECUTIVO"],
      "formatos": ["json", "pdf"]
    }
  ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 15.2 GET `/relatorios/operacional`
### Query params
```text
?date_from=&date_to=&territorio_id=&responsavel_usuario_id=&categoria_id=&format=json
```

## 15.3 GET `/relatorios/juridico`
## 15.4 GET `/relatorios/territorial`
## 15.5 GET `/relatorios/executivo`

### Exemplo Response operacional
```json
{
  "data": {
    "resumo": {
      "demandas_abertas": 20,
      "demandas_concluidas": 15,
      "tempo_medio_horas": 42.3
    },
    "itens": []
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 15.6 GET `/relatorios/{codigo}/export`
### Query params
```text
?format=pdf
```

### Response 202
```json
{
  "data": {
    "job_id": "uuid",
    "status": "PROCESSANDO"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

# 16. Módulo Uploads

## 16.1 POST `/uploads`
### Content-Type
`multipart/form-data`

### Campos
- `file`
- `contexto` opcional

### Response 201
```json
{
  "data": {
    "id": "uuid",
    "nome_original": "arquivo.pdf",
    "mime_type": "application/pdf",
    "tamanho_bytes": 120044,
    "url_storage": "storage/path/arquivo.pdf"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- validar extensão/tamanho
- registrar metadados
- não vincula automaticamente a uma entidade sem endpoint específico

---

# 17. Módulo Mobile Sync

## 17.1 POST `/mobile/sync`
### Objetivo
Receber lote de registros do app com idempotência.

### Request
```json
{
  "items": [
    {
      "client_generated_id": "mob-123",
      "entidade": "contato",
      "payload": {
        "territorio_id": "uuid",
        "origem_cadastro": "MOBILE_CAMPO",
        "nome": "Maria da Silva",
        "telefone_principal": "31999999999"
      }
    },
    {
      "client_generated_id": "mob-124",
      "entidade": "demanda",
      "payload": {
        "cidadao_id": "uuid",
        "territorio_id": "uuid",
        "titulo": "Demanda de campo",
        "descricao": "Descrição",
        "prioridade": "MEDIA",
        "origem_cadastro": "MOBILE_CAMPO"
      }
    }
  ]
}
```

### Response 200
```json
{
  "data": {
    "processed": [
      {
        "client_generated_id": "mob-123",
        "entidade": "contato",
        "entidade_id": "uuid",
        "status": "PROCESSADO"
      }
    ],
    "errors": [
      {
        "client_generated_id": "mob-124",
        "entidade": "demanda",
        "status": "ERRO",
        "message": "Contato fora do escopo permitido."
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regras
- idempotência por `client_generated_id`
- processar item a item
- retorno granular

---

# 18. Módulo IA Assistiva

## 18.0 GET `/political-os/overview`
### Objetivo
Retornar o overview executivo consumido pelo painel principal, com cards, fila de SLA, heatmap territorial, sentimento agregado, emendas, legislativo e alertas acionáveis.

### Response 200
```json
{
  "data": {
    "cards": {
      "demandas_abertas": 3,
      "sla_em_risco": 0,
      "sla_vencido": 2,
      "contatos": 15,
      "liderancas": 3,
      "engajamento_forte": 3,
      "agenda_pendente": 0,
      "oficios_pendentes": 2
    },
    "heatmap": [
      {
        "territorio_id": "uuid",
        "territorio_nome": "Centro",
        "demandas": 3,
        "contatos": 10,
        "liderancas": 3,
        "score": 22,
        "nivel_pressao": "ALTA"
      }
    ],
    "emendas": {
      "valor_indicado": 350000,
      "valor_aprovado": 250000,
      "valor_empenhado": 230000,
      "aprovadas": 2,
      "empenhadas": 2,
      "ultima_data_empenho": "2026-04-17T04:55:22Z"
    },
    "alertas": [
      {
        "tipo": "OFICIO",
        "titulo": "Solicitacao de vistoria e poda preventiva",
        "descricao": "Cobrar Secretaria Municipal de Meio Ambiente hoje. 26d sem resposta.",
        "action": "open-office",
        "entity_id": "uuid",
        "section": "oficios",
        "filtro_contexto": "pending-offices",
        "territorio_id": "uuid",
        "territorio_nome": "Centro"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-20T10:00:00Z"
  }
}
```

### Regras
- `heatmap[].nivel_pressao` sintetiza o score territorial em leitura executiva `BAIXA`, `MEDIA` ou `ALTA`
- `alertas[].filtro_contexto` ajuda a IA e o front a preservar a origem decisória do alerta, como `sla-overdue`, `sla-risk`, `pending-offices` ou `amendments`
- `alertas[].territorio_id` e `alertas[].territorio_nome` permitem cruzar o alerta com território sem recomputar contexto no cliente
- `emendas` resume apenas captação política: valor pleiteado, valor aprovado, valor empenhado, beneficiário e data de empenho
- o sistema não acompanha execução final da emenda; liquidação, pagamento e entrega ficam fora deste módulo

## 18.1 GET `/sentimento-social/resumo`
### Objetivo
Retornar um resumo agregado de sentimento público para o gabinete, com filtros opcionais por canal, período e território, sem recarregar o overview executivo completo.

### Query params
```text
?canal=INSTAGRAM&periodo=24H&territorio=Centro
```

### Response 200
```json
{
  "data": {
    "positivo": 54,
    "neutro": 31,
    "negativo": 15,
    "alerta": "Comentarios cobram retorno rapido em bairros com maior volume de demandas.",
    "tema": "Zeladoria urbana",
    "canal": "INSTAGRAM",
    "periodo": "24H",
    "coletado_em": "2026-04-20T11:25:00Z",
    "amostras": 1,
    "canais": [
      {
        "canal": "INSTAGRAM",
        "quantidade": 1
      }
    ],
    "periodos": [
      {
        "periodo": "24H",
        "quantidade": 1
      }
    ],
    "territorios": [
      {
        "territorio": "Centro",
        "quantidade": 1
      }
    ],
    "filtros_aplicados": {
      "canal": "INSTAGRAM",
      "periodo": "24H",
      "territorio": "Centro"
    }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-20T10:00:00Z"
  }
}
```

### Regras
- se o filtro nao encontrar amostras, o backend preserva o conjunto original para evitar painel vazio
- a resposta expõe buckets auxiliares para montar combos e rankings de canal, período e território

## 18.2 POST `/ai/contexto-operacional`
### Request
```json
{
  "contexto_tipo": "demanda",
  "contexto_id": "uuid",
  "modulo": "atendimento",
  "origem": "fila"
}
```

### Response 200
```json
{
  "data": {
    "titulo": "IA: Atendimento",
    "subtitulo": "Joao da Silva - Centro",
    "resumo": "Consulta especializada. ALTA | EM_TRIAGEM | 2 dia(s). Territorio Centro; responsavel nao atribuido. Defina responsavel e proximo passo.",
    "contexto": {
      "tipo": "demanda",
      "id": "uuid",
      "modulo": "atendimento",
      "origem": "fila",
      "rotulo": "Consulta especializada",
      "filtro": null,
      "canal": null,
      "periodo": null,
      "territorio": "Centro"
    },
    "sugestoes": [
      {
        "titulo": "Atribuir responsavel",
        "descricao": "Sem dono interno, a fila tende a perder prazo e rastreabilidade.",
        "label": "Definir responsavel",
        "action": "focus-demand-assignee",
        "section": "atendimento",
        "entity_id": "uuid"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-20T10:00:00Z"
  }
}
```

### Regra crítica
- a IA organiza contexto e fluxo manual, mas não altera estado automaticamente
- `contexto_tipo` agora pode representar tambem leituras de `territorio` e `sentimento`, permitindo que cards, heatmap e sinais de humor publico virem fluxos orientados por contexto

### Exemplo adicional: leitura territorial
```json
{
  "contexto_tipo": "territorio",
  "contexto_id": "uuid-bairro-centro",
  "modulo": "executivo",
  "origem": "heatmap",
  "filtro": "Centro"
}
```

### Comportamento adicional em heatmap e alertas
- quando `origem = heatmap`, o resumo territorial explicita `nivel_pressao` e orienta priorização local
- quando `origem = alerta`, o resumo fica mais curto e orientado à decisão, preservando `filtro` e território do item acionado
- o objeto `contexto` pode retornar `territorio`, `canal` e `periodo` já resolvidos para o front não recomputar esse escopo

### Exemplo adicional: leitura de sentimento
```json
{
  "contexto_tipo": "sentimento",
  "modulo": "executivo",
  "origem": "sentimento",
  "filtro": "negative",
  "canal": "INSTAGRAM",
  "periodo": "24H",
  "territorio": "Centro"
}
```

### Comportamento adicional no contexto de sentimento
- `canal`, `periodo` e `territorio` refinam o recorte analisado pela IA assistiva
- o `subtitulo` do contexto passa a refletir o escopo ativo, por exemplo `INSTAGRAM | 24H | Centro`
- o `resumo` menciona explicitamente o recorte ativo para manter rastreabilidade operacional

---

## 18.3 POST `/ai/resumir-contexto`
### Request
```json
{
  "contexto_tipo": "demanda",
  "contexto_id": "uuid",
  "modulo": "atendimento",
  "origem": "fila"
}
```

### Response 200
```json
{
  "data": {
    "resumo": "Consulta especializada. ALTA | EM_TRIAGEM | 2 dia(s). Territorio Centro; responsavel nao atribuido. Defina responsavel e proximo passo."
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

---

## 18.4 POST `/ai/sugerir-proxima-etapa`
### Request
```json
{
  "contexto_tipo": "demanda",
  "contexto_id": "uuid",
  "modulo": "atendimento",
  "origem": "fila"
}
```

### Response 200
```json
{
  "data": {
    "sugestao": "Encaminhar ao assessor jurídico para análise documental.",
    "justificativa": "Há anexos e histórico apontando necessidade formal."
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-16T10:00:00Z"
  }
}
```

### Regra crítica
- sugestão nunca altera estado automaticamente

---

## 18.5 POST `/ai/resumir-documento`
## 18.6 POST `/ai/alertas-risco`

---

# 19. Matriz resumida de autorização por módulo

## Auth
- todos autenticáveis conforme perfil ativo

## Administração
- somente `CHEFE_GABINETE`

## Territórios
- leitura: vários perfis operacionais
- escrita: `CHEFE_GABINETE`, `ASSESSOR_ADMINISTRATIVO`

## Contatos
- criação: campo, assessor, supervisor
- edição ampla: assessor, chefe
- leitura restrita por escopo

## Demandas
- criação: campo, assessor, supervisor
- triagem/distribuição: supervisor, chefe
- conclusão/reabertura: perfis autorizados no fluxo

## Agenda
- operacional: assessor, administrativo, chefe
- visão executiva: vereador, chefe

## Jurídico
- principal: `ASSESSOR_JURIDICO`
- leitura resumida: `CHEFE_GABINETE`, `VEREADOR`

## Administrativo
- principal: `ASSESSOR_ADMINISTRATIVO`, `CHEFE_GABINETE`

## Projetos
- chefe, assessor nível 1, vereador em leitura executiva

## Territorial
- supervisor, chefe, vereador
- sempre agregado

## IA
- assistiva, nunca decisória automática

---

# 20. Erros de negócio recomendados

## `CONTACT_DUPLICATE`
Quando CPF já existir ou duplicidade forte detectada.

## `OUT_OF_SCOPE`
Quando o usuário tenta acessar ou alterar recurso fora do escopo.

## `INVALID_STATUS_TRANSITION`
Quando a transição de status não é permitida.

## `SLA_POLICY_NOT_FOUND`
Quando categoria/prioridade exige SLA e não há configuração.

## `TERRITORY_HIERARCHY_INVALID`
Quando hierarquia territorial for inconsistente.

## `DOCUMENT_VERSION_CONFLICT`
Quando houver conflito de versionamento documental.

## `MOBILE_SYNC_DUPLICATE`
Quando item mobile já tiver sido processado.

---

# 21. Ordem sugerida de implementação das APIs

## Fase 1
- `auth`
- `usuarios`
- `equipes`
- `territorios`
- `contatos`
- `consentimentos`

## Fase 2
- `demandas`
- `historico_demanda`
- `encaminhamentos`
- `mobile/sync`

## Fase 3
- `agenda`
- `visitas-campo`
- `tarefas`
- `checklists`

## Fase 4
- `protocolos`
- `despachos`
- `documentos-juridicos`
- `pareceres`
- `requerimentos`
- `oficios`

## Fase 5
- `projetos`
- `territorial`
- `relatorios`
- `uploads`
- `ai`

---

# 22. Próximo passo natural

A continuação mais útil deste documento é uma destas duas:
1. transformar estes contratos em **OpenAPI/Swagger schema base**;
2. quebrar as APIs em **épicos técnicos + tasks backend/frontend** por sprint.

