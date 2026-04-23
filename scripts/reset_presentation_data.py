from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.auth import hash_password
from apps.api.app.store import COLLECTIONS, GABINETE_ID, default_territories

DB_PATH = ROOT / "data" / "gabinete_ia.json"

PASSWORD_HASH = hash_password("Senha@123")

CHEFE_ID = "10000000-0000-4000-8000-000000000001"
COORD_ID = "10000000-0000-4000-8000-000000000002"
SUP_NORTE_ID = "10000000-0000-4000-8000-000000000003"
SUP_CENTRO_ID = "10000000-0000-4000-8000-000000000004"
SUP_ALTEROSAS_ID = "10000000-0000-4000-8000-000000000005"
ASSESSOR_NORTE_ID = "10000000-0000-4000-8000-000000000006"
ASSESSOR_CENTRO_ID = "10000000-0000-4000-8000-000000000007"
ASSESSOR_ALTEROSAS_ID = "10000000-0000-4000-8000-000000000008"

TEAM_CENTRO_ID = "20000000-0000-4000-8000-000000000001"
TEAM_NORTE_ID = "20000000-0000-4000-8000-000000000002"
TEAM_ALTEROSAS_ID = "20000000-0000-4000-8000-000000000003"
TEAM_RELACIONAMENTO_ID = "20000000-0000-4000-8000-000000000004"

CENTRO_ID = "00000000-0000-4000-8000-000000000201"
NORTE_ID = "00000000-0000-4000-8000-000000000204"
ALTEROSAS_ID = "00000000-0000-4000-8000-000000000205"
PTB_ID = "00000000-0000-4000-8000-000000000206"
IMBIRUCU_ID = "00000000-0000-4000-8000-000000000209"

CATEGORY_URBANA_ID = "30000000-0000-4000-8000-000000000001"
CATEGORY_SAUDE_ID = "30000000-0000-4000-8000-000000000002"
CATEGORY_SOCIAL_ID = "30000000-0000-4000-8000-000000000003"
CATEGORY_MOBILIDADE_ID = "30000000-0000-4000-8000-000000000004"


def scope(scope_id: str, territory_id: str) -> dict[str, str]:
    return {
        "id": scope_id,
        "escopo_tipo": "TERRITORIO",
        "territorio_id": territory_id,
    }


def gabinete_scope(scope_id: str) -> dict[str, str]:
    return {
        "id": scope_id,
        "escopo_tipo": "GABINETE",
        "escopo_valor": GABINETE_ID,
    }


def build_state() -> dict[str, list[dict]]:
    now = "2026-04-23T15:30:00Z"
    state = {collection: [] for collection in COLLECTIONS}

    state["gabinetes"] = [
        {
            "id": GABINETE_ID,
            "nome": "Gabinete do Vereador - Gestao de Mandato",
            "sigla": "GDM",
            "descricao": "Base de apresentacao preparada para demonstracao executiva ao vereador.",
            "ativo": True,
            "created_at": now,
            "updated_at": now,
        }
    ]

    state["equipes"] = [
        {
            "id": TEAM_CENTRO_ID,
            "gabinete_id": GABINETE_ID,
            "nome": "Equipe Centro Expandido",
            "descricao": "Frente territorial focada em Centro e PTB.",
            "supervisor_usuario_id": SUP_CENTRO_ID,
            "escopos": [scope("21000000-0000-4000-8000-000000000001", CENTRO_ID), scope("21000000-0000-4000-8000-000000000002", PTB_ID)],
            "ativo": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": TEAM_NORTE_ID,
            "gabinete_id": GABINETE_ID,
            "nome": "Equipe Norte em Campo",
            "descricao": "Captacao e atendimento para a Regional Norte.",
            "supervisor_usuario_id": SUP_NORTE_ID,
            "escopos": [scope("21000000-0000-4000-8000-000000000003", NORTE_ID)],
            "ativo": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": TEAM_ALTEROSAS_ID,
            "gabinete_id": GABINETE_ID,
            "nome": "Equipe Alterosas",
            "descricao": "Base comunitaria, saude e agenda territorial.",
            "supervisor_usuario_id": SUP_ALTEROSAS_ID,
            "escopos": [scope("21000000-0000-4000-8000-000000000004", ALTEROSAS_ID), scope("21000000-0000-4000-8000-000000000005", IMBIRUCU_ID)],
            "ativo": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": TEAM_RELACIONAMENTO_ID,
            "gabinete_id": GABINETE_ID,
            "nome": "Equipe Relacionamento e Dados",
            "descricao": "Qualificacao de cadastros, relacionamento e termometro politico.",
            "supervisor_usuario_id": COORD_ID,
            "escopos": [],
            "ativo": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    state["usuarios"] = [
        {
            "id": CHEFE_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": None,
            "nome": "Marina Andrade",
            "email_login": "chefe@gabineteia.local",
            "telefone": "31999990000",
            "senha_hash": PASSWORD_HASH,
            "perfil": "CHEFE_GABINETE",
            "ultimo_login": "2026-04-23T13:00:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [gabinete_scope("22000000-0000-4000-8000-000000000001")],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": COORD_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_RELACIONAMENTO_ID,
            "nome": "Rafael Guimaraes",
            "email_login": "coordenacao@gabineteia.local",
            "telefone": "31999990001",
            "senha_hash": PASSWORD_HASH,
            "perfil": "COORDENADOR",
            "ultimo_login": "2026-04-23T12:40:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [gabinete_scope("22000000-0000-4000-8000-000000000002")],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": SUP_CENTRO_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_CENTRO_ID,
            "nome": "Camila Braga",
            "email_login": "centro@gabineteia.local",
            "telefone": "31999990002",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_1",
            "ultimo_login": "2026-04-23T11:55:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000003", CENTRO_ID), scope("22000000-0000-4000-8000-000000000004", PTB_ID)],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": SUP_NORTE_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_NORTE_ID,
            "nome": "Diego Torres",
            "email_login": "norte@gabineteia.local",
            "telefone": "31999990003",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_1",
            "ultimo_login": "2026-04-23T12:05:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000005", NORTE_ID)],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": SUP_ALTEROSAS_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_ALTEROSAS_ID,
            "nome": "Juliana Matos",
            "email_login": "alterosas@gabineteia.local",
            "telefone": "31999990004",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_1",
            "ultimo_login": "2026-04-23T11:20:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000006", ALTEROSAS_ID), scope("22000000-0000-4000-8000-000000000007", IMBIRUCU_ID)],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": ASSESSOR_NORTE_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_NORTE_ID,
            "nome": "Leandro Faria",
            "email_login": "campo.norte@gabineteia.local",
            "telefone": "31999990005",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_2",
            "ultimo_login": "2026-04-23T10:45:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000008", NORTE_ID)],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": ASSESSOR_CENTRO_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_CENTRO_ID,
            "nome": "Fernanda Lopes",
            "email_login": "campo.centro@gabineteia.local",
            "telefone": "31999990006",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_2",
            "ultimo_login": "2026-04-23T10:30:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000009", CENTRO_ID)],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": ASSESSOR_ALTEROSAS_ID,
            "gabinete_id": GABINETE_ID,
            "equipe_id": TEAM_ALTEROSAS_ID,
            "nome": "Patricia Moura",
            "email_login": "campo.alterosas@gabineteia.local",
            "telefone": "31999990007",
            "senha_hash": PASSWORD_HASH,
            "perfil": "ASSESSOR_NIVEL_2",
            "ultimo_login": "2026-04-23T10:15:00Z",
            "mfa_habilitado": False,
            "ativo": True,
            "escopos": [scope("22000000-0000-4000-8000-000000000010", ALTEROSAS_ID)],
            "created_at": now,
            "updated_at": now,
        },
    ]

    state["territorios"] = default_territories(now)

    state["categorias_demanda"] = [
        {"id": CATEGORY_URBANA_ID, "gabinete_id": GABINETE_ID, "nome": "Infraestrutura Urbana", "descricao": "Poda, tapa-buraco, limpeza e iluminacao.", "ativo": True},
        {"id": CATEGORY_SAUDE_ID, "gabinete_id": GABINETE_ID, "nome": "Saude e Atendimento", "descricao": "Consultas, exames e unidade de saude.", "ativo": True},
        {"id": CATEGORY_SOCIAL_ID, "gabinete_id": GABINETE_ID, "nome": "Assistencia Social", "descricao": "CRAS, beneficios e acolhimento.", "ativo": True},
        {"id": CATEGORY_MOBILIDADE_ID, "gabinete_id": GABINETE_ID, "nome": "Mobilidade e Transporte", "descricao": "Linhas, sinalizacao e acessibilidade.", "ativo": True},
    ]

    state["contatos"] = [
        {
            "id": "40000000-0000-4000-8000-000000000001",
            "gabinete_id": GABINETE_ID,
            "territorio_id": CENTRO_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "nome": "Ana Paula Ferreira",
            "cpf": None,
            "data_nascimento": "1987-02-14",
            "telefone_principal": "31991110001",
            "telefone_secundario": None,
            "email": "ana.paula.centro@example.com",
            "logradouro": "Rua do Rosario",
            "numero": "84",
            "complemento": "Apto 202",
            "bairro": "Centro",
            "cidade": "Betim",
            "cep": "32600080",
            "tipo_contato": "LIDERANCA",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "ALIADO",
            "influencia": "ALTA",
            "engajamento": "FORTE",
            "voto_2028": "FAVORAVEL",
            "prioridade_politica": "ALTA",
            "origem_politica": "BASE_COMUNITARIA",
            "equipe_id": TEAM_CENTRO_ID,
            "cadastrado_por_usuario_id": ASSESSOR_CENTRO_ID,
            "observacoes": "Preside associacao comercial e mobiliza liderancas do Centro.",
            "created_at": "2026-04-18T09:00:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000002",
            "gabinete_id": GABINETE_ID,
            "territorio_id": CENTRO_ID,
            "origem_cadastro": "WEB_INTERNO",
            "nome": "Jose Ricardo Almeida",
            "cpf": None,
            "data_nascimento": "1978-09-09",
            "telefone_principal": "31991110002",
            "telefone_secundario": None,
            "email": "jose.ricardo@example.com",
            "logradouro": "Rua da Matriz",
            "numero": "155",
            "complemento": None,
            "bairro": "Centro",
            "cidade": "Betim",
            "cep": "32600120",
            "tipo_contato": "CIDADAO",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "PARTICIPANTE",
            "influencia": "MEDIA",
            "engajamento": "MEDIO",
            "voto_2028": "INDEFINIDO",
            "prioridade_politica": "MEDIA",
            "origem_politica": "DECLARADO",
            "equipe_id": TEAM_CENTRO_ID,
            "cadastrado_por_usuario_id": SUP_CENTRO_ID,
            "observacoes": "Busca resposta para recapeamento e seguranca viaria.",
            "created_at": "2026-04-18T10:10:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000003",
            "gabinete_id": GABINETE_ID,
            "territorio_id": NORTE_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "nome": "Rosangela Xavier",
            "cpf": None,
            "data_nascimento": "1983-06-21",
            "telefone_principal": "31991110003",
            "telefone_secundario": None,
            "email": "rosangela.xavier@example.com",
            "logradouro": "Rua das Acacias",
            "numero": "411",
            "complemento": None,
            "bairro": "Regional Norte",
            "cidade": "Betim",
            "cep": "32620000",
            "tipo_contato": "CIDADAO",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "PROXIMO",
            "influencia": "MEDIA",
            "engajamento": "FORTE",
            "voto_2028": "FAVORAVEL",
            "prioridade_politica": "ALTA",
            "origem_politica": "BASE_TERRITORIAL",
            "equipe_id": TEAM_NORTE_ID,
            "cadastrado_por_usuario_id": ASSESSOR_NORTE_ID,
            "observacoes": "Referencia local na pauta de saude da regional.",
            "created_at": "2026-04-18T11:00:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000004",
            "gabinete_id": GABINETE_ID,
            "territorio_id": NORTE_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "nome": "Marcelo Tavares",
            "cpf": None,
            "data_nascimento": "1991-01-03",
            "telefone_principal": "31991110004",
            "telefone_secundario": None,
            "email": "marcelo.tavares@example.com",
            "logradouro": "Avenida das Palmeiras",
            "numero": "52",
            "complemento": None,
            "bairro": "Regional Norte",
            "cidade": "Betim",
            "cep": "32620010",
            "tipo_contato": "CIDADAO",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "PARTICIPANTE",
            "influencia": "BAIXA",
            "engajamento": "MEDIO",
            "voto_2028": "INDEFINIDO",
            "prioridade_politica": "MEDIA",
            "origem_politica": "ATENDIMENTO",
            "equipe_id": TEAM_NORTE_ID,
            "cadastrado_por_usuario_id": ASSESSOR_NORTE_ID,
            "observacoes": "Quer retorno sobre transporte e iluminacao.",
            "created_at": "2026-04-18T11:40:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000005",
            "gabinete_id": GABINETE_ID,
            "territorio_id": ALTEROSAS_ID,
            "origem_cadastro": "WEB_INTERNO",
            "nome": "Luciana Prado",
            "cpf": None,
            "data_nascimento": "1975-11-30",
            "telefone_principal": "31991110005",
            "telefone_secundario": None,
            "email": "luciana.prado@example.com",
            "logradouro": "Rua do Horizonte",
            "numero": "900",
            "complemento": None,
            "bairro": "Alterosas",
            "cidade": "Betim",
            "cep": "32640000",
            "tipo_contato": "LIDERANCA",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "ALIADO",
            "influencia": "ALTA",
            "engajamento": "FORTE",
            "voto_2028": "FAVORAVEL",
            "prioridade_politica": "ALTA",
            "origem_politica": "BASE_COMUNITARIA",
            "equipe_id": TEAM_ALTEROSAS_ID,
            "cadastrado_por_usuario_id": SUP_ALTEROSAS_ID,
            "observacoes": "Mobiliza liderancas religiosas e pauta acolhimento social.",
            "created_at": "2026-04-18T13:20:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000006",
            "gabinete_id": GABINETE_ID,
            "territorio_id": IMBIRUCU_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "nome": "Edson Martins",
            "cpf": None,
            "data_nascimento": "1984-07-08",
            "telefone_principal": "31991110006",
            "telefone_secundario": None,
            "email": "edson.martins@example.com",
            "logradouro": "Rua Bela Vista",
            "numero": "77",
            "complemento": None,
            "bairro": "Imbirucu",
            "cidade": "Betim",
            "cep": "32665000",
            "tipo_contato": "CIDADAO",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "PROXIMO",
            "influencia": "MEDIA",
            "engajamento": "ALTO",
            "voto_2028": "FAVORAVEL",
            "prioridade_politica": "ALTA",
            "origem_politica": "BASE_TERRITORIAL",
            "equipe_id": TEAM_ALTEROSAS_ID,
            "cadastrado_por_usuario_id": ASSESSOR_ALTEROSAS_ID,
            "observacoes": "Lidera pauta de esportes e convivencia comunitaria.",
            "created_at": "2026-04-18T14:05:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000007",
            "gabinete_id": GABINETE_ID,
            "territorio_id": PTB_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "nome": "Silvia Castro",
            "cpf": None,
            "data_nascimento": "1990-12-01",
            "telefone_principal": "31991110007",
            "telefone_secundario": None,
            "email": "silvia.castro@example.com",
            "logradouro": "Rua das Flores",
            "numero": "18",
            "complemento": None,
            "bairro": "PTB",
            "cidade": "Betim",
            "cep": "32670000",
            "tipo_contato": "COLABORADOR",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "ALIADO",
            "influencia": "MEDIA",
            "engajamento": "ALTO",
            "voto_2028": "FAVORAVEL",
            "prioridade_politica": "ALTA",
            "origem_politica": "ORGANIZACAO_INTERNA",
            "equipe_id": TEAM_CENTRO_ID,
            "cadastrado_por_usuario_id": SUP_CENTRO_ID,
            "observacoes": "Apoia mutiroes e mobilizacao de agendas de rua.",
            "created_at": "2026-04-18T15:00:00Z",
            "updated_at": now,
        },
        {
            "id": "40000000-0000-4000-8000-000000000008",
            "gabinete_id": GABINETE_ID,
            "territorio_id": ALTEROSAS_ID,
            "origem_cadastro": "WEB_INTERNO",
            "nome": "Marta Menezes",
            "cpf": None,
            "data_nascimento": "1969-04-17",
            "telefone_principal": "31991110008",
            "telefone_secundario": None,
            "email": "marta.menezes@example.com",
            "logradouro": "Rua Esperanca",
            "numero": "321",
            "complemento": None,
            "bairro": "Alterosas",
            "cidade": "Betim",
            "cep": "32640100",
            "tipo_contato": "CIDADAO",
            "status": "ATIVO",
            "duplicidade_suspeita": False,
            "nivel_relacionamento": "PARTICIPANTE",
            "influencia": "BAIXA",
            "engajamento": "MEDIO",
            "voto_2028": "INDEFINIDO",
            "prioridade_politica": "MEDIA",
            "origem_politica": "ATENDIMENTO",
            "equipe_id": TEAM_RELACIONAMENTO_ID,
            "cadastrado_por_usuario_id": COORD_ID,
            "observacoes": "Solicita acompanhamento de acesso a exame especializado.",
            "created_at": "2026-04-18T16:15:00Z",
            "updated_at": now,
        },
    ]

    state["consentimentos"] = [
        {
            "id": "41000000-0000-4000-8000-000000000001",
            "cidadao_id": "40000000-0000-4000-8000-000000000001",
            "canal": "WHATSAPP",
            "consentido": True,
            "finalidade": "relacionamento institucional",
            "forma_registro": "verbal",
            "observacao": "Autorizou recebimento de agenda e retorno de demandas.",
            "registrado_em": "2026-04-18T09:05:00Z",
            "registrado_por": ASSESSOR_CENTRO_ID,
        },
        {
            "id": "41000000-0000-4000-8000-000000000002",
            "cidadao_id": "40000000-0000-4000-8000-000000000003",
            "canal": "WHATSAPP",
            "consentido": True,
            "finalidade": "retorno de demanda de saude",
            "forma_registro": "mensagem",
            "observacao": "Aceitou retorno por mensagem e ligacao.",
            "registrado_em": "2026-04-18T11:02:00Z",
            "registrado_por": ASSESSOR_NORTE_ID,
        },
        {
            "id": "41000000-0000-4000-8000-000000000003",
            "cidadao_id": "40000000-0000-4000-8000-000000000005",
            "canal": "EMAIL",
            "consentido": True,
            "finalidade": "articulacao comunitaria",
            "forma_registro": "formulario",
            "observacao": "Recebe convites e informativos de agenda.",
            "registrado_em": "2026-04-18T13:22:00Z",
            "registrado_por": SUP_ALTEROSAS_ID,
        },
    ]

    state["demandas"] = [
        {
            "id": "50000000-0000-4000-8000-000000000001",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000002",
            "territorio_id": CENTRO_ID,
            "categoria_id": CATEGORY_URBANA_ID,
            "titulo": "Recapeamento e sinalizacao na Rua da Matriz",
            "descricao": "Trecho com risco para pedestres e motociclistas em horario de pico.",
            "prioridade": "CRITICA",
            "status": "EM_ATENDIMENTO",
            "responsavel_usuario_id": SUP_CENTRO_ID,
            "equipe_id": TEAM_CENTRO_ID,
            "gerada_por_usuario_id": ASSESSOR_CENTRO_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "sla_data": "2026-04-25T18:00:00Z",
            "data_abertura": "2026-04-19T08:00:00Z",
            "data_conclusao": None,
            "tags": ["viario", "centro"],
            "anexos": [],
            "created_at": "2026-04-19T08:00:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000002",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000001",
            "territorio_id": CENTRO_ID,
            "categoria_id": CATEGORY_MOBILIDADE_ID,
            "titulo": "Reforco de vagas rapidas e carga e descarga no Centro",
            "descricao": "Comerciantes pedem reorganizacao de vagas para melhorar fluxo local.",
            "prioridade": "ALTA",
            "status": "ENCAMINHADA",
            "responsavel_usuario_id": SUP_CENTRO_ID,
            "equipe_id": TEAM_CENTRO_ID,
            "gerada_por_usuario_id": SUP_CENTRO_ID,
            "origem_cadastro": "WEB_INTERNO",
            "sla_data": "2026-04-28T18:00:00Z",
            "data_abertura": "2026-04-19T10:30:00Z",
            "data_conclusao": None,
            "tags": ["mobilidade", "comercio"],
            "anexos": [],
            "created_at": "2026-04-19T10:30:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000003",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000003",
            "territorio_id": NORTE_ID,
            "categoria_id": CATEGORY_SAUDE_ID,
            "titulo": "Mutirao de exames e fila de ultrassom na Regional Norte",
            "descricao": "Base relata demora acima do esperado e necessidade de agenda extraordinaria.",
            "prioridade": "CRITICA",
            "status": "EM_TRIAGEM",
            "responsavel_usuario_id": SUP_NORTE_ID,
            "equipe_id": TEAM_NORTE_ID,
            "gerada_por_usuario_id": ASSESSOR_NORTE_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "sla_data": "2026-04-24T18:00:00Z",
            "data_abertura": "2026-04-20T09:20:00Z",
            "data_conclusao": None,
            "tags": ["saude", "exames"],
            "anexos": [],
            "created_at": "2026-04-20T09:20:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000004",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000004",
            "territorio_id": NORTE_ID,
            "categoria_id": CATEGORY_URBANA_ID,
            "titulo": "Troca de luminarias na Avenida das Palmeiras",
            "descricao": "Trecho escuro com aumento de queixas noturnas.",
            "prioridade": "ALTA",
            "status": "ABERTA",
            "responsavel_usuario_id": ASSESSOR_NORTE_ID,
            "equipe_id": TEAM_NORTE_ID,
            "gerada_por_usuario_id": ASSESSOR_NORTE_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "sla_data": "2026-04-27T18:00:00Z",
            "data_abertura": "2026-04-20T11:15:00Z",
            "data_conclusao": None,
            "tags": ["iluminacao", "seguranca"],
            "anexos": [],
            "created_at": "2026-04-20T11:15:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000005",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000005",
            "territorio_id": ALTEROSAS_ID,
            "categoria_id": CATEGORY_SOCIAL_ID,
            "titulo": "Reforco de atendimento do CRAS em Alterosas",
            "descricao": "Famílias relatam aumento de fila e necessidade de plantao extra.",
            "prioridade": "ALTA",
            "status": "AGUARDANDO_RETORNO",
            "responsavel_usuario_id": SUP_ALTEROSAS_ID,
            "equipe_id": TEAM_ALTEROSAS_ID,
            "gerada_por_usuario_id": SUP_ALTEROSAS_ID,
            "origem_cadastro": "WEB_INTERNO",
            "sla_data": "2026-04-29T18:00:00Z",
            "data_abertura": "2026-04-20T14:40:00Z",
            "data_conclusao": None,
            "tags": ["cras", "assistencia"],
            "anexos": [],
            "created_at": "2026-04-20T14:40:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000006",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000006",
            "territorio_id": IMBIRUCU_ID,
            "categoria_id": CATEGORY_MOBILIDADE_ID,
            "titulo": "Adequacao de sinalizacao em frente ao campo do Imbirucu",
            "descricao": "Pais pedem faixa elevada e ordenamento em horario de treino.",
            "prioridade": "MEDIA",
            "status": "CONCLUIDA",
            "responsavel_usuario_id": ASSESSOR_ALTEROSAS_ID,
            "equipe_id": TEAM_ALTEROSAS_ID,
            "gerada_por_usuario_id": ASSESSOR_ALTEROSAS_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "sla_data": "2026-04-22T18:00:00Z",
            "data_abertura": "2026-04-18T16:40:00Z",
            "data_conclusao": "2026-04-22T15:30:00Z",
            "tags": ["esporte", "seguranca"],
            "anexos": [],
            "created_at": "2026-04-18T16:40:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000007",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000007",
            "territorio_id": PTB_ID,
            "categoria_id": CATEGORY_URBANA_ID,
            "titulo": "Mutirao de limpeza e poda em corredores do PTB",
            "descricao": "Ação territorial com apoio de lideranças locais e pedido de cronograma fixo.",
            "prioridade": "MEDIA",
            "status": "REABERTA",
            "responsavel_usuario_id": SUP_CENTRO_ID,
            "equipe_id": TEAM_CENTRO_ID,
            "gerada_por_usuario_id": SUP_CENTRO_ID,
            "origem_cadastro": "MOBILE_CAMPO",
            "sla_data": "2026-04-26T18:00:00Z",
            "data_abertura": "2026-04-19T15:10:00Z",
            "data_conclusao": None,
            "tags": ["limpeza", "mutirao"],
            "anexos": [],
            "created_at": "2026-04-19T15:10:00Z",
            "updated_at": now,
        },
        {
            "id": "50000000-0000-4000-8000-000000000008",
            "gabinete_id": GABINETE_ID,
            "cidadao_id": "40000000-0000-4000-8000-000000000008",
            "territorio_id": ALTEROSAS_ID,
            "categoria_id": CATEGORY_SAUDE_ID,
            "titulo": "Regulacao de consulta com ortopedia para idosa de Alterosas",
            "descricao": "Caso sensivel acompanhado pelo gabinete com prioridade social.",
            "prioridade": "ALTA",
            "status": "ENCAMINHADA",
            "responsavel_usuario_id": COORD_ID,
            "equipe_id": TEAM_RELACIONAMENTO_ID,
            "gerada_por_usuario_id": COORD_ID,
            "origem_cadastro": "WEB_INTERNO",
            "sla_data": "2026-04-30T18:00:00Z",
            "data_abertura": "2026-04-21T09:00:00Z",
            "data_conclusao": None,
            "tags": ["saude", "prioridade_social"],
            "anexos": [],
            "created_at": "2026-04-21T09:00:00Z",
            "updated_at": now,
        },
    ]

    state["historico_demanda"] = [
        {"id": "51000000-0000-4000-8000-000000000001", "demanda_id": "50000000-0000-4000-8000-000000000001", "usuario_id": ASSESSOR_CENTRO_ID, "acao": "CREATE", "status_anterior": None, "status_novo": "EM_ATENDIMENTO", "observacao": "Demanda aberta apos escuta com comerciantes do Centro.", "dados_json": {}, "created_at": "2026-04-19T08:00:00Z"},
        {"id": "51000000-0000-4000-8000-000000000002", "demanda_id": "50000000-0000-4000-8000-000000000003", "usuario_id": ASSESSOR_NORTE_ID, "acao": "CREATE", "status_anterior": None, "status_novo": "EM_TRIAGEM", "observacao": "Caso concentrado na fila de exames da regional.", "dados_json": {}, "created_at": "2026-04-20T09:20:00Z"},
        {"id": "51000000-0000-4000-8000-000000000003", "demanda_id": "50000000-0000-4000-8000-000000000006", "usuario_id": ASSESSOR_ALTEROSAS_ID, "acao": "CONCLUSAO", "status_anterior": "EM_ATENDIMENTO", "status_novo": "CONCLUIDA", "observacao": "Sinalizacao executada pela prefeitura e validada pela comunidade.", "dados_json": {}, "created_at": "2026-04-22T15:30:00Z"},
        {"id": "51000000-0000-4000-8000-000000000004", "demanda_id": "50000000-0000-4000-8000-000000000007", "usuario_id": SUP_CENTRO_ID, "acao": "REABERTURA", "status_anterior": "CONCLUIDA", "status_novo": "REABERTA", "observacao": "Base solicitou novo ciclo de limpeza por cobertura parcial.", "dados_json": {}, "created_at": "2026-04-22T09:00:00Z"},
    ]

    state["agenda_eventos"] = [
        {"id": "60000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "territorio_id": NORTE_ID, "tipo_agenda_id": None, "tipo_agenda": "PLENARIA_REGIONAL", "demanda_id": "50000000-0000-4000-8000-000000000003", "titulo": "Plenaria da saude - Regional Norte", "descricao": "Escuta sobre exames, consultas e fila da unidade de referencia.", "status": "CONFIRMADO", "data_inicio": "2026-04-24T19:00:00Z", "data_fim": "2026-04-24T21:00:00Z", "local_texto": "Escola Municipal da Regional Norte", "responsavel_usuario_id": SUP_NORTE_ID, "eh_agenda_vereador": True, "participantes": [{"cidadao_id": "40000000-0000-4000-8000-000000000003", "tipo_participante": "EXTERNO"}], "publico_estimado": 70, "relatorio_execucao": None, "anexos": [], "created_at": "2026-04-22T10:00:00Z", "updated_at": now},
        {"id": "60000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "territorio_id": CENTRO_ID, "tipo_agenda_id": None, "tipo_agenda": "REUNIAO_BASE", "demanda_id": "50000000-0000-4000-8000-000000000002", "titulo": "Cafe com liderancas do Centro", "descricao": "Alinhamento de mobilidade, comercio e ordenamento urbano.", "status": "CONFIRMADO", "data_inicio": "2026-04-25T08:30:00Z", "data_fim": "2026-04-25T09:45:00Z", "local_texto": "Associacao Comercial", "responsavel_usuario_id": SUP_CENTRO_ID, "eh_agenda_vereador": True, "participantes": [{"cidadao_id": "40000000-0000-4000-8000-000000000001", "tipo_participante": "EXTERNO"}], "publico_estimado": 25, "relatorio_execucao": None, "anexos": [], "created_at": "2026-04-22T11:15:00Z", "updated_at": now},
        {"id": "60000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "territorio_id": ALTEROSAS_ID, "tipo_agenda_id": None, "tipo_agenda": "VISITA_TECNICA", "demanda_id": "50000000-0000-4000-8000-000000000005", "titulo": "Visita tecnica ao CRAS de Alterosas", "descricao": "Levantamento para reforco de atendimento e acolhimento.", "status": "PENDENTE", "data_inicio": "2026-04-26T14:00:00Z", "data_fim": "2026-04-26T15:30:00Z", "local_texto": "CRAS Alterosas", "responsavel_usuario_id": SUP_ALTEROSAS_ID, "eh_agenda_vereador": True, "participantes": [{"cidadao_id": "40000000-0000-4000-8000-000000000005", "tipo_participante": "EXTERNO"}], "publico_estimado": 18, "relatorio_execucao": None, "anexos": [], "created_at": "2026-04-22T13:30:00Z", "updated_at": now},
    ]

    state["interacoes"] = [
        {"id": "70000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000001", "demanda_id": "50000000-0000-4000-8000-000000000002", "agenda_evento_id": "60000000-0000-4000-8000-000000000002", "canal_contato": "PRESENCIAL", "tipo_interacao": "REUNIAO_BASE", "assunto": "Mobilidade no eixo comercial do Centro", "descricao_detalhada": "Liderancas apontaram necessidade de ordenamento de carga e descarga e reforco de fiscalizacao.", "status": "REGISTRADA", "prioridade": "ALTA", "responsavel_usuario_id": SUP_CENTRO_ID, "origem_demanda": "BASE_TERRITORIAL", "indicacao_de_quem": None, "resultado": "Demanda consolidada para envio ao orgao competente.", "proxima_acao": "Fechar memoria tecnica com dados de impacto comercial.", "data_contato": "2026-04-22T08:30:00Z", "data_proxima_acao": "2026-04-24T10:00:00Z", "observacoes": "Boa recepcao da base ao acompanhamento do gabinete.", "created_at": "2026-04-22T08:30:00Z", "updated_at": now},
        {"id": "70000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000003", "demanda_id": "50000000-0000-4000-8000-000000000003", "agenda_evento_id": "60000000-0000-4000-8000-000000000001", "canal_contato": "WHATSAPP", "tipo_interacao": "RETORNO_DEMANDA", "assunto": "Fila de exames na Regional Norte", "descricao_detalhada": "Contato confirmou aumento de pressao e necessidade de posicionamento publico.", "status": "REGISTRADA", "prioridade": "CRITICA", "responsavel_usuario_id": ASSESSOR_NORTE_ID, "origem_demanda": "ATENDIMENTO", "indicacao_de_quem": None, "resultado": "Tema elevado ao radar do vereador.", "proxima_acao": "Validar dados para plenaria e pronunciamento.", "data_contato": "2026-04-22T09:10:00Z", "data_proxima_acao": "2026-04-23T17:00:00Z", "observacoes": "Sentimento social pressionando por resposta rapida.", "created_at": "2026-04-22T09:10:00Z", "updated_at": now},
        {"id": "70000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000005", "demanda_id": "50000000-0000-4000-8000-000000000005", "agenda_evento_id": "60000000-0000-4000-8000-000000000003", "canal_contato": "PRESENCIAL", "tipo_interacao": "VISITA_TECNICA", "assunto": "Pressao social por reforco do CRAS", "descricao_detalhada": "Liderancas pedem cronograma publico de reforco e ampliação de equipe.", "status": "REGISTRADA", "prioridade": "ALTA", "responsavel_usuario_id": SUP_ALTEROSAS_ID, "origem_demanda": "BASE_TERRITORIAL", "indicacao_de_quem": None, "resultado": "Encaminhamento articulado com rede social e assistencia.", "proxima_acao": "Visita tecnica com equipe do vereador.", "data_contato": "2026-04-22T13:20:00Z", "data_proxima_acao": "2026-04-26T14:00:00Z", "observacoes": "Tema sensivel para agenda comunitaria.", "created_at": "2026-04-22T13:20:00Z", "updated_at": now},
    ]

    state["proposicoes"] = [
        {"id": "80000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "titulo": "Programa Municipal de Zeladoria por Rotas Prioritarias", "tipo": "PROJETO_LEI", "numero": "PL 18/2026", "tema": "Infraestrutura Urbana", "status": "COMISSAO", "etapa_kanban": "COMISSAO", "relator": "Comissao de Obras", "prazo": "2026-05-05T18:00:00Z", "posicionamento": "FAVORAVEL", "justificativa_tecnica": "Organiza cronograma por regional com foco em trechos de maior reclamacao.", "discursos": [], "tags": ["zeladoria", "territorio"], "created_at": "2026-04-15T10:00:00Z", "updated_at": now},
        {"id": "80000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "titulo": "Frente de Transparencia da Fila de Exames", "tipo": "REQUERIMENTO", "numero": "REQ 44/2026", "tema": "Saude", "status": "PROTOCOLO", "etapa_kanban": "PROTOCOLO", "relator": None, "prazo": "2026-04-29T18:00:00Z", "posicionamento": "FAVORAVEL", "justificativa_tecnica": "Solicita publicizacao regionalizada da fila e mutiroes extraordinarios.", "discursos": [], "tags": ["saude", "transparencia"], "created_at": "2026-04-20T16:00:00Z", "updated_at": now},
    ]

    state["emendas"] = [
        {"id": "90000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "numero": "EMD-2026-014", "titulo": "Requalificacao de eixos comerciais do Centro", "tipo_emenda": "INDIVIDUAL", "area": "Infraestrutura", "beneficiario": "Secretaria de Obras", "territorio_id": CENTRO_ID, "objeto": "Pavimentacao, drenagem leve e sinalizacao em vias de alto fluxo.", "valor_indicado": 650000.0, "valor_aprovado": 500000.0, "valor_empenhado": 250000.0, "status_execucao": "EMPENHADA", "data_indicacao": "2026-03-10T12:00:00Z", "data_empenho": "2026-04-10T09:00:00Z", "data_ultima_movimentacao": "2026-04-18T09:00:00Z", "latitude": -19.9676, "longitude": -44.1986, "documentos": [], "fotos": [], "created_at": "2026-03-10T12:00:00Z", "updated_at": now},
        {"id": "90000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "numero": "EMD-2026-021", "titulo": "Aparelhamento da atencao primaria no Norte", "tipo_emenda": "INDIVIDUAL", "area": "Saude", "beneficiario": "Secretaria de Saude", "territorio_id": NORTE_ID, "objeto": "Equipamentos para exames e reforco de atendimento itinerante.", "valor_indicado": 420000.0, "valor_aprovado": 420000.0, "valor_empenhado": 420000.0, "status_execucao": "EMPENHADA", "data_indicacao": "2026-03-18T14:00:00Z", "data_empenho": "2026-04-12T10:30:00Z", "data_ultima_movimentacao": "2026-04-21T11:00:00Z", "latitude": -19.9401, "longitude": -44.1672, "documentos": [], "fotos": [], "created_at": "2026-03-18T14:00:00Z", "updated_at": now},
        {"id": "90000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "numero": "EMD-2026-033", "titulo": "Protecao social em Alterosas", "tipo_emenda": "INDIVIDUAL", "area": "Assistencia Social", "beneficiario": "Rede SUAS", "territorio_id": ALTEROSAS_ID, "objeto": "Reforco de mobiliario e custeio para atendimento comunitario.", "valor_indicado": 280000.0, "valor_aprovado": 180000.0, "valor_empenhado": 0.0, "status_execucao": "APROVADA", "data_indicacao": "2026-03-22T16:00:00Z", "data_empenho": None, "data_ultima_movimentacao": "2026-04-19T09:30:00Z", "latitude": -19.9562, "longitude": -44.2155, "documentos": [], "fotos": [], "created_at": "2026-03-22T16:00:00Z", "updated_at": now},
    ]

    state["oficios"] = [
        {"id": "91000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000001", "numero": "OF-2026-041", "titulo": "Solicitacao de recapeamento emergencial", "assunto": "Viario urbano no Centro", "orgao_destino": "Secretaria Municipal de Obras", "status": "ENVIADO", "data_envio": "2026-04-20T08:45:00Z", "prazo_resposta": "2026-04-25T18:00:00Z", "responsavel_usuario_id": SUP_CENTRO_ID, "resposta": None, "follow_up": "Cobrar retorno ate a reuniao com liderancas do Centro.", "created_at": "2026-04-20T08:45:00Z", "updated_at": now},
        {"id": "91000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000003", "numero": "OF-2026-045", "titulo": "Pedido de mutirao extraordinario de exames", "assunto": "Fila de ultrassom - Regional Norte", "orgao_destino": "Secretaria Municipal de Saude", "status": "AGUARDANDO_RETORNO", "data_envio": "2026-04-21T09:40:00Z", "prazo_resposta": "2026-04-24T18:00:00Z", "responsavel_usuario_id": SUP_NORTE_ID, "resposta": None, "follow_up": "Avaliar fala publica do vereador caso nao haja resposta.", "created_at": "2026-04-21T09:40:00Z", "updated_at": now},
        {"id": "91000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000005", "numero": "OF-2026-049", "titulo": "Solicitacao de reforco operacional do CRAS", "assunto": "Atendimento social em Alterosas", "orgao_destino": "Secretaria de Assistencia Social", "status": "ENVIADO", "data_envio": "2026-04-21T15:15:00Z", "prazo_resposta": "2026-04-29T18:00:00Z", "responsavel_usuario_id": SUP_ALTEROSAS_ID, "resposta": None, "follow_up": "Articular visita tecnica e posicionamento conjunto.", "created_at": "2026-04-21T15:15:00Z", "updated_at": now},
    ]

    state["sentimento_social"] = [
        {"id": "92000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "canal": "INSTAGRAM", "periodo": "24H", "tema": "Fila de exames", "positivo": 18, "neutro": 24, "negativo": 58, "alerta": "Regional Norte concentra pressao nas mencoes sobre saude.", "territorio_id": NORTE_ID, "territorio_nome": "Regional Norte", "coletado_em": "2026-04-23T12:10:00Z", "created_at": "2026-04-23T12:10:00Z", "updated_at": now},
        {"id": "92000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "canal": "WHATSAPP", "periodo": "7D", "tema": "Zeladoria urbana", "positivo": 42, "neutro": 33, "negativo": 25, "alerta": "Centro reconhece presenca, mas cobra prazo de execucao do viario.", "territorio_id": CENTRO_ID, "territorio_nome": "Regional Centro", "coletado_em": "2026-04-23T11:50:00Z", "created_at": "2026-04-23T11:50:00Z", "updated_at": now},
        {"id": "92000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "canal": "FACEBOOK", "periodo": "7D", "tema": "Atendimento social", "positivo": 36, "neutro": 29, "negativo": 35, "alerta": "Alterosas pede reforco rapido do CRAS e acolhimento continuado.", "territorio_id": ALTEROSAS_ID, "territorio_nome": "Regional Alterosas", "coletado_em": "2026-04-23T11:20:00Z", "created_at": "2026-04-23T11:20:00Z", "updated_at": now},
        {"id": "92000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "canal": "INSTAGRAM", "periodo": "24H", "tema": "Agenda do vereador", "positivo": 61, "neutro": 25, "negativo": 14, "alerta": "Boa tracao da agenda territorial quando vinculada a entregas concretas.", "territorio_id": PTB_ID, "territorio_nome": "Regional PTB", "coletado_em": "2026-04-23T10:55:00Z", "created_at": "2026-04-23T10:55:00Z", "updated_at": now},
    ]

    state["editais_convenios"] = [
        {"id": "93000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "titulo": "Programa de requalificacao de equipamentos urbanos", "orgao": "Ministerio das Cidades", "status": "OPORTUNIDADE", "prazo": "2026-05-20T18:00:00Z", "municipio_alvo": "Betim", "valor_estimado": 1200000.0, "responsavel_usuario_id": CHEFE_ID, "observacoes": "Pode alavancar entregas em Centro e Norte com contrapartida municipal.", "created_at": "2026-04-22T12:00:00Z", "updated_at": now}
    ]

    state["documentos"] = [
        {"id": "94000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "tipo": "NOTA_TECNICA", "titulo": "Memoria executiva - saude da Regional Norte", "status": "FINALIZADO", "versao_atual": 2, "autor_usuario_id": COORD_ID, "demanda_id": "50000000-0000-4000-8000-000000000003", "protocolo_id": "95000000-0000-4000-8000-000000000001", "projeto_id": None, "tema": "Saude", "ementa": "Analise territorial da fila de exames e proposta de resposta institucional.", "conteudo_texto": "Documento consolidado para fala do vereador e articulacao com a secretaria.", "versoes": [{"id": "94000000-0000-4000-8000-000000000011", "numero_versao": 1, "resumo_alteracao": "Versao inicial", "created_at": "2026-04-21T13:00:00Z"}, {"id": "94000000-0000-4000-8000-000000000012", "numero_versao": 2, "resumo_alteracao": "Inclusao de dados territoriais e agenda", "created_at": "2026-04-22T17:00:00Z"}], "created_at": "2026-04-21T13:00:00Z", "updated_at": now}
    ]

    state["protocolos"] = [
        {"id": "95000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "tipo_protocolo_id": None, "documento_id": "94000000-0000-4000-8000-000000000001", "numero": "2026-118", "titulo": "Protocolo de memoria executiva da saude", "status": "REGISTRADO", "responsavel_usuario_id": COORD_ID, "prazo_final": "2026-04-25T18:00:00Z", "origem": "INTERNA", "observacoes": "Base para audiencia com Executivo.", "created_at": "2026-04-22T17:10:00Z", "updated_at": now}
    ]

    state["tarefas"] = [
        {"id": "96000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000003", "protocolo_id": "95000000-0000-4000-8000-000000000001", "projeto_id": None, "titulo": "Fechar fala do vereador para plenaria da saude", "descricao": "Organizar dados, fala de abertura e respostas mais provaveis.", "responsavel_usuario_id": COORD_ID, "prioridade": "ALTA", "status": "ABERTA", "data_limite": "2026-04-24T12:00:00Z", "data_conclusao": None, "created_at": "2026-04-23T08:00:00Z", "updated_at": now},
        {"id": "96000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000005", "protocolo_id": None, "projeto_id": None, "titulo": "Preparar roteiro de visita ao CRAS Alterosas", "descricao": "Levantar perguntas-chave e interlocutores da visita tecnica.", "responsavel_usuario_id": SUP_ALTEROSAS_ID, "prioridade": "MEDIA", "status": "EM_ANDAMENTO", "data_limite": "2026-04-26T10:00:00Z", "data_conclusao": None, "created_at": "2026-04-23T08:30:00Z", "updated_at": now}
    ]

    state["projetos"] = [
        {"id": "97000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "territorio_id": NORTE_ID, "nome": "Projeto Norte Presente", "descricao": "Plano de agenda, relacionamento e entregas para reduzir pressao territorial na Regional Norte.", "status": "EM_EXECUCAO", "responsavel_usuario_id": SUP_NORTE_ID, "prioritario": True, "data_inicio": "2026-04-15T09:00:00Z", "data_fim_prevista": "2026-06-30T18:00:00Z", "created_at": "2026-04-15T09:00:00Z", "updated_at": now},
        {"id": "97000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "territorio_id": CENTRO_ID, "nome": "Projeto Centro Ordenado", "descricao": "Combina zeladoria, mobilidade e escuta com comerciantes.", "status": "PLANEJADO", "responsavel_usuario_id": SUP_CENTRO_ID, "prioritario": True, "data_inicio": "2026-04-25T08:00:00Z", "data_fim_prevista": "2026-07-15T18:00:00Z", "created_at": "2026-04-18T09:00:00Z", "updated_at": now}
    ]

    state["sync_mobile"] = [
        {"id": "98000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "usuario_id": ASSESSOR_NORTE_ID, "tipo": "UPLOAD", "status": "SUCESSO", "resumo": "18 registros sincronizados da Regional Norte.", "created_at": "2026-04-23T09:15:00Z", "updated_at": "2026-04-23T09:15:00Z"},
        {"id": "98000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "usuario_id": ASSESSOR_CENTRO_ID, "tipo": "UPLOAD", "status": "SUCESSO", "resumo": "12 registros sincronizados do Centro e PTB.", "created_at": "2026-04-23T09:35:00Z", "updated_at": "2026-04-23T09:35:00Z"},
        {"id": "98000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "usuario_id": ASSESSOR_ALTEROSAS_ID, "tipo": "UPLOAD", "status": "SUCESSO", "resumo": "15 registros sincronizados de Alterosas e Imbirucu.", "created_at": "2026-04-23T09:50:00Z", "updated_at": "2026-04-23T09:50:00Z"},
    ]

    state["notificacoes"] = [
        {"id": "99000000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "usuario_id": CHEFE_ID, "titulo": "Pressao alta na Regional Norte", "mensagem": "Fila de exames virou tema dominante nas ultimas 24h.", "lida": False, "created_at": "2026-04-23T12:15:00Z", "updated_at": now},
        {"id": "99000000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "usuario_id": CHEFE_ID, "titulo": "Agenda confirmada com liderancas do Centro", "mensagem": "Cafe com liderancas confirmado para sexta-feira cedo.", "lida": False, "created_at": "2026-04-23T12:25:00Z", "updated_at": now},
    ]

    state["configuracoes"] = [
        {"id": "99500000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "chave": "sla_atendimento", "valor": {"critica_horas": 24, "alta_horas": 48, "media_horas": 72, "baixa_horas": 120, "janela_risco_percentual": 0.8}, "created_at": now, "updated_at": now}
    ]

    state["sla_historico"] = [
        {"id": "99600000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000001", "status": "EM_RISCO", "horas_decorridas": 30, "created_at": "2026-04-23T08:00:00Z", "updated_at": now},
        {"id": "99600000-0000-4000-8000-000000000002", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000003", "status": "VENCIDO", "horas_decorridas": 52, "created_at": "2026-04-23T08:10:00Z", "updated_at": now},
        {"id": "99600000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000006", "status": "CONCLUIDO_NO_PRAZO", "horas_decorridas": 40, "created_at": "2026-04-22T15:30:00Z", "updated_at": now},
    ]

    state["contatos"].extend(
        [
            {"id": "40000000-0000-4000-8000-000000000009", "gabinete_id": GABINETE_ID, "territorio_id": NORTE_ID, "origem_cadastro": "MOBILE_CAMPO", "nome": "Valeria Nunes", "cpf": None, "data_nascimento": "1982-03-11", "telefone_principal": "31991110009", "telefone_secundario": None, "email": "valeria.nunes@example.com", "logradouro": "Rua das Andorinhas", "numero": "140", "complemento": None, "bairro": "Regional Norte", "cidade": "Betim", "cep": "32620020", "tipo_contato": "LIDERANCA", "status": "ATIVO", "duplicidade_suspeita": False, "nivel_relacionamento": "ALIADO", "influencia": "ALTA", "engajamento": "FORTE", "voto_2028": "FAVORAVEL", "prioridade_politica": "ALTA", "origem_politica": "BASE_COMUNITARIA", "equipe_id": TEAM_NORTE_ID, "cadastrado_por_usuario_id": SUP_NORTE_ID, "observacoes": "Coordena grupo de mães que pressiona por exames e pediatria.", "created_at": "2026-04-22T08:20:00Z", "updated_at": now},
            {"id": "40000000-0000-4000-8000-000000000010", "gabinete_id": GABINETE_ID, "territorio_id": NORTE_ID, "origem_cadastro": "MOBILE_CAMPO", "nome": "Paulo Henrique Rocha", "cpf": None, "data_nascimento": "1972-08-02", "telefone_principal": "31991110010", "telefone_secundario": None, "email": "paulo.henrique@example.com", "logradouro": "Rua Bahia", "numero": "45", "complemento": None, "bairro": "Regional Norte", "cidade": "Betim", "cep": "32620030", "tipo_contato": "CIDADAO", "status": "ATIVO", "duplicidade_suspeita": False, "nivel_relacionamento": "PARTICIPANTE", "influencia": "BAIXA", "engajamento": "MEDIO", "voto_2028": "INDEFINIDO", "prioridade_politica": "MEDIA", "origem_politica": "ATENDIMENTO", "equipe_id": TEAM_NORTE_ID, "cadastrado_por_usuario_id": ASSESSOR_NORTE_ID, "observacoes": "Queixa recorrente sobre onibus lotado e atrasos.", "created_at": "2026-04-22T09:00:00Z", "updated_at": now},
            {"id": "40000000-0000-4000-8000-000000000011", "gabinete_id": GABINETE_ID, "territorio_id": PTB_ID, "origem_cadastro": "MOBILE_CAMPO", "nome": "Cristiane Souza", "cpf": None, "data_nascimento": "1988-10-18", "telefone_principal": "31991110011", "telefone_secundario": None, "email": "cristiane.souza@example.com", "logradouro": "Rua Ametista", "numero": "210", "complemento": None, "bairro": "PTB", "cidade": "Betim", "cep": "32670020", "tipo_contato": "CIDADAO", "status": "ATIVO", "duplicidade_suspeita": False, "nivel_relacionamento": "PROXIMO", "influencia": "MEDIA", "engajamento": "ALTO", "voto_2028": "FAVORAVEL", "prioridade_politica": "ALTA", "origem_politica": "BASE_TERRITORIAL", "equipe_id": TEAM_CENTRO_ID, "cadastrado_por_usuario_id": SUP_CENTRO_ID, "observacoes": "Articula abaixo-assinado sobre limpeza urbana e drenagem.", "created_at": "2026-04-22T10:40:00Z", "updated_at": now},
            {"id": "40000000-0000-4000-8000-000000000012", "gabinete_id": GABINETE_ID, "territorio_id": IMBIRUCU_ID, "origem_cadastro": "WEB_INTERNO", "nome": "Renato Borges", "cpf": None, "data_nascimento": "1994-05-26", "telefone_principal": "31991110012", "telefone_secundario": None, "email": "renato.borges@example.com", "logradouro": "Rua das Oliveiras", "numero": "612", "complemento": None, "bairro": "Imbirucu", "cidade": "Betim", "cep": "32665020", "tipo_contato": "COLABORADOR", "status": "ATIVO", "duplicidade_suspeita": False, "nivel_relacionamento": "ALIADO", "influencia": "MEDIA", "engajamento": "ALTO", "voto_2028": "FAVORAVEL", "prioridade_politica": "ALTA", "origem_politica": "ORGANIZACAO_INTERNA", "equipe_id": TEAM_ALTEROSAS_ID, "cadastrado_por_usuario_id": SUP_ALTEROSAS_ID, "observacoes": "Apoia organizacao de agenda esportiva e de juventude.", "created_at": "2026-04-22T11:30:00Z", "updated_at": now},
        ]
    )

    state["demandas"].extend(
        [
            {"id": "50000000-0000-4000-8000-000000000009", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000009", "territorio_id": NORTE_ID, "categoria_id": CATEGORY_SAUDE_ID, "titulo": "Falta de pediatra e sobrecarga da UBS na Regional Norte", "descricao": "Tema explodiu nas redes locais e nas escutas presenciais desta semana.", "prioridade": "CRITICA", "status": "ABERTA", "responsavel_usuario_id": SUP_NORTE_ID, "equipe_id": TEAM_NORTE_ID, "gerada_por_usuario_id": SUP_NORTE_ID, "origem_cadastro": "MOBILE_CAMPO", "sla_data": "2026-04-24T12:00:00Z", "data_abertura": "2026-04-22T08:25:00Z", "data_conclusao": None, "tags": ["saude", "ubs", "pediatria"], "anexos": [], "created_at": "2026-04-22T08:25:00Z", "updated_at": now},
            {"id": "50000000-0000-4000-8000-000000000010", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000010", "territorio_id": NORTE_ID, "categoria_id": CATEGORY_MOBILIDADE_ID, "titulo": "Superlotacao e atraso na linha troncal da Regional Norte", "descricao": "Moradores relatam perda de turno de trabalho por atrasos recorrentes.", "prioridade": "ALTA", "status": "EM_TRIAGEM", "responsavel_usuario_id": ASSESSOR_NORTE_ID, "equipe_id": TEAM_NORTE_ID, "gerada_por_usuario_id": ASSESSOR_NORTE_ID, "origem_cadastro": "MOBILE_CAMPO", "sla_data": "2026-04-25T18:00:00Z", "data_abertura": "2026-04-22T09:05:00Z", "data_conclusao": None, "tags": ["transporte", "onibus"], "anexos": [], "created_at": "2026-04-22T09:05:00Z", "updated_at": now},
            {"id": "50000000-0000-4000-8000-000000000011", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000011", "territorio_id": PTB_ID, "categoria_id": CATEGORY_URBANA_ID, "titulo": "Alagamento recorrente em corredor do PTB", "descricao": "Rua fica intransitavel em dias de chuva e voltou a pressionar a base.", "prioridade": "ALTA", "status": "EM_ATENDIMENTO", "responsavel_usuario_id": SUP_CENTRO_ID, "equipe_id": TEAM_CENTRO_ID, "gerada_por_usuario_id": SUP_CENTRO_ID, "origem_cadastro": "MOBILE_CAMPO", "sla_data": "2026-04-26T18:00:00Z", "data_abertura": "2026-04-22T10:45:00Z", "data_conclusao": None, "tags": ["alagamento", "drenagem"], "anexos": [], "created_at": "2026-04-22T10:45:00Z", "updated_at": now},
            {"id": "50000000-0000-4000-8000-000000000012", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000005", "territorio_id": ALTEROSAS_ID, "categoria_id": CATEGORY_SOCIAL_ID, "titulo": "Aumento de familias sem acolhimento imediato em Alterosas", "descricao": "Rede local relata crescimento de casos e demora no atendimento social.", "prioridade": "CRITICA", "status": "ABERTA", "responsavel_usuario_id": SUP_ALTEROSAS_ID, "equipe_id": TEAM_ALTEROSAS_ID, "gerada_por_usuario_id": SUP_ALTEROSAS_ID, "origem_cadastro": "WEB_INTERNO", "sla_data": "2026-04-24T18:00:00Z", "data_abertura": "2026-04-22T12:20:00Z", "data_conclusao": None, "tags": ["assistencia", "acolhimento"], "anexos": [], "created_at": "2026-04-22T12:20:00Z", "updated_at": now},
            {"id": "50000000-0000-4000-8000-000000000013", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000012", "territorio_id": IMBIRUCU_ID, "categoria_id": CATEGORY_MOBILIDADE_ID, "titulo": "Iluminacao do entorno do campo ainda insuficiente", "descricao": "Mesmo apos intervencao, comunidade pede reforco em acessos laterais.", "prioridade": "MEDIA", "status": "REABERTA", "responsavel_usuario_id": ASSESSOR_ALTEROSAS_ID, "equipe_id": TEAM_ALTEROSAS_ID, "gerada_por_usuario_id": ASSESSOR_ALTEROSAS_ID, "origem_cadastro": "MOBILE_CAMPO", "sla_data": "2026-04-27T18:00:00Z", "data_abertura": "2026-04-22T13:00:00Z", "data_conclusao": None, "tags": ["iluminacao", "juventude"], "anexos": [], "created_at": "2026-04-22T13:00:00Z", "updated_at": now},
        ]
    )

    state["historico_demanda"].extend(
        [
            {"id": "51000000-0000-4000-8000-000000000005", "demanda_id": "50000000-0000-4000-8000-000000000009", "usuario_id": SUP_NORTE_ID, "acao": "CREATE", "status_anterior": None, "status_novo": "ABERTA", "observacao": "Pressao de saude escalada para prioridade critica.", "dados_json": {}, "created_at": "2026-04-22T08:25:00Z"},
            {"id": "51000000-0000-4000-8000-000000000006", "demanda_id": "50000000-0000-4000-8000-000000000012", "usuario_id": SUP_ALTEROSAS_ID, "acao": "CREATE", "status_anterior": None, "status_novo": "ABERTA", "observacao": "Casos sociais cresceram acima da capacidade atual de acolhimento.", "dados_json": {}, "created_at": "2026-04-22T12:20:00Z"},
            {"id": "51000000-0000-4000-8000-000000000007", "demanda_id": "50000000-0000-4000-8000-000000000013", "usuario_id": ASSESSOR_ALTEROSAS_ID, "acao": "REABERTURA", "status_anterior": "CONCLUIDA", "status_novo": "REABERTA", "observacao": "Entrega parcial gerou nova rodada de cobranca comunitaria.", "dados_json": {}, "created_at": "2026-04-22T13:00:00Z"},
        ]
    )

    state["agenda_eventos"].extend(
        [
            {"id": "60000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "territorio_id": PTB_ID, "tipo_agenda_id": None, "tipo_agenda": "AUDIENCIA_PUBLICA", "demanda_id": "50000000-0000-4000-8000-000000000011", "titulo": "Escuta sobre drenagem e alagamentos no PTB", "descricao": "Reuniao ampliada para resposta tecnica e politica sobre drenagem.", "status": "CONFIRMADO", "data_inicio": "2026-04-27T18:30:00Z", "data_fim": "2026-04-27T20:00:00Z", "local_texto": "Escola estadual do PTB", "responsavel_usuario_id": SUP_CENTRO_ID, "eh_agenda_vereador": True, "participantes": [{"cidadao_id": "40000000-0000-4000-8000-000000000011", "tipo_participante": "EXTERNO"}], "publico_estimado": 90, "relatorio_execucao": None, "anexos": [], "created_at": "2026-04-23T08:40:00Z", "updated_at": now},
            {"id": "60000000-0000-4000-8000-000000000005", "gabinete_id": GABINETE_ID, "territorio_id": NORTE_ID, "tipo_agenda_id": None, "tipo_agenda": "VISITA_UNIDADE", "demanda_id": "50000000-0000-4000-8000-000000000009", "titulo": "Visita do vereador a unidade de saude do Norte", "descricao": "Checagem de fluxo, acolhimento e posicionamento para a comunidade.", "status": "PENDENTE", "data_inicio": "2026-04-24T15:00:00Z", "data_fim": "2026-04-24T16:30:00Z", "local_texto": "UBS Regional Norte", "responsavel_usuario_id": SUP_NORTE_ID, "eh_agenda_vereador": True, "participantes": [{"cidadao_id": "40000000-0000-4000-8000-000000000009", "tipo_participante": "EXTERNO"}], "publico_estimado": 40, "relatorio_execucao": None, "anexos": [], "created_at": "2026-04-23T08:55:00Z", "updated_at": now},
        ]
    )

    state["interacoes"].extend(
        [
            {"id": "70000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000009", "demanda_id": "50000000-0000-4000-8000-000000000009", "agenda_evento_id": "60000000-0000-4000-8000-000000000005", "canal_contato": "WHATSAPP", "tipo_interacao": "ALERTA_BASE", "assunto": "Escalada de pressao na UBS do Norte", "descricao_detalhada": "Relatos apontam risco de desgaste politico se nao houver presenca imediata do vereador.", "status": "REGISTRADA", "prioridade": "CRITICA", "responsavel_usuario_id": SUP_NORTE_ID, "origem_demanda": "BASE_TERRITORIAL", "indicacao_de_quem": None, "resultado": "Tema passou a liderar o radar territorial.", "proxima_acao": "Levar vereador para visita e alinhar cobranca publica.", "data_contato": "2026-04-23T09:00:00Z", "data_proxima_acao": "2026-04-24T15:00:00Z", "observacoes": "Tom da base ficou mais duro nas ultimas horas.", "created_at": "2026-04-23T09:00:00Z", "updated_at": now},
            {"id": "70000000-0000-4000-8000-000000000005", "gabinete_id": GABINETE_ID, "cidadao_id": "40000000-0000-4000-8000-000000000011", "demanda_id": "50000000-0000-4000-8000-000000000011", "agenda_evento_id": "60000000-0000-4000-8000-000000000004", "canal_contato": "PRESENCIAL", "tipo_interacao": "ESCUTA_COMUNITARIA", "assunto": "Alagamentos e drenagem no PTB", "descricao_detalhada": "Comunidade quer cronograma visivel e cobranca mais firme do Executivo.", "status": "REGISTRADA", "prioridade": "ALTA", "responsavel_usuario_id": SUP_CENTRO_ID, "origem_demanda": "BASE_TERRITORIAL", "indicacao_de_quem": None, "resultado": "Audiência publica virou prioridade da semana.", "proxima_acao": "Consolidar memoria com imagens e protocolo tecnico.", "data_contato": "2026-04-23T10:45:00Z", "data_proxima_acao": "2026-04-25T09:00:00Z", "observacoes": "Base quer resposta concreta, nao so visita.", "created_at": "2026-04-23T10:45:00Z", "updated_at": now},
        ]
    )

    state["oficios"].extend(
        [
            {"id": "91000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000009", "numero": "OF-2026-052", "titulo": "Solicitacao urgente sobre pediatria e acolhimento na UBS Norte", "assunto": "Saude - Regional Norte", "orgao_destino": "Secretaria Municipal de Saude", "status": "ENVIADO", "data_envio": "2026-04-23T09:20:00Z", "prazo_resposta": "2026-04-24T18:00:00Z", "responsavel_usuario_id": SUP_NORTE_ID, "resposta": None, "follow_up": "Sem resposta, vereador deve cobrar publicamente na visita tecnica.", "created_at": "2026-04-23T09:20:00Z", "updated_at": now},
            {"id": "91000000-0000-4000-8000-000000000005", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000011", "numero": "OF-2026-053", "titulo": "Pedido de plano emergencial de drenagem no PTB", "assunto": "Infraestrutura - PTB", "orgao_destino": "Secretaria Municipal de Obras", "status": "AGUARDANDO_RETORNO", "data_envio": "2026-04-23T11:00:00Z", "prazo_resposta": "2026-04-28T18:00:00Z", "responsavel_usuario_id": SUP_CENTRO_ID, "resposta": None, "follow_up": "Levar tema para audiencia se nao houver cronograma oficial.", "created_at": "2026-04-23T11:00:00Z", "updated_at": now},
        ]
    )

    state["sentimento_social"].extend(
        [
            {"id": "92000000-0000-4000-8000-000000000005", "gabinete_id": GABINETE_ID, "canal": "WHATSAPP", "periodo": "24H", "tema": "Pediatria e exames", "positivo": 10, "neutro": 20, "negativo": 70, "alerta": "Base do Norte endureceu o tom e cobra presenca imediata do vereador.", "territorio_id": NORTE_ID, "territorio_nome": "Regional Norte", "coletado_em": "2026-04-23T13:00:00Z", "created_at": "2026-04-23T13:00:00Z", "updated_at": now},
            {"id": "92000000-0000-4000-8000-000000000006", "gabinete_id": GABINETE_ID, "canal": "FACEBOOK", "periodo": "24H", "tema": "Drenagem e alagamentos", "positivo": 14, "neutro": 22, "negativo": 64, "alerta": "PTB concentra relatos de desgaste por promessas antigas ainda sem entrega.", "territorio_id": PTB_ID, "territorio_nome": "Regional PTB", "coletado_em": "2026-04-23T12:45:00Z", "created_at": "2026-04-23T12:45:00Z", "updated_at": now},
            {"id": "92000000-0000-4000-8000-000000000007", "gabinete_id": GABINETE_ID, "canal": "INSTAGRAM", "periodo": "24H", "tema": "Acolhimento social", "positivo": 16, "neutro": 26, "negativo": 58, "alerta": "Alterosas cobra capacidade de resposta e visibilidade da agenda social.", "territorio_id": ALTEROSAS_ID, "territorio_nome": "Regional Alterosas", "coletado_em": "2026-04-23T12:30:00Z", "created_at": "2026-04-23T12:30:00Z", "updated_at": now},
            {"id": "92000000-0000-4000-8000-000000000008", "gabinete_id": GABINETE_ID, "canal": "INSTAGRAM", "periodo": "7D", "tema": "Recapeamento e drenagem", "positivo": 21, "neutro": 29, "negativo": 50, "alerta": "Centro segue responsivo, mas ha fadiga com prazo e entrega parcial.", "territorio_id": CENTRO_ID, "territorio_nome": "Regional Centro", "coletado_em": "2026-04-23T12:20:00Z", "created_at": "2026-04-23T12:20:00Z", "updated_at": now},
        ]
    )

    state["tarefas"].extend(
        [
            {"id": "96000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000009", "protocolo_id": None, "projeto_id": "97000000-0000-4000-8000-000000000001", "titulo": "Montar briefing duro para visita a UBS Norte", "descricao": "Separar dados de fila, relatos e mensagem politica para resposta publica.", "responsavel_usuario_id": COORD_ID, "prioridade": "ALTA", "status": "ABERTA", "data_limite": "2026-04-24T11:00:00Z", "data_conclusao": None, "created_at": "2026-04-23T09:30:00Z", "updated_at": now},
            {"id": "96000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000011", "protocolo_id": None, "projeto_id": "97000000-0000-4000-8000-000000000002", "titulo": "Fechar dossiê de drenagem do PTB", "descricao": "Consolidar fotos, pontos criticos e historico de cobrancas.", "responsavel_usuario_id": SUP_CENTRO_ID, "prioridade": "ALTA", "status": "EM_ANDAMENTO", "data_limite": "2026-04-25T14:00:00Z", "data_conclusao": None, "created_at": "2026-04-23T10:50:00Z", "updated_at": now},
        ]
    )

    state["sync_mobile"].append(
        {"id": "98000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "usuario_id": SUP_NORTE_ID, "tipo": "UPLOAD", "status": "SUCESSO", "resumo": "9 alertas criticos adicionais consolidados da Regional Norte.", "created_at": "2026-04-23T12:05:00Z", "updated_at": "2026-04-23T12:05:00Z"}
    )

    state["notificacoes"].extend(
        [
            {"id": "99000000-0000-4000-8000-000000000003", "gabinete_id": GABINETE_ID, "usuario_id": CHEFE_ID, "titulo": "Fila da saude virou tema dominante", "mensagem": "Sentimento do Norte piorou e ja pede presenca direta do vereador.", "lida": False, "created_at": "2026-04-23T13:05:00Z", "updated_at": now},
            {"id": "99000000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "usuario_id": CHEFE_ID, "titulo": "PTB entrou em alerta por drenagem", "mensagem": "Comunidade quer cronograma oficial e audiencia com resposta tecnica.", "lida": False, "created_at": "2026-04-23T13:10:00Z", "updated_at": now},
        ]
    )

    state["sla_historico"].extend(
        [
            {"id": "99600000-0000-4000-8000-000000000004", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000009", "status": "VENCIDO", "horas_decorridas": 31, "created_at": "2026-04-23T12:40:00Z", "updated_at": now},
            {"id": "99600000-0000-4000-8000-000000000005", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000011", "status": "EM_RISCO", "horas_decorridas": 20, "created_at": "2026-04-23T12:20:00Z", "updated_at": now},
            {"id": "99600000-0000-4000-8000-000000000006", "gabinete_id": GABINETE_ID, "demanda_id": "50000000-0000-4000-8000-000000000012", "status": "VENCIDO", "horas_decorridas": 29, "created_at": "2026-04-23T12:25:00Z", "updated_at": now},
        ]
    )

    state["auditoria"] = [
        {"id": "99700000-0000-4000-8000-000000000001", "gabinete_id": GABINETE_ID, "usuario_id": CHEFE_ID, "entidade": "base", "entidade_id": GABINETE_ID, "acao": "RESET_PRESENTATION_DATA", "payload_anterior": None, "payload_novo": {"motivo": "Preparacao de base para apresentacao ao vereador.", "contatos": len(state["contatos"]), "demandas": len(state["demandas"]), "equipes": len(state["equipes"])}, "created_at": now}
    ]

    return state


def main() -> None:
    state = build_state()
    DB_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Base redefinida em {DB_PATH}")
    print(
        "Resumo:",
        json.dumps(
            {
                "usuarios": len(state["usuarios"]),
                "equipes": len(state["equipes"]),
                "territorios": len(state["territorios"]),
                "contatos": len(state["contatos"]),
                "demandas": len(state["demandas"]),
                "agenda": len(state["agenda_eventos"]),
                "sentimento_social": len(state["sentimento_social"]),
            },
            ensure_ascii=False,
        ),
    )


if __name__ == "__main__":
    main()