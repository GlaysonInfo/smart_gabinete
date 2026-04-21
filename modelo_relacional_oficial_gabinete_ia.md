# Modelo relacional oficial — GESTÃO DE MANDATOS / GABINETE IA

## 1. Objetivo do documento

Definir o **modelo relacional oficial** do sistema **GABINETE IA**, tabela por tabela, com foco em:
- estrutura persistente do produto
- relações entre domínios
- constraints e integridade
- índices recomendados
- regras de segregação por perfil e escopo
- base para migrações, APIs e relatórios

Este sistema é **independente do REVISA**, com banco próprio e sem compartilhamento de schema.

---

# 2. Premissas de modelagem

## 2.1 Estratégia geral
- Banco principal: **PostgreSQL**
- Geodados futuros: **PostGIS**
- IDs primários: **UUID**
- Datas de auditoria: `created_at`, `updated_at`
- Exclusão lógica preferencial: `ativo` ou `status`
- Toda entidade sensível deve suportar auditoria
- Entidades documentais devem suportar versionamento

## 2.2 Escopo lógico
Cada instância lógica do sistema opera sobre um **gabinete**, portanto a maior parte das tabelas terá `gabinete_id`.

## 2.3 Padrão de campos base
Sempre que fizer sentido, usar:
- `id UUID PRIMARY KEY`
- `gabinete_id UUID NOT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL`
- `updated_by UUID NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## 2.4 Domínios principais
- identidade e acesso
- cadastros e territórios
- cidadãos/contatos e consentimento
- atendimento e demanda
- agenda
- jurídico e documental
- administrativo
- projetos do mandato
- territorial agregado
- arquivos, auditoria e integrações

---

# 3. Convenções de tipos e enums

## 3.1 Enums recomendados no banco

### perfil_usuario
- `COLABORADOR_EXTERNO`
- `SUPERVISOR_EQUIPE`
- `ASSESSOR_NIVEL_1`
- `ASSESSOR_JURIDICO`
- `ASSESSOR_ADMINISTRATIVO`
- `CHEFE_GABINETE`
- `VEREADOR`

### status_contato
- `ATIVO`
- `INATIVO`
- `PENDENTE_VALIDACAO`
- `DUPLICIDADE_SUSPEITA`

### status_demanda
- `ABERTA`
- `EM_TRIAGEM`
- `EM_ATENDIMENTO`
- `ENCAMINHADA`
- `AGUARDANDO_RETORNO`
- `CONCLUIDA`
- `SUSPENSA`
- `CANCELADA`
- `REABERTA`

### prioridade_demanda
- `BAIXA`
- `MEDIA`
- `ALTA`
- `CRITICA`

### status_visita
- `PLANEJADA`
- `REALIZADA`
- `NAO_REALIZADA`
- `REAGENDADA`
- `CANCELADA`

### status_agenda
- `PLANEJADO`
- `CONFIRMADO`
- `EM_ANDAMENTO`
- `REALIZADO`
- `CANCELADO`
- `REAGENDADO`

### status_tarefa
- `ABERTA`
- `EM_EXECUCAO`
- `BLOQUEADA`
- `CONCLUIDA`
- `CANCELADA`

### status_documento
- `RASCUNHO`
- `EM_ELABORACAO`
- `EM_REVISAO`
- `APROVADO`
- `PROTOCOLADO`
- `ARQUIVADO`
- `CANCELADO`

### tipo_documento
- `PARECER`
- `REQUERIMENTO`
- `OFICIO`
- `MINUTA`
- `ANEXO_OPERACIONAL`
- `OUTRO`

### status_protocolo
- `REGISTRADO`
- `EM_TRAMITACAO`
- `PENDENTE`
- `CONCLUIDO`
- `ARQUIVADO`

### status_projeto
- `PLANEJADO`
- `EM_ANDAMENTO`
- `PAUSADO`
- `CONCLUIDO`
- `CANCELADO`

### nivel_risco
- `BAIXO`
- `MEDIO`
- `ALTO`
- `CRITICO`

### tipo_territorio
- `REGIAO`
- `BAIRRO`
- `MICROAREA`

### origem_cadastro
- `MOBILE_CAMPO`
- `WEB_INTERNO`
- `IMPORTACAO`
- `INTEGRACAO`

### canal_contato
- `TELEFONE`
- `WHATSAPP`
- `EMAIL`
- `OUTRO`

### tipo_encaminhamento
- `INTERNO`
- `JURIDICO`
- `ADMINISTRATIVO`
- `EXTERNO`

---

# 4. Diagrama conceitual resumido

```text
GABINETE
 ├── USUARIO
 │    ├── USUARIO_ESCOPO
 │    └── EQUIPE
 ├── TERRITORIO
 ├── CIDADAO_CONTATO
 │    ├── CONSENTIMENTO_CONTATO
 │    ├── CONTATO_CANAL
 │    ├── DEMANDA
 │    │    ├── HISTORICO_DEMANDA
 │    │    ├── ENCAMINHAMENTO
 │    │    ├── DEMANDA_ANEXO
 │    │    └── DEMANDA_TAG
 │    ├── VISITA_CAMPO
 │    └── AGENDA_EVENTO
 ├── ORGANIZACAO
 ├── LIDERANCA_COMUNITARIA
 ├── AGENDA_EVENTO
 │    └── AGENDA_PARTICIPANTE
 ├── DOCUMENTO
 │    ├── DOCUMENTO_VERSAO
 │    ├── PARECER_JURIDICO
 │    ├── REQUERIMENTO
 │    └── OFICIO
 ├── PROTOCOLO
 │    ├── RITO
 │    ├── PRAZO
 │    ├── CHECKLIST
 │    └── DESPACHO
 ├── TAREFA
 ├── PROJETO
 │    ├── ETAPA_PROJETO
 │    ├── ENTREGAVEL
 │    ├── INDICADOR_PROJETO
 │    └── RISCO_PROJETO
 ├── EVENTO_TERRITORIAL
 ├── COBERTURA_EQUIPE
 ├── INDICADOR_TERRITORIAL_AGREGADO
 ├── ARQUIVO_UPLOAD
 ├── AUDITORIA
 └── INTEGRACAO_EVENTO
```

---

# 5. Domínio identidade e acesso

# 5.1 Tabela `gabinete`
## Finalidade
Representa a unidade lógica do sistema.

## Campos
- `id UUID PK`
- `nome VARCHAR(150) NOT NULL`
- `sigla VARCHAR(50) NULL`
- `descricao TEXT NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `nome` obrigatório

## Índices
- `idx_gabinete_ativo (ativo)`

---

# 5.2 Tabela `equipe`
## Finalidade
Agrupa usuários operacionais, especialmente campo e supervisão.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(150) NOT NULL`
- `descricao TEXT NULL`
- `supervisor_usuario_id UUID NULL FK -> usuario(id)`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (gabinete_id, nome)`

## Índices
- `idx_equipe_gabinete (gabinete_id)`
- `idx_equipe_supervisor (supervisor_usuario_id)`

---

# 5.3 Tabela `usuario`
## Finalidade
Armazena usuários do sistema.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `equipe_id UUID NULL FK -> equipe(id)`
- `nome VARCHAR(150) NOT NULL`
- `email_login VARCHAR(150) NOT NULL`
- `telefone VARCHAR(20) NULL`
- `senha_hash TEXT NOT NULL`
- `perfil perfil_usuario NOT NULL`
- `ultimo_login TIMESTAMP NULL`
- `mfa_habilitado BOOLEAN NOT NULL DEFAULT FALSE`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`
- `updated_by UUID NULL FK -> usuario(id)`

## Constraints
- `UNIQUE (email_login)`
- `CHECK (nome <> '')`

## Índices
- `idx_usuario_gabinete (gabinete_id)`
- `idx_usuario_perfil (perfil)`
- `idx_usuario_equipe (equipe_id)`
- `idx_usuario_ativo (ativo)`

---

# 5.4 Tabela `usuario_escopo`
## Finalidade
Define escopo territorial e funcional do usuário.

## Campos
- `id UUID PK`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `equipe_id UUID NULL FK -> equipe(id)`
- `escopo_tipo VARCHAR(50) NOT NULL`
- `escopo_valor VARCHAR(100) NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Regras
- pode haver múltiplos escopos por usuário
- usado para filtrar territorial, equipe e domínio específico

## Índices
- `idx_usuario_escopo_usuario (usuario_id)`
- `idx_usuario_escopo_territorio (territorio_id)`
- `idx_usuario_escopo_equipe (equipe_id)`

---

# 5.5 Tabela `sessao_usuario` (opcional)
## Finalidade
Controle de sessões, refresh tokens e dispositivos.

## Campos
- `id UUID PK`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `refresh_token_hash TEXT NOT NULL`
- `device_info TEXT NULL`
- `ip_origem VARCHAR(64) NULL`
- `expira_em TIMESTAMP NOT NULL`
- `revogada BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

---

# 6. Domínio territorial e cadastros base

# 6.1 Tabela `territorio`
## Finalidade
Hierarquia territorial do gabinete.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `parent_id UUID NULL FK -> territorio(id)`
- `nome VARCHAR(150) NOT NULL`
- `tipo tipo_territorio NOT NULL`
- `codigo_externo VARCHAR(50) NULL`
- `geom GEOMETRY NULL` *(PostGIS futuro)*
- `centroide GEOMETRY NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (gabinete_id, parent_id, nome, tipo)`
- regra de árvore válida na aplicação ou trigger

## Índices
- `idx_territorio_gabinete (gabinete_id)`
- `idx_territorio_parent (parent_id)`
- `idx_territorio_tipo (tipo)`
- índice espacial quando houver PostGIS

---

# 6.2 Tabela `organizacao`
## Finalidade
Cadastro de organizações, associações, grupos e entidades.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `nome VARCHAR(200) NOT NULL`
- `tipo VARCHAR(80) NOT NULL`
- `telefone VARCHAR(20) NULL`
- `email VARCHAR(150) NULL`
- `endereco TEXT NULL`
- `observacoes TEXT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'ATIVO'`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_organizacao_gabinete (gabinete_id)`
- `idx_organizacao_territorio (territorio_id)`
- `idx_organizacao_tipo (tipo)`

---

# 6.3 Tabela `lideranca_comunitaria`
## Finalidade
Cadastro institucional de lideranças comunitárias, sem perfilamento eleitoral individual.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `organizacao_id UUID NULL FK -> organizacao(id)`
- `nome VARCHAR(150) NOT NULL`
- `telefone VARCHAR(20) NULL`
- `email VARCHAR(150) NULL`
- `tema_principal VARCHAR(100) NULL`
- `observacoes TEXT NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_lideranca_gabinete (gabinete_id)`
- `idx_lideranca_territorio (territorio_id)`
- `idx_lideranca_organizacao (organizacao_id)`

---

# 7. Domínio cidadãos/contatos

# 7.1 Tabela `cidadao_contato`
## Finalidade
Entidade central de relacionamento institucional.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `origem_cadastro origem_cadastro NOT NULL`
- `nome VARCHAR(150) NOT NULL`
- `cpf VARCHAR(14) NULL`
- `data_nascimento DATE NULL`
- `telefone_principal VARCHAR(20) NULL`
- `telefone_secundario VARCHAR(20) NULL`
- `email VARCHAR(150) NULL`
- `logradouro TEXT NULL`
- `numero VARCHAR(20) NULL`
- `complemento VARCHAR(100) NULL`
- `bairro VARCHAR(100) NULL`
- `cidade VARCHAR(100) NULL`
- `cep VARCHAR(10) NULL`
- `tipo_contato VARCHAR(50) NOT NULL DEFAULT 'CIDADAO'`
- `status status_contato NOT NULL DEFAULT 'ATIVO'`
- `duplicidade_suspeita BOOLEAN NOT NULL DEFAULT FALSE`
- `observacoes TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`
- `updated_by UUID NULL FK -> usuario(id)`

## Constraints
- `UNIQUE (cpf)` parcial quando `cpf IS NOT NULL`

## Índices
- `idx_contato_gabinete (gabinete_id)`
- `idx_contato_territorio (territorio_id)`
- `idx_contato_nome (nome)`
- `idx_contato_telefone (telefone_principal)`
- `idx_contato_status (status)`
- `idx_contato_duplicidade (duplicidade_suspeita)`

---

# 7.2 Tabela `contato_canal`
## Finalidade
Armazena canais extras do contato.

## Campos
- `id UUID PK`
- `cidadao_id UUID NOT NULL FK -> cidadao_contato(id)`
- `canal canal_contato NOT NULL`
- `valor VARCHAR(150) NOT NULL`
- `principal BOOLEAN NOT NULL DEFAULT FALSE`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- opcionalmente `UNIQUE (cidadao_id, canal, valor)`

## Índices
- `idx_contato_canal_cidadao (cidadao_id)`
- `idx_contato_canal_tipo (canal)`

---

# 7.3 Tabela `consentimento_contato`
## Finalidade
Registra consentimentos e finalidades de contato.

## Campos
- `id UUID PK`
- `cidadao_id UUID NOT NULL FK -> cidadao_contato(id)`
- `canal canal_contato NOT NULL`
- `consentido BOOLEAN NOT NULL`
- `finalidade VARCHAR(150) NOT NULL`
- `forma_registro VARCHAR(50) NULL`
- `observacao TEXT NULL`
- `registrado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `registrado_por UUID NULL FK -> usuario(id)`

## Índices
- `idx_consentimento_cidadao (cidadao_id)`
- `idx_consentimento_canal (canal)`
- `idx_consentimento_finalidade (finalidade)`

---

# 7.4 Tabela `contato_tag`
## Finalidade
Tags operacionais neutras para classificação interna.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(80) NOT NULL`
- `cor VARCHAR(20) NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Constraints
- `UNIQUE (gabinete_id, nome)`

---

# 7.5 Tabela `contato_tag_rel`
## Finalidade
Relaciona contato a tags operacionais.

## Campos
- `id UUID PK`
- `cidadao_id UUID NOT NULL FK -> cidadao_contato(id)`
- `tag_id UUID NOT NULL FK -> contato_tag(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (cidadao_id, tag_id)`

---

# 8. Domínio atendimento e demanda

# 8.1 Tabela `categoria_demanda`
## Finalidade
Catálogo configurável de categorias.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(100) NOT NULL`
- `descricao TEXT NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Constraints
- `UNIQUE (gabinete_id, nome)`

---

# 8.2 Tabela `demanda`
## Finalidade
Entidade principal do atendimento.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `cidadao_id UUID NULL FK -> cidadao_contato(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `categoria_id UUID NULL FK -> categoria_demanda(id)`
- `titulo VARCHAR(200) NOT NULL`
- `descricao TEXT NOT NULL`
- `prioridade prioridade_demanda NOT NULL DEFAULT 'MEDIA'`
- `status status_demanda NOT NULL DEFAULT 'ABERTA'`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `origem_cadastro origem_cadastro NOT NULL`
- `data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `sla_data TIMESTAMP NULL`
- `data_conclusao TIMESTAMP NULL`
- `motivo_reabertura TEXT NULL`
- `motivo_cancelamento TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`
- `updated_by UUID NULL FK -> usuario(id)`

## Constraints
- `CHECK (titulo <> '')`
- `CHECK (descricao <> '')`

## Índices
- `idx_demanda_gabinete (gabinete_id)`
- `idx_demanda_cidadao (cidadao_id)`
- `idx_demanda_territorio (territorio_id)`
- `idx_demanda_categoria (categoria_id)`
- `idx_demanda_status (status)`
- `idx_demanda_prioridade (prioridade)`
- `idx_demanda_responsavel (responsavel_usuario_id)`
- `idx_demanda_sla (sla_data)`
- índice composto: `(status, prioridade, sla_data)`

---

# 8.3 Tabela `historico_demanda`
## Finalidade
Linha do tempo da demanda.

## Campos
- `id UUID PK`
- `demanda_id UUID NOT NULL FK -> demanda(id)`
- `usuario_id UUID NULL FK -> usuario(id)`
- `acao VARCHAR(80) NOT NULL`
- `status_anterior status_demanda NULL`
- `status_novo status_demanda NULL`
- `observacao TEXT NULL`
- `dados_json JSONB NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_hist_demanda_demanda (demanda_id)`
- `idx_hist_demanda_usuario (usuario_id)`
- `idx_hist_demanda_data (created_at)`

---

# 8.4 Tabela `encaminhamento`
## Finalidade
Encaminhamento interno, jurídico, administrativo ou externo.

## Campos
- `id UUID PK`
- `demanda_id UUID NOT NULL FK -> demanda(id)`
- `tipo tipo_encaminhamento NOT NULL`
- `destino_usuario_id UUID NULL FK -> usuario(id)`
- `destino_texto VARCHAR(150) NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'ABERTO'`
- `descricao TEXT NOT NULL`
- `data_encaminhamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `data_retorno TIMESTAMP NULL`
- `created_by UUID NULL FK -> usuario(id)`

## Índices
- `idx_encaminhamento_demanda (demanda_id)`
- `idx_encaminhamento_destino (destino_usuario_id)`
- `idx_encaminhamento_status (status)`

---

# 8.5 Tabela `demanda_tag`
## Finalidade
Tags operacionais para a demanda.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(80) NOT NULL`
- `cor VARCHAR(20) NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Constraints
- `UNIQUE (gabinete_id, nome)`

---

# 8.6 Tabela `demanda_tag_rel`
## Finalidade
Relaciona demanda a tags.

## Campos
- `id UUID PK`
- `demanda_id UUID NOT NULL FK -> demanda(id)`
- `tag_id UUID NOT NULL FK -> demanda_tag(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (demanda_id, tag_id)`

---

# 8.7 Tabela `demanda_anexo`
## Finalidade
Vincula uploads à demanda.

## Campos
- `id UUID PK`
- `demanda_id UUID NOT NULL FK -> demanda(id)`
- `arquivo_id UUID NOT NULL FK -> arquivo_upload(id)`
- `tipo VARCHAR(50) NULL`
- `descricao TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`

## Constraints
- `UNIQUE (demanda_id, arquivo_id)`

---

# 8.8 Tabela `visita_campo`
## Finalidade
Histórico de visita e atividade de campo.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NOT NULL FK -> territorio(id)`
- `cidadao_id UUID NULL FK -> cidadao_contato(id)`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `tipo VARCHAR(50) NOT NULL`
- `status status_visita NOT NULL DEFAULT 'PLANEJADA'`
- `resultado VARCHAR(50) NULL`
- `data_hora TIMESTAMP NOT NULL`
- `observacao TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_visita_gabinete (gabinete_id)`
- `idx_visita_territorio (territorio_id)`
- `idx_visita_usuario (usuario_id)`
- `idx_visita_cidadao (cidadao_id)`
- `idx_visita_data (data_hora)`

---

# 9. Domínio agenda

# 9.1 Tabela `tipo_agenda`
## Finalidade
Catálogo de tipos de agenda.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(80) NOT NULL`
- `cor VARCHAR(20) NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Constraints
- `UNIQUE (gabinete_id, nome)`

---

# 9.2 Tabela `agenda_evento`
## Finalidade
Compromissos, reuniões, visitas, agendas institucionais.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `tipo_agenda_id UUID NULL FK -> tipo_agenda(id)`
- `demanda_id UUID NULL FK -> demanda(id)`
- `titulo VARCHAR(200) NOT NULL`
- `descricao TEXT NULL`
- `status status_agenda NOT NULL DEFAULT 'PLANEJADO'`
- `data_inicio TIMESTAMP NOT NULL`
- `data_fim TIMESTAMP NOT NULL`
- `local_texto VARCHAR(200) NULL`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `eh_agenda_vereador BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`
- `updated_by UUID NULL FK -> usuario(id)`

## Constraints
- `CHECK (data_fim >= data_inicio)`

## Índices
- `idx_agenda_gabinete (gabinete_id)`
- `idx_agenda_territorio (territorio_id)`
- `idx_agenda_tipo (tipo_agenda_id)`
- `idx_agenda_status (status)`
- `idx_agenda_inicio (data_inicio)`
- `idx_agenda_responsavel (responsavel_usuario_id)`
- `idx_agenda_vereador (eh_agenda_vereador)`

---

# 9.3 Tabela `agenda_participante`
## Finalidade
Participantes internos e externos do evento.

## Campos
- `id UUID PK`
- `agenda_evento_id UUID NOT NULL FK -> agenda_evento(id)`
- `usuario_id UUID NULL FK -> usuario(id)`
- `cidadao_id UUID NULL FK -> cidadao_contato(id)`
- `nome_externo VARCHAR(150) NULL`
- `tipo_participante VARCHAR(30) NOT NULL`
- `confirmado BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- pelo menos um entre `usuario_id`, `cidadao_id` ou `nome_externo`

## Índices
- `idx_agenda_participante_evento (agenda_evento_id)`
- `idx_agenda_participante_usuario (usuario_id)`
- `idx_agenda_participante_cidadao (cidadao_id)`

---

# 9.4 Tabela `lembrete_agenda`
## Finalidade
Lembretes configuráveis dos eventos.

## Campos
- `id UUID PK`
- `agenda_evento_id UUID NOT NULL FK -> agenda_evento(id)`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `minutos_antes INTEGER NOT NULL`
- `canal VARCHAR(30) NOT NULL`
- `enviado BOOLEAN NOT NULL DEFAULT FALSE`
- `enviado_em TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

---

# 10. Domínio jurídico e documental

# 10.1 Tabela `documento`
## Finalidade
Entidade raiz para documentos formais e operacionais versionáveis.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `demanda_id UUID NULL FK -> demanda(id)`
- `protocolo_id UUID NULL FK -> protocolo(id)`
- `projeto_id UUID NULL FK -> projeto(id)`
- `tipo tipo_documento NOT NULL`
- `titulo VARCHAR(200) NOT NULL`
- `status status_documento NOT NULL DEFAULT 'RASCUNHO'`
- `versao_atual INTEGER NOT NULL DEFAULT 1`
- `autor_usuario_id UUID NULL FK -> usuario(id)`
- `responsavel_revisao_id UUID NULL FK -> usuario(id)`
- `data_aprovacao TIMESTAMP NULL`
- `data_arquivamento TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_documento_gabinete (gabinete_id)`
- `idx_documento_tipo (tipo)`
- `idx_documento_status (status)`
- `idx_documento_demanda (demanda_id)`
- `idx_documento_protocolo (protocolo_id)`
- `idx_documento_projeto (projeto_id)`

---

# 10.2 Tabela `documento_versao`
## Finalidade
Conteúdo e arquivos por versão do documento.

## Campos
- `id UUID PK`
- `documento_id UUID NOT NULL FK -> documento(id)`
- `numero_versao INTEGER NOT NULL`
- `conteudo_texto TEXT NULL`
- `arquivo_id UUID NULL FK -> arquivo_upload(id)`
- `resumo_alteracao TEXT NULL`
- `criado_por UUID NULL FK -> usuario(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (documento_id, numero_versao)`

## Índices
- `idx_doc_versao_documento (documento_id)`

---

# 10.3 Tabela `parecer_juridico`
## Finalidade
Extensão semântica do documento do tipo parecer.

## Campos
- `id UUID PK`
- `documento_id UUID NOT NULL UNIQUE FK -> documento(id)`
- `tema VARCHAR(150) NULL`
- `ementa TEXT NULL`
- `fundamentacao_resumo TEXT NULL`
- `conclusao_resumo TEXT NULL`

---

# 10.4 Tabela `requerimento`
## Finalidade
Extensão semântica do documento do tipo requerimento.

## Campos
- `id UUID PK`
- `documento_id UUID NOT NULL UNIQUE FK -> documento(id)`
- `numero VARCHAR(50) NULL`
- `assunto VARCHAR(150) NULL`
- `destinatario VARCHAR(150) NULL`
- `data_protocolo TIMESTAMP NULL`

## Índices
- `idx_requerimento_numero (numero)`

---

# 10.5 Tabela `oficio`
## Finalidade
Extensão semântica do documento do tipo ofício.

## Campos
- `id UUID PK`
- `documento_id UUID NOT NULL UNIQUE FK -> documento(id)`
- `numero VARCHAR(50) NULL`
- `destinatario VARCHAR(150) NOT NULL`
- `assunto VARCHAR(150) NULL`
- `data_envio TIMESTAMP NULL`

## Índices
- `idx_oficio_numero (numero)`
- `idx_oficio_destinatario (destinatario)`

---

# 10.6 Tabela `documento_relacao`
## Finalidade
Relacionar documentos entre si.

## Campos
- `id UUID PK`
- `documento_origem_id UUID NOT NULL FK -> documento(id)`
- `documento_destino_id UUID NOT NULL FK -> documento(id)`
- `tipo_relacao VARCHAR(50) NOT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (documento_origem_id, documento_destino_id, tipo_relacao)`

---

# 11. Domínio administrativo

# 11.1 Tabela `tipo_protocolo`
## Finalidade
Catálogo de tipos de protocolo.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome VARCHAR(80) NOT NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Constraints
- `UNIQUE (gabinete_id, nome)`

---

# 11.2 Tabela `protocolo`
## Finalidade
Controle de protocolos e tramitação administrativa.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `tipo_protocolo_id UUID NULL FK -> tipo_protocolo(id)`
- `documento_id UUID NULL FK -> documento(id)`
- `numero VARCHAR(50) NULL`
- `titulo VARCHAR(200) NOT NULL`
- `status status_protocolo NOT NULL DEFAULT 'REGISTRADO'`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `prazo_final TIMESTAMP NULL`
- `origem VARCHAR(100) NULL`
- `observacoes TEXT NULL`
- `data_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `data_conclusao TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_protocolo_gabinete (gabinete_id)`
- `idx_protocolo_tipo (tipo_protocolo_id)`
- `idx_protocolo_status (status)`
- `idx_protocolo_responsavel (responsavel_usuario_id)`
- `idx_protocolo_prazo (prazo_final)`
- `idx_protocolo_numero (numero)`

---

# 11.3 Tabela `rito`
## Finalidade
Etapas administrativas do protocolo.

## Campos
- `id UUID PK`
- `protocolo_id UUID NOT NULL FK -> protocolo(id)`
- `nome_etapa VARCHAR(100) NOT NULL`
- `ordem INTEGER NOT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE'`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `data_inicio TIMESTAMP NULL`
- `data_fim TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (protocolo_id, ordem)`

## Índices
- `idx_rito_protocolo (protocolo_id)`
- `idx_rito_responsavel (responsavel_usuario_id)`

---

# 11.4 Tabela `prazo`
## Finalidade
Prazos específicos ligados a protocolos ou ritos.

## Campos
- `id UUID PK`
- `protocolo_id UUID NULL FK -> protocolo(id)`
- `rito_id UUID NULL FK -> rito(id)`
- `titulo VARCHAR(150) NOT NULL`
- `data_limite TIMESTAMP NOT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'ABERTO'`
- `alerta_em TIMESTAMP NULL`
- `concluido_em TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_prazo_protocolo (protocolo_id)`
- `idx_prazo_rito (rito_id)`
- `idx_prazo_data_limite (data_limite)`

---

# 11.5 Tabela `checklist`
## Finalidade
Itens de checklist de protocolo, tarefa ou projeto.

## Campos
- `id UUID PK`
- `protocolo_id UUID NULL FK -> protocolo(id)`
- `tarefa_id UUID NULL FK -> tarefa(id)`
- `projeto_id UUID NULL FK -> projeto(id)`
- `descricao VARCHAR(200) NOT NULL`
- `ordem INTEGER NULL`
- `concluido BOOLEAN NOT NULL DEFAULT FALSE`
- `concluido_em TIMESTAMP NULL`
- `concluido_por UUID NULL FK -> usuario(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_checklist_protocolo (protocolo_id)`
- `idx_checklist_tarefa (tarefa_id)`
- `idx_checklist_projeto (projeto_id)`

---

# 11.6 Tabela `despacho`
## Finalidade
Despachos administrativos.

## Campos
- `id UUID PK`
- `protocolo_id UUID NOT NULL FK -> protocolo(id)`
- `usuario_id UUID NULL FK -> usuario(id)`
- `texto TEXT NOT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_despacho_protocolo (protocolo_id)`

---

# 11.7 Tabela `tarefa`
## Finalidade
Tarefas operacionais e administrativas.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `demanda_id UUID NULL FK -> demanda(id)`
- `protocolo_id UUID NULL FK -> protocolo(id)`
- `projeto_id UUID NULL FK -> projeto(id)`
- `titulo VARCHAR(200) NOT NULL`
- `descricao TEXT NULL`
- `responsavel_usuario_id UUID NOT NULL FK -> usuario(id)`
- `prioridade prioridade_demanda NOT NULL DEFAULT 'MEDIA'`
- `status status_tarefa NOT NULL DEFAULT 'ABERTA'`
- `data_limite TIMESTAMP NULL`
- `data_conclusao TIMESTAMP NULL`
- `bloqueio_motivo TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`

## Índices
- `idx_tarefa_gabinete (gabinete_id)`
- `idx_tarefa_responsavel (responsavel_usuario_id)`
- `idx_tarefa_status (status)`
- `idx_tarefa_data_limite (data_limite)`
- `idx_tarefa_demanda (demanda_id)`
- `idx_tarefa_projeto (projeto_id)`

---

# 12. Domínio projetos do mandato

# 12.1 Tabela `projeto`
## Finalidade
Projetos, iniciativas e ações estratégicas do mandato.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NULL FK -> territorio(id)`
- `nome VARCHAR(200) NOT NULL`
- `descricao TEXT NULL`
- `status status_projeto NOT NULL DEFAULT 'PLANEJADO'`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `prioritario BOOLEAN NOT NULL DEFAULT FALSE`
- `data_inicio DATE NULL`
- `data_fim_prevista DATE NULL`
- `data_fim_real DATE NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `created_by UUID NULL FK -> usuario(id)`

## Índices
- `idx_projeto_gabinete (gabinete_id)`
- `idx_projeto_territorio (territorio_id)`
- `idx_projeto_status (status)`
- `idx_projeto_responsavel (responsavel_usuario_id)`
- `idx_projeto_prioritario (prioritario)`

---

# 12.2 Tabela `responsavel_projeto`
## Finalidade
Múltiplos responsáveis por projeto.

## Campos
- `id UUID PK`
- `projeto_id UUID NOT NULL FK -> projeto(id)`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `papel VARCHAR(50) NOT NULL`
- `principal BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (projeto_id, usuario_id, papel)`

---

# 12.3 Tabela `etapa_projeto`
## Finalidade
Etapas do projeto.

## Campos
- `id UUID PK`
- `projeto_id UUID NOT NULL FK -> projeto(id)`
- `nome VARCHAR(150) NOT NULL`
- `descricao TEXT NULL`
- `ordem INTEGER NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'PLANEJADO'`
- `data_inicio DATE NULL`
- `data_fim_prevista DATE NULL`
- `data_fim_real DATE NULL`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_etapa_projeto (projeto_id)`
- `idx_etapa_status (status)`

---

# 12.4 Tabela `entregavel`
## Finalidade
Entregáveis mensuráveis do projeto.

## Campos
- `id UUID PK`
- `projeto_id UUID NOT NULL FK -> projeto(id)`
- `etapa_id UUID NULL FK -> etapa_projeto(id)`
- `nome VARCHAR(150) NOT NULL`
- `descricao TEXT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE'`
- `data_prevista DATE NULL`
- `data_entrega DATE NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_entregavel_projeto (projeto_id)`
- `idx_entregavel_etapa (etapa_id)`

---

# 12.5 Tabela `indicador_projeto`
## Finalidade
Indicadores quantitativos do projeto.

## Campos
- `id UUID PK`
- `projeto_id UUID NOT NULL FK -> projeto(id)`
- `nome VARCHAR(150) NOT NULL`
- `unidade VARCHAR(30) NULL`
- `meta NUMERIC(14,2) NULL`
- `valor_atual NUMERIC(14,2) NULL`
- `data_referencia DATE NULL`
- `observacao TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_indicador_projeto (projeto_id)`

---

# 12.6 Tabela `risco_projeto`
## Finalidade
Riscos do projeto.

## Campos
- `id UUID PK`
- `projeto_id UUID NOT NULL FK -> projeto(id)`
- `descricao TEXT NOT NULL`
- `nivel nivel_risco NOT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'ABERTO'`
- `plano_acao TEXT NULL`
- `responsavel_usuario_id UUID NULL FK -> usuario(id)`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_risco_projeto (projeto_id)`
- `idx_risco_nivel (nivel)`
- `idx_risco_status (status)`

---

# 13. Domínio territorial agregado

# 13.1 Tabela `evento_territorial`
## Finalidade
Registro de eventos territoriais relevantes, agregáveis por área.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NOT NULL FK -> territorio(id)`
- `tipo VARCHAR(80) NOT NULL`
- `titulo VARCHAR(200) NOT NULL`
- `descricao TEXT NULL`
- `data_evento TIMESTAMP NOT NULL`
- `usuario_responsavel_id UUID NULL FK -> usuario(id)`
- `publico_estimado INTEGER NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_evento_territorial_territorio (territorio_id)`
- `idx_evento_territorial_tipo (tipo)`
- `idx_evento_territorial_data (data_evento)`

---

# 13.2 Tabela `cobertura_equipe`
## Finalidade
Snapshot ou consolidado de cobertura territorial por equipe/colaborador.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NOT NULL FK -> territorio(id)`
- `equipe_id UUID NULL FK -> equipe(id)`
- `usuario_id UUID NULL FK -> usuario(id)`
- `periodo_inicio DATE NOT NULL`
- `periodo_fim DATE NOT NULL`
- `quantidade_visitas INTEGER NOT NULL DEFAULT 0`
- `quantidade_registros INTEGER NOT NULL DEFAULT 0`
- `quantidade_demandas INTEGER NOT NULL DEFAULT 0`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_cobertura_territorio (territorio_id)`
- `idx_cobertura_equipe (equipe_id)`
- `idx_cobertura_usuario (usuario_id)`
- `idx_cobertura_periodo (periodo_inicio, periodo_fim)`

---

# 13.3 Tabela `indicador_territorial_agregado`
## Finalidade
Persistência de agregados territoriais por período e tema.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `territorio_id UUID NOT NULL FK -> territorio(id)`
- `periodo_inicio DATE NOT NULL`
- `periodo_fim DATE NOT NULL`
- `tema VARCHAR(100) NOT NULL`
- `quantidade_demandas INTEGER NOT NULL DEFAULT 0`
- `quantidade_visitas INTEGER NOT NULL DEFAULT 0`
- `quantidade_eventos INTEGER NOT NULL DEFAULT 0`
- `tempo_medio_atendimento_horas NUMERIC(10,2) NULL`
- `dados_json JSONB NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (gabinete_id, territorio_id, periodo_inicio, periodo_fim, tema)`

## Índices
- `idx_ind_territorial_territorio (territorio_id)`
- `idx_ind_territorial_periodo (periodo_inicio, periodo_fim)`
- `idx_ind_territorial_tema (tema)`

---

# 14. Arquivos, auditoria e integração

# 14.1 Tabela `arquivo_upload`
## Finalidade
Metadados de arquivos enviados ao sistema.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `nome_original VARCHAR(255) NOT NULL`
- `nome_storage VARCHAR(255) NOT NULL`
- `mime_type VARCHAR(100) NOT NULL`
- `tamanho_bytes BIGINT NOT NULL`
- `hash_sha256 VARCHAR(64) NULL`
- `url_storage TEXT NOT NULL`
- `bucket VARCHAR(100) NULL`
- `uploaded_by UUID NULL FK -> usuario(id)`
- `uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## Índices
- `idx_arquivo_gabinete (gabinete_id)`
- `idx_arquivo_hash (hash_sha256)`
- `idx_arquivo_uploader (uploaded_by)`

---

# 14.2 Tabela `auditoria`
## Finalidade
Trilha de auditoria de ações sensíveis.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `usuario_id UUID NULL FK -> usuario(id)`
- `entidade VARCHAR(100) NOT NULL`
- `entidade_id UUID NULL`
- `acao VARCHAR(50) NOT NULL`
- `payload_anterior JSONB NULL`
- `payload_novo JSONB NULL`
- `ip_origem VARCHAR(64) NULL`
- `user_agent TEXT NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_auditoria_gabinete (gabinete_id)`
- `idx_auditoria_usuario (usuario_id)`
- `idx_auditoria_entidade (entidade, entidade_id)`
- `idx_auditoria_data (created_at)`

---

# 14.3 Tabela `notificacao`
## Finalidade
Fila e histórico de notificações do sistema.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `tipo VARCHAR(50) NOT NULL`
- `titulo VARCHAR(150) NOT NULL`
- `mensagem TEXT NOT NULL`
- `lida BOOLEAN NOT NULL DEFAULT FALSE`
- `referencia_tipo VARCHAR(50) NULL`
- `referencia_id UUID NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `lida_em TIMESTAMP NULL`

## Índices
- `idx_notificacao_usuario (usuario_id, lida)`
- `idx_notificacao_data (created_at)`

---

# 14.4 Tabela `integracao_evento`
## Finalidade
Eventos outbound/inbound para integrações futuras, inclusive com REVISA.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `direcao VARCHAR(20) NOT NULL`  
  Valores: `OUTBOUND`, `INBOUND`
- `sistema_origem VARCHAR(50) NOT NULL`
- `sistema_destino VARCHAR(50) NOT NULL`
- `tipo_evento VARCHAR(80) NOT NULL`
- `chave_externa VARCHAR(100) NULL`
- `payload JSONB NOT NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE'`
- `tentativas INTEGER NOT NULL DEFAULT 0`
- `processado_em TIMESTAMP NULL`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Índices
- `idx_integracao_status (status)`
- `idx_integracao_tipo (tipo_evento)`
- `idx_integracao_chave (chave_externa)`

---

# 14.5 Tabela `sync_mobile`
## Finalidade
Controle de idempotência dos envios mobile.

## Campos
- `id UUID PK`
- `gabinete_id UUID NOT NULL FK -> gabinete(id)`
- `usuario_id UUID NOT NULL FK -> usuario(id)`
- `client_generated_id VARCHAR(100) NOT NULL`
- `entidade VARCHAR(50) NOT NULL`
- `entidade_id UUID NULL`
- `hash_payload VARCHAR(64) NULL`
- `status VARCHAR(30) NOT NULL DEFAULT 'PROCESSADO'`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

## Constraints
- `UNIQUE (usuario_id, client_generated_id, entidade)`

## Índices
- `idx_sync_mobile_usuario (usuario_id)`
- `idx_sync_mobile_entidade (entidade)`

---

# 15. Tabelas de parâmetros configuráveis

Para evitar hardcode excessivo, recomenda-se tabelas paramétricas por gabinete.

## 15.1 `parametro_prioridade`
- `id UUID PK`
- `gabinete_id UUID FK`
- `nome VARCHAR(50)`
- `ordem INTEGER`
- `ativo BOOLEAN`

## 15.2 `parametro_tipo_agenda`
- substituível por `tipo_agenda`

## 15.3 `parametro_tipo_documento_extra`
- para tipos adicionais além do enum base, se necessário

## 15.4 `parametro_sla`
- `id UUID PK`
- `gabinete_id UUID FK`
- `categoria_id UUID NULL`
- `prioridade prioridade_demanda`
- `horas_limite INTEGER NOT NULL`
- `ativo BOOLEAN NOT NULL DEFAULT TRUE`

## 15.5 `parametro_notificacao`
- tipo de evento
- perfil alvo
- canal
- antecedência

---

# 16. Views e materialized views recomendadas

# 16.1 `vw_dashboard_executivo`
## Finalidade
Consolidar cards do dashboard executivo.

## Métricas sugeridas
- demandas abertas
- demandas críticas
- SLA vencido
- protocolos pendentes
- tarefas críticas
- projetos prioritários em risco
- documentos em revisão

---

# 16.2 `vw_agenda_vereador`
## Finalidade
Agenda consolidada e limpa do vereador.

---

# 16.3 `vw_cobertura_equipes`
## Finalidade
Consolidado de cobertura por equipe/período.

---

# 16.4 `mv_indicador_territorial_mensal`
## Finalidade
Materialized view para leitura rápida territorial agregada.

---

# 16.5 `vw_fila_demandas`
## Finalidade
Fila operacional com coluna derivada de criticidade.

---

# 17. Constraints funcionais críticas

## 17.1 Integridade de território
- `territorio.parent_id` deve respeitar hierarquia
- região não pode ser filha de microárea
- microárea não pode ter filhos no MVP

## 17.2 Integridade de contato
- CPF único quando informado
- alertas de duplicidade por heurística: nome + telefone + bairro

## 17.3 Integridade de demanda
- toda alteração de status relevante deve gerar `historico_demanda`
- conclusão deve preencher `data_conclusao`
- reabertura deve preencher `motivo_reabertura`

## 17.4 Integridade documental
- `documento_versao` deve ser monotônica por `numero_versao`
- `documento.versao_atual` deve refletir a última versão válida

## 17.5 Integridade administrativa
- `agenda_evento.data_fim >= data_inicio`
- `tarefa.responsavel_usuario_id` obrigatório
- protocolos concluídos devem ter data de conclusão

## 17.6 Integridade territorial agregada
- indicadores territoriais só devem armazenar agregados
- não criar tabela de score individual político

---

# 18. Estratégia de migrações

## Ordem sugerida
1. `gabinete`
2. `equipe`
3. `usuario`
4. `usuario_escopo`
5. `territorio`
6. cadastros de base (`organizacao`, `lideranca_comunitaria`)
7. `cidadao_contato`, `contato_canal`, `consentimento_contato`
8. `categoria_demanda`, `demanda`, `historico_demanda`, `encaminhamento`
9. `tipo_agenda`, `agenda_evento`, `agenda_participante`, `lembrete_agenda`
10. `arquivo_upload`, `demanda_anexo`, `visita_campo`
11. `documento`, `documento_versao`, `parecer_juridico`, `requerimento`, `oficio`
12. `tipo_protocolo`, `protocolo`, `rito`, `prazo`, `despacho`, `checklist`, `tarefa`
13. `projeto`, `responsavel_projeto`, `etapa_projeto`, `entregavel`, `indicador_projeto`, `risco_projeto`
14. `evento_territorial`, `cobertura_equipe`, `indicador_territorial_agregado`
15. `auditoria`, `notificacao`, `sync_mobile`, `integracao_evento`
16. views e materialized views

---

# 19. Exemplo SQL inicial do núcleo

```sql
CREATE TABLE gabinete (
    id UUID PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    sigla VARCHAR(50),
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipe (
    id UUID PRIMARY KEY,
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    supervisor_usuario_id UUID,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (gabinete_id, nome)
);

CREATE TABLE usuario (
    id UUID PRIMARY KEY,
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    equipe_id UUID REFERENCES equipe(id),
    nome VARCHAR(150) NOT NULL,
    email_login VARCHAR(150) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    foto_upload_id UUID,
    foto_url TEXT,
    senha_hash TEXT NOT NULL,
    perfil VARCHAR(50) NOT NULL,
    ultimo_login TIMESTAMP,
    mfa_habilitado BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE territorio (
    id UUID PRIMARY KEY,
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    parent_id UUID REFERENCES territorio(id),
    nome VARCHAR(150) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    codigo_externo VARCHAR(50),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (gabinete_id, parent_id, nome, tipo)
);

CREATE TABLE cidadao_contato (
    id UUID PRIMARY KEY,
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    origem_cadastro VARCHAR(30) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    cpf VARCHAR(14),
    data_nascimento DATE,
    telefone_principal VARCHAR(20),
    telefone_secundario VARCHAR(20),
    email VARCHAR(150),
    logradouro TEXT,
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    cep VARCHAR(10),
    tipo_contato VARCHAR(50) NOT NULL DEFAULT 'CIDADAO',
    foto_upload_id UUID,
    foto_url TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'ATIVO',
    duplicidade_suspeita BOOLEAN NOT NULL DEFAULT FALSE,
    observacoes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX ux_cidadao_contato_cpf
ON cidadao_contato(cpf)
WHERE cpf IS NOT NULL;

CREATE TABLE demanda (
    id UUID PRIMARY KEY,
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    cidadao_id UUID REFERENCES cidadao_contato(id),
    territorio_id UUID REFERENCES territorio(id),
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NOT NULL,
    prioridade VARCHAR(20) NOT NULL DEFAULT 'MEDIA',
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTA',
    responsavel_usuario_id UUID REFERENCES usuario(id),
    origem_cadastro VARCHAR(30) NOT NULL,
    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sla_data TIMESTAMP,
    data_conclusao TIMESTAMP,
    motivo_reabertura TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE historico_demanda (
    id UUID PRIMARY KEY,
    demanda_id UUID NOT NULL REFERENCES demanda(id),
    usuario_id UUID REFERENCES usuario(id),
    acao VARCHAR(80) NOT NULL,
    status_anterior VARCHAR(30),
    status_novo VARCHAR(30),
    observacao TEXT,
    dados_json JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

# 20. Relatório interpretativo

Este modelo relacional foi construído para sustentar três objetivos ao mesmo tempo:

1. **operação diária do gabinete**
2. **rastreabilidade jurídica e administrativa**
3. **visão territorial agregada e executiva**

O desenho evita dois erros comuns:
- achatar tudo em poucas tabelas genéricas demais
- fragmentar demais cedo demais com modelagem impossível de operar

A separação por domínios permite crescer com segurança:
- mobile e campo alimentam `cidadao_contato`, `demanda` e `visita_campo`
- operação interna gira em torno de `demanda`, `agenda`, `tarefa` e `protocolo`
- jurídico evolui sobre `documento` e `documento_versao`
- territorial agregado se consolida com snapshots e views

Também ficou preservado o princípio mais importante deste sistema: **não modelar inferência política sensível individual**.
A camada territorial foi mantida em leitura agregada e operacional.

---

# 21. Próximo passo natural

A partir deste ponto, as duas continuações mais úteis são:

1. transformar este modelo em **DDL SQL completo de criação do banco**, pronto para migrations;
2. transformar o modelo em **contratos de API por domínio** (`auth`, `contatos`, `demandas`, `agenda`, `juridico`, `admin`, `projetos`, `territorial`).

