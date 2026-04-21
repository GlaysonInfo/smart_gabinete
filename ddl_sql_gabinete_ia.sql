BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS postgis;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'perfil_usuario') THEN
        CREATE TYPE perfil_usuario AS ENUM (
            'COLABORADOR_EXTERNO',
            'SUPERVISOR_EQUIPE',
            'ASSESSOR_NIVEL_1',
            'ASSESSOR_JURIDICO',
            'ASSESSOR_ADMINISTRATIVO',
            'CHEFE_GABINETE',
            'VEREADOR'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_contato') THEN
        CREATE TYPE status_contato AS ENUM (
            'ATIVO',
            'INATIVO',
            'PENDENTE_VALIDACAO',
            'DUPLICIDADE_SUSPEITA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_demanda') THEN
        CREATE TYPE status_demanda AS ENUM (
            'ABERTA',
            'EM_TRIAGEM',
            'EM_ATENDIMENTO',
            'ENCAMINHADA',
            'AGUARDANDO_RETORNO',
            'CONCLUIDA',
            'SUSPENSA',
            'CANCELADA',
            'REABERTA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prioridade_demanda') THEN
        CREATE TYPE prioridade_demanda AS ENUM (
            'BAIXA',
            'MEDIA',
            'ALTA',
            'CRITICA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_visita') THEN
        CREATE TYPE status_visita AS ENUM (
            'PLANEJADA',
            'REALIZADA',
            'NAO_REALIZADA',
            'REAGENDADA',
            'CANCELADA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_agenda') THEN
        CREATE TYPE status_agenda AS ENUM (
            'PLANEJADO',
            'CONFIRMADO',
            'EM_ANDAMENTO',
            'REALIZADO',
            'CANCELADO',
            'REAGENDADO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_tarefa') THEN
        CREATE TYPE status_tarefa AS ENUM (
            'ABERTA',
            'EM_EXECUCAO',
            'BLOQUEADA',
            'CONCLUIDA',
            'CANCELADA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_documento') THEN
        CREATE TYPE status_documento AS ENUM (
            'RASCUNHO',
            'EM_ELABORACAO',
            'EM_REVISAO',
            'APROVADO',
            'PROTOCOLADO',
            'ARQUIVADO',
            'CANCELADO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_documento') THEN
        CREATE TYPE tipo_documento AS ENUM (
            'PARECER',
            'REQUERIMENTO',
            'OFICIO',
            'MINUTA',
            'ANEXO_OPERACIONAL',
            'OUTRO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_protocolo') THEN
        CREATE TYPE status_protocolo AS ENUM (
            'REGISTRADO',
            'EM_TRAMITACAO',
            'PENDENTE',
            'CONCLUIDO',
            'ARQUIVADO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_projeto') THEN
        CREATE TYPE status_projeto AS ENUM (
            'PLANEJADO',
            'EM_ANDAMENTO',
            'PAUSADO',
            'CONCLUIDO',
            'CANCELADO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nivel_risco') THEN
        CREATE TYPE nivel_risco AS ENUM (
            'BAIXO',
            'MEDIO',
            'ALTO',
            'CRITICO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_territorio') THEN
        CREATE TYPE tipo_territorio AS ENUM (
            'REGIAO',
            'BAIRRO',
            'MICROAREA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'origem_cadastro') THEN
        CREATE TYPE origem_cadastro AS ENUM (
            'MOBILE_CAMPO',
            'WEB_INTERNO',
            'IMPORTACAO',
            'INTEGRACAO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'canal_contato') THEN
        CREATE TYPE canal_contato AS ENUM (
            'TELEFONE',
            'WHATSAPP',
            'EMAIL',
            'OUTRO'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_encaminhamento') THEN
        CREATE TYPE tipo_encaminhamento AS ENUM (
            'INTERNO',
            'JURIDICO',
            'ADMINISTRATIVO',
            'EXTERNO'
        );
    END IF;
END $$;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION validar_hierarquia_territorio()
RETURNS TRIGGER AS $$
DECLARE
    parent_tipo tipo_territorio;
BEGIN
    IF NEW.parent_id IS NULL THEN
        IF NEW.tipo <> 'REGIAO' THEN
            RAISE EXCEPTION 'Somente REGIAO pode existir sem parent_id';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.parent_id = NEW.id THEN
        RAISE EXCEPTION 'Território não pode referenciar a si mesmo';
    END IF;

    SELECT tipo INTO parent_tipo
    FROM territorio
    WHERE id = NEW.parent_id;

    IF parent_tipo IS NULL THEN
        RAISE EXCEPTION 'parent_id inválido para território';
    END IF;

    IF NEW.tipo = 'BAIRRO' AND parent_tipo <> 'REGIAO' THEN
        RAISE EXCEPTION 'BAIRRO deve ser filho de REGIAO';
    ELSIF NEW.tipo = 'MICROAREA' AND parent_tipo <> 'BAIRRO' THEN
        RAISE EXCEPTION 'MICROAREA deve ser filha de BAIRRO';
    ELSIF NEW.tipo = 'REGIAO' THEN
        RAISE EXCEPTION 'REGIAO não pode ter parent_id';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE gabinete (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(150) NOT NULL,
    sigla VARCHAR(50),
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipe (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    supervisor_usuario_id UUID,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_equipe_nome UNIQUE (gabinete_id, nome)
);

CREATE TABLE territorio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    parent_id UUID REFERENCES territorio(id),
    nome VARCHAR(150) NOT NULL,
    tipo tipo_territorio NOT NULL,
    codigo_externo VARCHAR(50),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_territorio_nome UNIQUE (gabinete_id, parent_id, nome, tipo),
    CONSTRAINT chk_territorio_parent_self CHECK (parent_id IS NULL OR parent_id <> id)
);

CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    equipe_id UUID REFERENCES equipe(id),
    nome VARCHAR(150) NOT NULL,
    email_login VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    foto_upload_id UUID,
    foto_url TEXT,
    senha_hash TEXT NOT NULL,
    perfil perfil_usuario NOT NULL,
    ultimo_login TIMESTAMPTZ,
    mfa_habilitado BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id),
    updated_by UUID REFERENCES usuario(id),
    CONSTRAINT uq_usuario_email UNIQUE (email_login),
    CONSTRAINT chk_usuario_nome CHECK (btrim(nome) <> '')
);

ALTER TABLE equipe
    ADD CONSTRAINT fk_equipe_supervisor
    FOREIGN KEY (supervisor_usuario_id) REFERENCES usuario(id);

CREATE TABLE usuario_escopo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    territorio_id UUID REFERENCES territorio(id),
    equipe_id UUID REFERENCES equipe(id),
    escopo_tipo VARCHAR(50) NOT NULL,
    escopo_valor VARCHAR(100),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_usuario_escopo_alvo CHECK (
        territorio_id IS NOT NULL OR equipe_id IS NOT NULL OR escopo_valor IS NOT NULL
    )
);

CREATE TABLE sessao_usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    refresh_token_hash TEXT NOT NULL,
    device_info TEXT,
    ip_origem VARCHAR(64),
    expira_em TIMESTAMPTZ NOT NULL,
    revogada BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organizacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(80) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(150),
    endereco TEXT,
    observacoes TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'ATIVO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lideranca_comunitaria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    organizacao_id UUID REFERENCES organizacao(id),
    nome VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(150),
    tema_principal VARCHAR(100),
    observacoes TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cidadao_contato (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    origem_cadastro origem_cadastro NOT NULL,
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
    status status_contato NOT NULL DEFAULT 'ATIVO',
    duplicidade_suspeita BOOLEAN NOT NULL DEFAULT FALSE,
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id),
    updated_by UUID REFERENCES usuario(id)
);

CREATE UNIQUE INDEX ux_cidadao_contato_cpf
ON cidadao_contato(cpf)
WHERE cpf IS NOT NULL;

CREATE TABLE contato_canal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cidadao_id UUID NOT NULL REFERENCES cidadao_contato(id) ON DELETE CASCADE,
    canal canal_contato NOT NULL,
    valor VARCHAR(150) NOT NULL,
    principal BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_contato_canal UNIQUE (cidadao_id, canal, valor)
);

CREATE TABLE consentimento_contato (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cidadao_id UUID NOT NULL REFERENCES cidadao_contato(id) ON DELETE CASCADE,
    canal canal_contato NOT NULL,
    consentido BOOLEAN NOT NULL,
    finalidade VARCHAR(150) NOT NULL,
    forma_registro VARCHAR(50),
    observacao TEXT,
    registrado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    registrado_por UUID REFERENCES usuario(id)
);

CREATE TABLE contato_tag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(80) NOT NULL,
    cor VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_contato_tag UNIQUE (gabinete_id, nome)
);

CREATE TABLE contato_tag_rel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cidadao_id UUID NOT NULL REFERENCES cidadao_contato(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES contato_tag(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_contato_tag_rel UNIQUE (cidadao_id, tag_id)
);

CREATE TABLE categoria_demanda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_categoria_demanda UNIQUE (gabinete_id, nome)
);

CREATE TABLE demanda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    cidadao_id UUID REFERENCES cidadao_contato(id),
    territorio_id UUID REFERENCES territorio(id),
    categoria_id UUID REFERENCES categoria_demanda(id),
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NOT NULL,
    prioridade prioridade_demanda NOT NULL DEFAULT 'MEDIA',
    status status_demanda NOT NULL DEFAULT 'ABERTA',
    responsavel_usuario_id UUID REFERENCES usuario(id),
    origem_cadastro origem_cadastro NOT NULL,
    data_abertura TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sla_data TIMESTAMPTZ,
    data_conclusao TIMESTAMPTZ,
    motivo_reabertura TEXT,
    motivo_cancelamento TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id),
    updated_by UUID REFERENCES usuario(id),
    CONSTRAINT chk_demanda_titulo CHECK (btrim(titulo) <> ''),
    CONSTRAINT chk_demanda_descricao CHECK (btrim(descricao) <> '')
);

CREATE TABLE historico_demanda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demanda_id UUID NOT NULL REFERENCES demanda(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuario(id),
    acao VARCHAR(80) NOT NULL,
    status_anterior status_demanda,
    status_novo status_demanda,
    observacao TEXT,
    dados_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE encaminhamento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demanda_id UUID NOT NULL REFERENCES demanda(id) ON DELETE CASCADE,
    tipo tipo_encaminhamento NOT NULL,
    destino_usuario_id UUID REFERENCES usuario(id),
    destino_texto VARCHAR(150),
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTO',
    descricao TEXT NOT NULL,
    data_encaminhamento TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_retorno TIMESTAMPTZ,
    created_by UUID REFERENCES usuario(id)
);

CREATE TABLE demanda_tag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(80) NOT NULL,
    cor VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_demanda_tag UNIQUE (gabinete_id, nome)
);

CREATE TABLE demanda_tag_rel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demanda_id UUID NOT NULL REFERENCES demanda(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES demanda_tag(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_demanda_tag_rel UNIQUE (demanda_id, tag_id)
);

CREATE TABLE arquivo_upload (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome_original VARCHAR(255) NOT NULL,
    nome_storage VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamanho_bytes BIGINT NOT NULL,
    hash_sha256 VARCHAR(64),
    url_storage TEXT NOT NULL,
    bucket VARCHAR(100),
    uploaded_by UUID REFERENCES usuario(id),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE demanda_anexo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demanda_id UUID NOT NULL REFERENCES demanda(id) ON DELETE CASCADE,
    arquivo_id UUID NOT NULL REFERENCES arquivo_upload(id) ON DELETE CASCADE,
    tipo VARCHAR(50),
    descricao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id),
    CONSTRAINT uq_demanda_anexo UNIQUE (demanda_id, arquivo_id)
);

CREATE TABLE visita_campo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID NOT NULL REFERENCES territorio(id),
    cidadao_id UUID REFERENCES cidadao_contato(id),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    tipo VARCHAR(50) NOT NULL,
    status status_visita NOT NULL DEFAULT 'PLANEJADA',
    resultado VARCHAR(50),
    data_hora TIMESTAMPTZ NOT NULL,
    observacao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tipo_agenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(80) NOT NULL,
    cor VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_tipo_agenda UNIQUE (gabinete_id, nome)
);

CREATE TABLE agenda_evento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    tipo_agenda_id UUID REFERENCES tipo_agenda(id),
    demanda_id UUID REFERENCES demanda(id),
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    status status_agenda NOT NULL DEFAULT 'PLANEJADO',
    data_inicio TIMESTAMPTZ NOT NULL,
    data_fim TIMESTAMPTZ NOT NULL,
    local_texto VARCHAR(200),
    responsavel_usuario_id UUID REFERENCES usuario(id),
    eh_agenda_vereador BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id),
    updated_by UUID REFERENCES usuario(id),
    CONSTRAINT chk_agenda_datas CHECK (data_fim >= data_inicio)
);

CREATE TABLE agenda_participante (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agenda_evento_id UUID NOT NULL REFERENCES agenda_evento(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuario(id),
    cidadao_id UUID REFERENCES cidadao_contato(id),
    nome_externo VARCHAR(150),
    tipo_participante VARCHAR(30) NOT NULL,
    confirmado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_agenda_participante_alvo CHECK (
        num_nonnulls(usuario_id, cidadao_id, nome_externo) >= 1
    )
);

CREATE TABLE lembrete_agenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agenda_evento_id UUID NOT NULL REFERENCES agenda_evento(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    minutos_antes INTEGER NOT NULL,
    canal VARCHAR(30) NOT NULL,
    enviado BOOLEAN NOT NULL DEFAULT FALSE,
    enviado_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_lembrete_minutos CHECK (minutos_antes >= 0)
);

CREATE TABLE tipo_protocolo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(80) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_tipo_protocolo UNIQUE (gabinete_id, nome)
);

CREATE TABLE protocolo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    tipo_protocolo_id UUID REFERENCES tipo_protocolo(id),
    documento_id UUID,
    numero VARCHAR(50),
    titulo VARCHAR(200) NOT NULL,
    status status_protocolo NOT NULL DEFAULT 'REGISTRADO',
    responsavel_usuario_id UUID REFERENCES usuario(id),
    prazo_final TIMESTAMPTZ,
    origem VARCHAR(100),
    observacoes TEXT,
    data_registro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_conclusao TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolo_id UUID NOT NULL REFERENCES protocolo(id) ON DELETE CASCADE,
    nome_etapa VARCHAR(100) NOT NULL,
    ordem INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    responsavel_usuario_id UUID REFERENCES usuario(id),
    data_inicio TIMESTAMPTZ,
    data_fim TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_rito_ordem UNIQUE (protocolo_id, ordem)
);

CREATE TABLE prazo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolo_id UUID REFERENCES protocolo(id) ON DELETE CASCADE,
    rito_id UUID REFERENCES rito(id) ON DELETE CASCADE,
    titulo VARCHAR(150) NOT NULL,
    data_limite TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTO',
    alerta_em TIMESTAMPTZ,
    concluido_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prazo_alvo CHECK (
        num_nonnulls(protocolo_id, rito_id) >= 1
    )
);

CREATE TABLE projeto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID REFERENCES territorio(id),
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    status status_projeto NOT NULL DEFAULT 'PLANEJADO',
    responsavel_usuario_id UUID REFERENCES usuario(id),
    prioritario BOOLEAN NOT NULL DEFAULT FALSE,
    data_inicio DATE,
    data_fim_prevista DATE,
    data_fim_real DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id)
);

CREATE TABLE responsavel_projeto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES projeto(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    papel VARCHAR(50) NOT NULL,
    principal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_responsavel_projeto UNIQUE (projeto_id, usuario_id, papel)
);

CREATE TABLE etapa_projeto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES projeto(id) ON DELETE CASCADE,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    ordem INTEGER,
    status VARCHAR(30) NOT NULL DEFAULT 'PLANEJADO',
    data_inicio DATE,
    data_fim_prevista DATE,
    data_fim_real DATE,
    responsavel_usuario_id UUID REFERENCES usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entregavel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES projeto(id) ON DELETE CASCADE,
    etapa_id UUID REFERENCES etapa_projeto(id) ON DELETE SET NULL,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    data_prevista DATE,
    data_entrega DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE indicador_projeto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES projeto(id) ON DELETE CASCADE,
    nome VARCHAR(150) NOT NULL,
    unidade VARCHAR(30),
    meta NUMERIC(14,2),
    valor_atual NUMERIC(14,2),
    data_referencia DATE,
    observacao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risco_projeto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projeto_id UUID NOT NULL REFERENCES projeto(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    nivel nivel_risco NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTO',
    plano_acao TEXT,
    responsavel_usuario_id UUID REFERENCES usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tarefa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    demanda_id UUID REFERENCES demanda(id) ON DELETE SET NULL,
    protocolo_id UUID REFERENCES protocolo(id) ON DELETE SET NULL,
    projeto_id UUID REFERENCES projeto(id) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    responsavel_usuario_id UUID NOT NULL REFERENCES usuario(id),
    prioridade prioridade_demanda NOT NULL DEFAULT 'MEDIA',
    status status_tarefa NOT NULL DEFAULT 'ABERTA',
    data_limite TIMESTAMPTZ,
    data_conclusao TIMESTAMPTZ,
    bloqueio_motivo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES usuario(id)
);

CREATE TABLE checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolo_id UUID REFERENCES protocolo(id) ON DELETE CASCADE,
    tarefa_id UUID REFERENCES tarefa(id) ON DELETE CASCADE,
    projeto_id UUID REFERENCES projeto(id) ON DELETE CASCADE,
    descricao VARCHAR(200) NOT NULL,
    ordem INTEGER,
    concluido BOOLEAN NOT NULL DEFAULT FALSE,
    concluido_em TIMESTAMPTZ,
    concluido_por UUID REFERENCES usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_checklist_alvo CHECK (
        num_nonnulls(protocolo_id, tarefa_id, projeto_id) = 1
    )
);

CREATE TABLE despacho (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolo_id UUID NOT NULL REFERENCES protocolo(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuario(id),
    texto TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    demanda_id UUID REFERENCES demanda(id) ON DELETE SET NULL,
    protocolo_id UUID REFERENCES protocolo(id) ON DELETE SET NULL,
    projeto_id UUID REFERENCES projeto(id) ON DELETE SET NULL,
    tipo tipo_documento NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    status status_documento NOT NULL DEFAULT 'RASCUNHO',
    versao_atual INTEGER NOT NULL DEFAULT 1,
    autor_usuario_id UUID REFERENCES usuario(id),
    responsavel_revisao_id UUID REFERENCES usuario(id),
    data_aprovacao TIMESTAMPTZ,
    data_arquivamento TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_documento_versao_atual CHECK (versao_atual >= 1)
);

ALTER TABLE protocolo
    ADD CONSTRAINT fk_protocolo_documento
    FOREIGN KEY (documento_id) REFERENCES documento(id) ON DELETE SET NULL;

CREATE TABLE documento_versao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL REFERENCES documento(id) ON DELETE CASCADE,
    numero_versao INTEGER NOT NULL,
    conteudo_texto TEXT,
    arquivo_id UUID REFERENCES arquivo_upload(id) ON DELETE SET NULL,
    resumo_alteracao TEXT,
    criado_por UUID REFERENCES usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_documento_versao UNIQUE (documento_id, numero_versao),
    CONSTRAINT chk_documento_numero_versao CHECK (numero_versao >= 1)
);

CREATE TABLE parecer_juridico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL UNIQUE REFERENCES documento(id) ON DELETE CASCADE,
    tema VARCHAR(150),
    ementa TEXT,
    fundamentacao_resumo TEXT,
    conclusao_resumo TEXT
);

CREATE TABLE requerimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL UNIQUE REFERENCES documento(id) ON DELETE CASCADE,
    numero VARCHAR(50),
    assunto VARCHAR(150),
    destinatario VARCHAR(150),
    data_protocolo TIMESTAMPTZ
);

CREATE TABLE oficio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL UNIQUE REFERENCES documento(id) ON DELETE CASCADE,
    numero VARCHAR(50),
    destinatario VARCHAR(150) NOT NULL,
    assunto VARCHAR(150),
    data_envio TIMESTAMPTZ
);

CREATE TABLE documento_relacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_origem_id UUID NOT NULL REFERENCES documento(id) ON DELETE CASCADE,
    documento_destino_id UUID NOT NULL REFERENCES documento(id) ON DELETE CASCADE,
    tipo_relacao VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_documento_relacao UNIQUE (documento_origem_id, documento_destino_id, tipo_relacao),
    CONSTRAINT chk_documento_relacao_distinto CHECK (documento_origem_id <> documento_destino_id)
);

CREATE TABLE evento_territorial (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID NOT NULL REFERENCES territorio(id),
    tipo VARCHAR(80) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    data_evento TIMESTAMPTZ NOT NULL,
    usuario_responsavel_id UUID REFERENCES usuario(id),
    publico_estimado INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_evento_publico CHECK (publico_estimado IS NULL OR publico_estimado >= 0)
);

CREATE TABLE cobertura_equipe (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID NOT NULL REFERENCES territorio(id),
    equipe_id UUID REFERENCES equipe(id),
    usuario_id UUID REFERENCES usuario(id),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    quantidade_visitas INTEGER NOT NULL DEFAULT 0,
    quantidade_registros INTEGER NOT NULL DEFAULT 0,
    quantidade_demandas INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cobertura_periodo CHECK (periodo_fim >= periodo_inicio),
    CONSTRAINT chk_cobertura_quantidades CHECK (
        quantidade_visitas >= 0 AND quantidade_registros >= 0 AND quantidade_demandas >= 0
    )
);

CREATE TABLE indicador_territorial_agregado (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    territorio_id UUID NOT NULL REFERENCES territorio(id),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    tema VARCHAR(100) NOT NULL,
    quantidade_demandas INTEGER NOT NULL DEFAULT 0,
    quantidade_visitas INTEGER NOT NULL DEFAULT 0,
    quantidade_eventos INTEGER NOT NULL DEFAULT 0,
    tempo_medio_atendimento_horas NUMERIC(10,2),
    dados_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_indicador_territorial UNIQUE (gabinete_id, territorio_id, periodo_inicio, periodo_fim, tema),
    CONSTRAINT chk_indicador_territorial_periodo CHECK (periodo_fim >= periodo_inicio),
    CONSTRAINT chk_indicador_territorial_quantidades CHECK (
        quantidade_demandas >= 0 AND quantidade_visitas >= 0 AND quantidade_eventos >= 0
    )
);

CREATE TABLE notificacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    mensagem TEXT NOT NULL,
    lida BOOLEAN NOT NULL DEFAULT FALSE,
    referencia_tipo VARCHAR(50),
    referencia_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lida_em TIMESTAMPTZ
);

CREATE TABLE auditoria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    usuario_id UUID REFERENCES usuario(id),
    entidade VARCHAR(100) NOT NULL,
    entidade_id UUID,
    acao VARCHAR(50) NOT NULL,
    payload_anterior JSONB,
    payload_novo JSONB,
    ip_origem VARCHAR(64),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE integracao_evento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    direcao VARCHAR(20) NOT NULL,
    sistema_origem VARCHAR(50) NOT NULL,
    sistema_destino VARCHAR(50) NOT NULL,
    tipo_evento VARCHAR(80) NOT NULL,
    chave_externa VARCHAR(100),
    payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    tentativas INTEGER NOT NULL DEFAULT 0,
    processado_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_integracao_direcao CHECK (direcao IN ('OUTBOUND', 'INBOUND')),
    CONSTRAINT chk_integracao_tentativas CHECK (tentativas >= 0)
);

CREATE TABLE sync_mobile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    client_generated_id VARCHAR(100) NOT NULL,
    entidade VARCHAR(50) NOT NULL,
    entidade_id UUID,
    hash_payload VARCHAR(64),
    status VARCHAR(30) NOT NULL DEFAULT 'PROCESSADO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sync_mobile UNIQUE (usuario_id, client_generated_id, entidade)
);

CREATE TABLE parametro_prioridade (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    nome VARCHAR(50) NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_parametro_prioridade UNIQUE (gabinete_id, nome)
);

CREATE TABLE parametro_sla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    categoria_id UUID REFERENCES categoria_demanda(id),
    prioridade prioridade_demanda NOT NULL,
    horas_limite INTEGER NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_parametro_sla_horas CHECK (horas_limite > 0)
);

CREATE TABLE parametro_notificacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gabinete_id UUID NOT NULL REFERENCES gabinete(id),
    tipo_evento VARCHAR(80) NOT NULL,
    perfil_alvo perfil_usuario,
    canal VARCHAR(30) NOT NULL,
    antecedencia_minutos INTEGER,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_parametro_notificacao_antecedencia CHECK (
        antecedencia_minutos IS NULL OR antecedencia_minutos >= 0
    )
);

CREATE INDEX idx_gabinete_ativo ON gabinete (ativo);

CREATE INDEX idx_equipe_gabinete ON equipe (gabinete_id);
CREATE INDEX idx_equipe_supervisor ON equipe (supervisor_usuario_id);

CREATE INDEX idx_territorio_gabinete ON territorio (gabinete_id);
CREATE INDEX idx_territorio_parent ON territorio (parent_id);
CREATE INDEX idx_territorio_tipo ON territorio (tipo);

CREATE INDEX idx_usuario_gabinete ON usuario (gabinete_id);
CREATE INDEX idx_usuario_perfil ON usuario (perfil);
CREATE INDEX idx_usuario_equipe ON usuario (equipe_id);
CREATE INDEX idx_usuario_ativo ON usuario (ativo);

CREATE INDEX idx_usuario_escopo_usuario ON usuario_escopo (usuario_id);
CREATE INDEX idx_usuario_escopo_territorio ON usuario_escopo (territorio_id);
CREATE INDEX idx_usuario_escopo_equipe ON usuario_escopo (equipe_id);

CREATE INDEX idx_sessao_usuario_usuario ON sessao_usuario (usuario_id);
CREATE INDEX idx_sessao_usuario_expira ON sessao_usuario (expira_em);

CREATE INDEX idx_organizacao_gabinete ON organizacao (gabinete_id);
CREATE INDEX idx_organizacao_territorio ON organizacao (territorio_id);
CREATE INDEX idx_organizacao_tipo ON organizacao (tipo);

CREATE INDEX idx_lideranca_gabinete ON lideranca_comunitaria (gabinete_id);
CREATE INDEX idx_lideranca_territorio ON lideranca_comunitaria (territorio_id);
CREATE INDEX idx_lideranca_organizacao ON lideranca_comunitaria (organizacao_id);

CREATE INDEX idx_contato_gabinete ON cidadao_contato (gabinete_id);
CREATE INDEX idx_contato_territorio ON cidadao_contato (territorio_id);
CREATE INDEX idx_contato_nome ON cidadao_contato (nome);
CREATE INDEX idx_contato_telefone ON cidadao_contato (telefone_principal);
CREATE INDEX idx_contato_status ON cidadao_contato (status);
CREATE INDEX idx_contato_duplicidade ON cidadao_contato (duplicidade_suspeita);

CREATE INDEX idx_contato_canal_cidadao ON contato_canal (cidadao_id);
CREATE INDEX idx_contato_canal_tipo ON contato_canal (canal);

CREATE INDEX idx_consentimento_cidadao ON consentimento_contato (cidadao_id);
CREATE INDEX idx_consentimento_canal ON consentimento_contato (canal);
CREATE INDEX idx_consentimento_finalidade ON consentimento_contato (finalidade);

CREATE INDEX idx_categoria_demanda_gabinete ON categoria_demanda (gabinete_id);

CREATE INDEX idx_demanda_gabinete ON demanda (gabinete_id);
CREATE INDEX idx_demanda_cidadao ON demanda (cidadao_id);
CREATE INDEX idx_demanda_territorio ON demanda (territorio_id);
CREATE INDEX idx_demanda_categoria ON demanda (categoria_id);
CREATE INDEX idx_demanda_status ON demanda (status);
CREATE INDEX idx_demanda_prioridade ON demanda (prioridade);
CREATE INDEX idx_demanda_responsavel ON demanda (responsavel_usuario_id);
CREATE INDEX idx_demanda_sla ON demanda (sla_data);
CREATE INDEX idx_demanda_status_prioridade_sla ON demanda (status, prioridade, sla_data);

CREATE INDEX idx_hist_demanda_demanda ON historico_demanda (demanda_id);
CREATE INDEX idx_hist_demanda_usuario ON historico_demanda (usuario_id);
CREATE INDEX idx_hist_demanda_data ON historico_demanda (created_at);

CREATE INDEX idx_encaminhamento_demanda ON encaminhamento (demanda_id);
CREATE INDEX idx_encaminhamento_destino ON encaminhamento (destino_usuario_id);
CREATE INDEX idx_encaminhamento_status ON encaminhamento (status);

CREATE INDEX idx_visita_gabinete ON visita_campo (gabinete_id);
CREATE INDEX idx_visita_territorio ON visita_campo (territorio_id);
CREATE INDEX idx_visita_usuario ON visita_campo (usuario_id);
CREATE INDEX idx_visita_cidadao ON visita_campo (cidadao_id);
CREATE INDEX idx_visita_data ON visita_campo (data_hora);

CREATE INDEX idx_arquivo_gabinete ON arquivo_upload (gabinete_id);
CREATE INDEX idx_arquivo_hash ON arquivo_upload (hash_sha256);
CREATE INDEX idx_arquivo_uploader ON arquivo_upload (uploaded_by);

CREATE INDEX idx_agenda_gabinete ON agenda_evento (gabinete_id);
CREATE INDEX idx_agenda_territorio ON agenda_evento (territorio_id);
CREATE INDEX idx_agenda_tipo ON agenda_evento (tipo_agenda_id);
CREATE INDEX idx_agenda_status ON agenda_evento (status);
CREATE INDEX idx_agenda_inicio ON agenda_evento (data_inicio);
CREATE INDEX idx_agenda_responsavel ON agenda_evento (responsavel_usuario_id);
CREATE INDEX idx_agenda_vereador ON agenda_evento (eh_agenda_vereador);

CREATE INDEX idx_agenda_participante_evento ON agenda_participante (agenda_evento_id);
CREATE INDEX idx_agenda_participante_usuario ON agenda_participante (usuario_id);
CREATE INDEX idx_agenda_participante_cidadao ON agenda_participante (cidadao_id);

CREATE INDEX idx_lembrete_agenda_evento ON lembrete_agenda (agenda_evento_id);
CREATE INDEX idx_lembrete_agenda_usuario ON lembrete_agenda (usuario_id);

CREATE INDEX idx_protocolo_gabinete ON protocolo (gabinete_id);
CREATE INDEX idx_protocolo_tipo ON protocolo (tipo_protocolo_id);
CREATE INDEX idx_protocolo_status ON protocolo (status);
CREATE INDEX idx_protocolo_responsavel ON protocolo (responsavel_usuario_id);
CREATE INDEX idx_protocolo_prazo ON protocolo (prazo_final);
CREATE INDEX idx_protocolo_numero ON protocolo (numero);

CREATE INDEX idx_rito_protocolo ON rito (protocolo_id);
CREATE INDEX idx_rito_responsavel ON rito (responsavel_usuario_id);

CREATE INDEX idx_prazo_protocolo ON prazo (protocolo_id);
CREATE INDEX idx_prazo_rito ON prazo (rito_id);
CREATE INDEX idx_prazo_data_limite ON prazo (data_limite);

CREATE INDEX idx_tarefa_gabinete ON tarefa (gabinete_id);
CREATE INDEX idx_tarefa_responsavel ON tarefa (responsavel_usuario_id);
CREATE INDEX idx_tarefa_status ON tarefa (status);
CREATE INDEX idx_tarefa_data_limite ON tarefa (data_limite);
CREATE INDEX idx_tarefa_demanda ON tarefa (demanda_id);
CREATE INDEX idx_tarefa_protocolo ON tarefa (protocolo_id);
CREATE INDEX idx_tarefa_projeto ON tarefa (projeto_id);

CREATE INDEX idx_checklist_protocolo ON checklist (protocolo_id);
CREATE INDEX idx_checklist_tarefa ON checklist (tarefa_id);
CREATE INDEX idx_checklist_projeto ON checklist (projeto_id);

CREATE INDEX idx_despacho_protocolo ON despacho (protocolo_id);

CREATE INDEX idx_projeto_gabinete ON projeto (gabinete_id);
CREATE INDEX idx_projeto_territorio ON projeto (territorio_id);
CREATE INDEX idx_projeto_status ON projeto (status);
CREATE INDEX idx_projeto_responsavel ON projeto (responsavel_usuario_id);
CREATE INDEX idx_projeto_prioritario ON projeto (prioritario);

CREATE INDEX idx_etapa_projeto ON etapa_projeto (projeto_id);
CREATE INDEX idx_etapa_status ON etapa_projeto (status);

CREATE INDEX idx_entregavel_projeto ON entregavel (projeto_id);
CREATE INDEX idx_entregavel_etapa ON entregavel (etapa_id);

CREATE INDEX idx_indicador_projeto ON indicador_projeto (projeto_id);

CREATE INDEX idx_risco_projeto ON risco_projeto (projeto_id);
CREATE INDEX idx_risco_nivel ON risco_projeto (nivel);
CREATE INDEX idx_risco_status ON risco_projeto (status);

CREATE INDEX idx_documento_gabinete ON documento (gabinete_id);
CREATE INDEX idx_documento_tipo ON documento (tipo);
CREATE INDEX idx_documento_status ON documento (status);
CREATE INDEX idx_documento_demanda ON documento (demanda_id);
CREATE INDEX idx_documento_protocolo ON documento (protocolo_id);
CREATE INDEX idx_documento_projeto ON documento (projeto_id);

CREATE INDEX idx_documento_versao_documento ON documento_versao (documento_id);

CREATE INDEX idx_requerimento_numero ON requerimento (numero);
CREATE INDEX idx_oficio_numero ON oficio (numero);
CREATE INDEX idx_oficio_destinatario ON oficio (destinatario);

CREATE INDEX idx_evento_territorial_territorio ON evento_territorial (territorio_id);
CREATE INDEX idx_evento_territorial_tipo ON evento_territorial (tipo);
CREATE INDEX idx_evento_territorial_data ON evento_territorial (data_evento);

CREATE INDEX idx_cobertura_territorio ON cobertura_equipe (territorio_id);
CREATE INDEX idx_cobertura_equipe ON cobertura_equipe (equipe_id);
CREATE INDEX idx_cobertura_usuario ON cobertura_equipe (usuario_id);
CREATE INDEX idx_cobertura_periodo ON cobertura_equipe (periodo_inicio, periodo_fim);

CREATE INDEX idx_ind_territorial_territorio ON indicador_territorial_agregado (territorio_id);
CREATE INDEX idx_ind_territorial_periodo ON indicador_territorial_agregado (periodo_inicio, periodo_fim);
CREATE INDEX idx_ind_territorial_tema ON indicador_territorial_agregado (tema);

CREATE INDEX idx_notificacao_usuario ON notificacao (usuario_id, lida);
CREATE INDEX idx_notificacao_data ON notificacao (created_at);

CREATE INDEX idx_auditoria_gabinete ON auditoria (gabinete_id);
CREATE INDEX idx_auditoria_usuario ON auditoria (usuario_id);
CREATE INDEX idx_auditoria_entidade ON auditoria (entidade, entidade_id);
CREATE INDEX idx_auditoria_data ON auditoria (created_at);

CREATE INDEX idx_integracao_status ON integracao_evento (status);
CREATE INDEX idx_integracao_tipo ON integracao_evento (tipo_evento);
CREATE INDEX idx_integracao_chave ON integracao_evento (chave_externa);

CREATE INDEX idx_sync_mobile_usuario ON sync_mobile (usuario_id);
CREATE INDEX idx_sync_mobile_entidade ON sync_mobile (entidade);

CREATE INDEX idx_parametro_sla_categoria ON parametro_sla (categoria_id);
CREATE INDEX idx_parametro_sla_prioridade ON parametro_sla (prioridade);

CREATE INDEX idx_parametro_notificacao_evento ON parametro_notificacao (tipo_evento);
CREATE INDEX idx_parametro_notificacao_perfil ON parametro_notificacao (perfil_alvo);

CREATE TRIGGER trg_territorio_validar_hierarquia
BEFORE INSERT OR UPDATE OF parent_id, tipo ON territorio
FOR EACH ROW EXECUTE FUNCTION validar_hierarquia_territorio();

CREATE TRIGGER trg_gabinete_updated_at
BEFORE UPDATE ON gabinete
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_equipe_updated_at
BEFORE UPDATE ON equipe
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_territorio_updated_at
BEFORE UPDATE ON territorio
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_usuario_updated_at
BEFORE UPDATE ON usuario
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_organizacao_updated_at
BEFORE UPDATE ON organizacao
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_lideranca_updated_at
BEFORE UPDATE ON lideranca_comunitaria
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_contato_updated_at
BEFORE UPDATE ON cidadao_contato
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_demanda_updated_at
BEFORE UPDATE ON demanda
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_agenda_evento_updated_at
BEFORE UPDATE ON agenda_evento
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_protocolo_updated_at
BEFORE UPDATE ON protocolo
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_projeto_updated_at
BEFORE UPDATE ON projeto
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_indicador_projeto_updated_at
BEFORE UPDATE ON indicador_projeto
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_risco_projeto_updated_at
BEFORE UPDATE ON risco_projeto
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tarefa_updated_at
BEFORE UPDATE ON tarefa
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_documento_updated_at
BEFORE UPDATE ON documento
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE VIEW vw_fila_demandas AS
SELECT
    d.id,
    d.gabinete_id,
    d.cidadao_id,
    c.nome AS cidadao_nome,
    d.territorio_id,
    t.nome AS territorio_nome,
    d.categoria_id,
    cd.nome AS categoria_nome,
    d.titulo,
    d.prioridade,
    d.status,
    d.responsavel_usuario_id,
    u.nome AS responsavel_nome,
    d.sla_data,
    CASE
        WHEN d.status IN ('CONCLUIDA', 'CANCELADA') THEN 'BAIXA'
        WHEN d.prioridade = 'CRITICA' THEN 'CRITICA'
        WHEN d.sla_data IS NOT NULL AND d.sla_data < CURRENT_TIMESTAMP THEN 'CRITICA'
        WHEN d.prioridade = 'ALTA' THEN 'ALTA'
        ELSE 'NORMAL'
    END AS criticidade_derivada,
    d.created_at,
    d.updated_at
FROM demanda d
LEFT JOIN cidadao_contato c ON c.id = d.cidadao_id
LEFT JOIN territorio t ON t.id = d.territorio_id
LEFT JOIN categoria_demanda cd ON cd.id = d.categoria_id
LEFT JOIN usuario u ON u.id = d.responsavel_usuario_id;

CREATE OR REPLACE VIEW vw_dashboard_executivo AS
SELECT
    g.id AS gabinete_id,
    COUNT(*) FILTER (WHERE d.status NOT IN ('CONCLUIDA', 'CANCELADA')) AS demandas_abertas,
    COUNT(*) FILTER (
        WHERE d.status NOT IN ('CONCLUIDA', 'CANCELADA')
          AND (d.prioridade = 'CRITICA' OR (d.sla_data IS NOT NULL AND d.sla_data < CURRENT_TIMESTAMP))
    ) AS demandas_criticas,
    COUNT(*) FILTER (
        WHERE d.status NOT IN ('CONCLUIDA', 'CANCELADA')
          AND d.sla_data IS NOT NULL
          AND d.sla_data < CURRENT_TIMESTAMP
    ) AS sla_vencido,
    COUNT(DISTINCT p.id) FILTER (WHERE p.status IN ('REGISTRADO', 'EM_TRAMITACAO', 'PENDENTE')) AS protocolos_pendentes,
    COUNT(DISTINCT tj.id) FILTER (WHERE tj.status IN ('ABERTA', 'EM_EXECUCAO', 'BLOQUEADA')) AS tarefas_abertas,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.prioritario = TRUE AND pr.status IN ('PLANEJADO', 'EM_ANDAMENTO', 'PAUSADO')) AS projetos_prioritarios_ativos,
    COUNT(DISTINCT doc.id) FILTER (WHERE doc.status = 'EM_REVISAO') AS documentos_em_revisao
FROM gabinete g
LEFT JOIN demanda d ON d.gabinete_id = g.id
LEFT JOIN protocolo p ON p.gabinete_id = g.id
LEFT JOIN tarefa tj ON tj.gabinete_id = g.id
LEFT JOIN projeto pr ON pr.gabinete_id = g.id
LEFT JOIN documento doc ON doc.gabinete_id = g.id
GROUP BY g.id;

CREATE OR REPLACE VIEW vw_agenda_vereador AS
SELECT
    a.id,
    a.gabinete_id,
    a.titulo,
    a.descricao,
    a.status,
    a.data_inicio,
    a.data_fim,
    a.local_texto,
    a.territorio_id,
    t.nome AS territorio_nome,
    a.responsavel_usuario_id,
    u.nome AS responsavel_nome
FROM agenda_evento a
LEFT JOIN territorio t ON t.id = a.territorio_id
LEFT JOIN usuario u ON u.id = a.responsavel_usuario_id
WHERE a.eh_agenda_vereador = TRUE;

COMMIT;
