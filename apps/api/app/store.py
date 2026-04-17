from __future__ import annotations

import copy
import json
import threading
import uuid
from pathlib import Path
from typing import Any

from .auth import hash_password, iso_now


COLLECTIONS = (
    "gabinetes",
    "usuarios",
    "equipes",
    "auditoria",
    "territorios",
    "contatos",
    "consentimentos",
    "categorias_demanda",
    "demandas",
    "historico_demanda",
    "encaminhamentos",
    "agenda_eventos",
    "interacoes",
    "proposicoes",
    "emendas",
    "oficios",
    "sentimento_social",
    "editais_convenios",
    "documentos",
    "protocolos",
    "tarefas",
    "projetos",
    "uploads",
    "sync_mobile",
    "notificacoes",
)


GABINETE_ID = "00000000-0000-4000-8000-000000000001"
TEAM_ID = "00000000-0000-4000-8000-000000000011"
CHEFE_ID = "00000000-0000-4000-8000-000000000101"
ASSESSOR_ID = "00000000-0000-4000-8000-000000000102"
REGIAO_ID = "00000000-0000-4000-8000-000000000201"
BAIRRO_ID = "00000000-0000-4000-8000-000000000202"
MICRO_ID = "00000000-0000-4000-8000-000000000203"
CONTATO_ID = "00000000-0000-4000-8000-000000000301"
CATEGORIA_ID = "00000000-0000-4000-8000-000000000401"
DEMANDA_ID = "00000000-0000-4000-8000-000000000501"
AGENDA_ID = "00000000-0000-4000-8000-000000000601"
DOC_ID = "00000000-0000-4000-8000-000000000701"
PROTOCOLO_ID = "00000000-0000-4000-8000-000000000801"
TAREFA_ID = "00000000-0000-4000-8000-000000000901"
PROJETO_ID = "00000000-0000-4000-8000-000000001001"
INTERACAO_ID = "00000000-0000-4000-8000-000000001101"
PROPOSICAO_ID = "00000000-0000-4000-8000-000000001201"
EMENDA_ID = "00000000-0000-4000-8000-000000001301"
OFICIO_ID = "00000000-0000-4000-8000-000000001401"
SENTIMENTO_ID = "00000000-0000-4000-8000-000000001501"
CONVENIO_ID = "00000000-0000-4000-8000-000000001601"


def new_id() -> str:
    return str(uuid.uuid4())


def seed_state() -> dict[str, list[dict[str, Any]]]:
    now = iso_now()
    return {
        "gabinetes": [
            {
                "id": GABINETE_ID,
                "nome": "Gabinete IA Demo",
                "sigla": "GIA",
                "descricao": "Base inicial gerada a partir dos contratos oficiais.",
                "ativo": True,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "equipes": [
            {
                "id": TEAM_ID,
                "gabinete_id": GABINETE_ID,
                "nome": "Equipe Centro",
                "descricao": "Equipe territorial do centro",
                "supervisor_usuario_id": ASSESSOR_ID,
                "ativo": True,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "usuarios": [
            {
                "id": CHEFE_ID,
                "gabinete_id": GABINETE_ID,
                "equipe_id": None,
                "nome": "Maria Souza",
                "email_login": "chefe@gabineteia.local",
                "telefone": "31999990000",
                "senha_hash": hash_password("Senha@123"),
                "perfil": "CHEFE_GABINETE",
                "ultimo_login": None,
                "mfa_habilitado": False,
                "ativo": True,
                "escopos": [{"id": new_id(), "escopo_tipo": "GABINETE", "escopo_valor": GABINETE_ID}],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": ASSESSOR_ID,
                "gabinete_id": GABINETE_ID,
                "equipe_id": TEAM_ID,
                "nome": "Carlos Lima",
                "email_login": "assessor@gabineteia.local",
                "telefone": "31999991111",
                "senha_hash": hash_password("Senha@123"),
                "perfil": "ASSESSOR_NIVEL_1",
                "ultimo_login": None,
                "mfa_habilitado": False,
                "ativo": True,
                "escopos": [{"id": new_id(), "escopo_tipo": "TERRITORIO", "territorio_id": BAIRRO_ID}],
                "created_at": now,
                "updated_at": now,
            },
        ],
        "auditoria": [],
        "territorios": [
            {
                "id": REGIAO_ID,
                "gabinete_id": GABINETE_ID,
                "parent_id": None,
                "nome": "Regiao Centro",
                "tipo": "REGIAO",
                "codigo_externo": "REG-CENTRO",
                "ativo": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": BAIRRO_ID,
                "gabinete_id": GABINETE_ID,
                "parent_id": REGIAO_ID,
                "nome": "Centro",
                "tipo": "BAIRRO",
                "codigo_externo": "BAI-CENTRO",
                "ativo": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": MICRO_ID,
                "gabinete_id": GABINETE_ID,
                "parent_id": BAIRRO_ID,
                "nome": "Microarea 1",
                "tipo": "MICROAREA",
                "codigo_externo": "MIC-001",
                "ativo": True,
                "created_at": now,
                "updated_at": now,
            },
        ],
        "contatos": [
            {
                "id": CONTATO_ID,
                "gabinete_id": GABINETE_ID,
                "territorio_id": BAIRRO_ID,
                "origem_cadastro": "WEB_INTERNO",
                "nome": "Maria da Silva",
                "cpf": None,
                "data_nascimento": None,
                "telefone_principal": "31999999999",
                "telefone_secundario": None,
                "email": "maria@example.com",
                "logradouro": "Rua A",
                "numero": "10",
                "complemento": None,
                "bairro": "Centro",
                "cidade": "Betim",
                "cep": "32600000",
                "tipo_contato": "CIDADAO",
                "status": "ATIVO",
                "duplicidade_suspeita": False,
                "nivel_relacionamento": "PARTICIPANTE",
                "influencia": "MEDIA",
                "engajamento": "MEDIO",
                "voto_2028": "INDEFINIDO",
                "prioridade_politica": "MEDIA",
                "origem_politica": "DECLARADO",
                "observacoes": "Contato inicial de demonstracao",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "consentimentos": [
            {
                "id": new_id(),
                "cidadao_id": CONTATO_ID,
                "canal": "WHATSAPP",
                "consentido": True,
                "finalidade": "atendimento institucional",
                "forma_registro": "verbal",
                "observacao": "Autorizado no atendimento presencial",
                "registrado_em": now,
                "registrado_por": ASSESSOR_ID,
            }
        ],
        "categorias_demanda": [
            {
                "id": CATEGORIA_ID,
                "gabinete_id": GABINETE_ID,
                "nome": "Urbana",
                "descricao": "Demandas urbanas e zeladoria",
                "ativo": True,
            }
        ],
        "demandas": [
            {
                "id": DEMANDA_ID,
                "gabinete_id": GABINETE_ID,
                "cidadao_id": CONTATO_ID,
                "territorio_id": BAIRRO_ID,
                "categoria_id": CATEGORIA_ID,
                "titulo": "Solicitacao de poda de arvore",
                "descricao": "Arvore com risco em frente a residencia.",
                "prioridade": "ALTA",
                "status": "EM_TRIAGEM",
                "responsavel_usuario_id": None,
                "origem_cadastro": "WEB_INTERNO",
                "sla_data": None,
                "data_abertura": now,
                "data_conclusao": None,
                "tags": [],
                "anexos": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "historico_demanda": [
            {
                "id": new_id(),
                "demanda_id": DEMANDA_ID,
                "usuario_id": ASSESSOR_ID,
                "acao": "CREATE",
                "status_anterior": None,
                "status_novo": "EM_TRIAGEM",
                "observacao": "Demanda criada na carga inicial.",
                "dados_json": {},
                "created_at": now,
            }
        ],
        "encaminhamentos": [],
        "agenda_eventos": [
            {
                "id": AGENDA_ID,
                "gabinete_id": GABINETE_ID,
                "territorio_id": BAIRRO_ID,
                "tipo_agenda_id": None,
                "tipo_agenda": "REUNIAO_BASE",
                "demanda_id": DEMANDA_ID,
                "titulo": "Reuniao com associacao",
                "descricao": "Alinhamento institucional",
                "status": "CONFIRMADO",
                "data_inicio": now,
                "data_fim": now,
                "local_texto": "Associacao do Centro",
                "responsavel_usuario_id": ASSESSOR_ID,
                "eh_agenda_vereador": True,
                "participantes": [{"cidadao_id": CONTATO_ID, "tipo_participante": "EXTERNO"}],
                "publico_estimado": 12,
                "relatorio_execucao": None,
                "anexos": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "interacoes": [
            {
                "id": INTERACAO_ID,
                "gabinete_id": GABINETE_ID,
                "cidadao_id": CONTATO_ID,
                "demanda_id": DEMANDA_ID,
                "agenda_evento_id": AGENDA_ID,
                "canal_contato": "PRESENCIAL",
                "tipo_interacao": "REUNIAO_BASE",
                "assunto": "Poda de arvore e zeladoria",
                "descricao_detalhada": "Contato registrado durante reuniao da associacao; demanda aberta para acompanhar retorno do Executivo.",
                "status": "REGISTRADA",
                "prioridade": "ALTA",
                "responsavel_usuario_id": ASSESSOR_ID,
                "origem_demanda": "BASE_TERRITORIAL",
                "indicacao_de_quem": None,
                "resultado": "Demanda protocolada e aguardando encaminhamento.",
                "proxima_acao": "Gerar oficio para secretaria responsavel.",
                "data_contato": now,
                "data_proxima_acao": now,
                "observacoes": "Registro inicial do CRM politico.",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "proposicoes": [
            {
                "id": PROPOSICAO_ID,
                "gabinete_id": GABINETE_ID,
                "titulo": "Projeto de lei de manutencao preventiva de arvores urbanas",
                "tipo": "PROJETO_LEI",
                "numero": "PL 12/2026",
                "tema": "Zeladoria urbana",
                "status": "COMISSAO",
                "etapa_kanban": "COMISSAO",
                "relator": "Comissao de Meio Ambiente",
                "prazo": now,
                "posicionamento": "FAVORAVEL",
                "justificativa_tecnica": "Resposta legislativa a demandas recorrentes de risco em vias publicas.",
                "discursos": [],
                "tags": ["zeladoria", "meio ambiente"],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "emendas": [
            {
                "id": EMENDA_ID,
                "gabinete_id": GABINETE_ID,
                "numero": "EMD-2026-001",
                "titulo": "Equipamentos para manutencao urbana",
                "tipo_emenda": "INDIVIDUAL",
                "area": "Infraestrutura",
                "beneficiario": "Secretaria Municipal de Obras",
                "territorio_id": BAIRRO_ID,
                "objeto": "Aquisicao de equipamentos para podas preventivas e manutencao de pracas.",
                "valor_indicado": 250000.0,
                "valor_empenhado": 180000.0,
                "valor_liquidado": 90000.0,
                "valor_pago": 45000.0,
                "status_execucao": "LIQUIDACAO",
                "data_indicacao": now,
                "data_ultima_movimentacao": now,
                "latitude": -19.9676,
                "longitude": -44.1986,
                "documentos": [],
                "fotos": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "oficios": [
            {
                "id": OFICIO_ID,
                "gabinete_id": GABINETE_ID,
                "demanda_id": DEMANDA_ID,
                "numero": "OF-2026-001",
                "titulo": "Solicitacao de vistoria e poda preventiva",
                "assunto": "Zeladoria urbana",
                "orgao_destino": "Secretaria Municipal de Meio Ambiente",
                "status": "ENVIADO",
                "data_envio": "2026-03-25T09:00:00+00:00",
                "prazo_resposta": "2026-04-09T18:00:00+00:00",
                "responsavel_usuario_id": ASSESSOR_ID,
                "resposta": None,
                "follow_up": "Cobrar retorno apos 15 dias sem resposta.",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "sentimento_social": [
            {
                "id": SENTIMENTO_ID,
                "gabinete_id": GABINETE_ID,
                "canal": "INSTAGRAM",
                "periodo": "24H",
                "tema": "Zeladoria urbana",
                "positivo": 54,
                "neutro": 31,
                "negativo": 15,
                "alerta": "Comentarios cobram retorno rapido em bairros com maior volume de demandas.",
                "coletado_em": now,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "editais_convenios": [
            {
                "id": CONVENIO_ID,
                "gabinete_id": GABINETE_ID,
                "titulo": "Edital de infraestrutura comunitaria",
                "orgao": "Ministerio das Cidades",
                "status": "OPORTUNIDADE",
                "prazo": now,
                "municipio_alvo": "Betim",
                "valor_estimado": 500000.0,
                "responsavel_usuario_id": CHEFE_ID,
                "observacoes": "Monitorar documentacao da prefeitura aliada.",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "documentos": [
            {
                "id": DOC_ID,
                "gabinete_id": GABINETE_ID,
                "tipo": "PARECER",
                "titulo": "Parecer sobre demanda inicial",
                "status": "RASCUNHO",
                "versao_atual": 1,
                "autor_usuario_id": CHEFE_ID,
                "demanda_id": DEMANDA_ID,
                "protocolo_id": None,
                "projeto_id": None,
                "tema": "Regularidade administrativa",
                "ementa": "Analise preliminar",
                "conteudo_texto": "Texto inicial do parecer.",
                "versoes": [
                    {
                        "id": new_id(),
                        "numero_versao": 1,
                        "resumo_alteracao": "Versao inicial",
                        "created_at": now,
                    }
                ],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "protocolos": [
            {
                "id": PROTOCOLO_ID,
                "gabinete_id": GABINETE_ID,
                "tipo_protocolo_id": None,
                "documento_id": DOC_ID,
                "numero": "2026-001",
                "titulo": "Protocolo administrativo inicial",
                "status": "REGISTRADO",
                "responsavel_usuario_id": ASSESSOR_ID,
                "prazo_final": None,
                "origem": "INTERNA",
                "observacoes": "Acompanhamento administrativo",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "tarefas": [
            {
                "id": TAREFA_ID,
                "gabinete_id": GABINETE_ID,
                "demanda_id": DEMANDA_ID,
                "protocolo_id": None,
                "projeto_id": None,
                "titulo": "Retornar ligacao para cidada",
                "descricao": "Contato para atualizacao de andamento",
                "responsavel_usuario_id": ASSESSOR_ID,
                "prioridade": "MEDIA",
                "status": "ABERTA",
                "data_limite": None,
                "data_conclusao": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "projetos": [
            {
                "id": PROJETO_ID,
                "gabinete_id": GABINETE_ID,
                "territorio_id": BAIRRO_ID,
                "nome": "Projeto Mobilidade Centro",
                "descricao": "Iniciativa para acompanhamento de pautas de mobilidade",
                "status": "PLANEJADO",
                "responsavel_usuario_id": ASSESSOR_ID,
                "prioritario": True,
                "data_inicio": None,
                "data_fim_prevista": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "uploads": [],
        "sync_mobile": [],
        "notificacoes": [],
    }


class JsonStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.RLock()
        self.state: dict[str, list[dict[str, Any]]] = {}
        self.load()

    def load(self) -> None:
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.state = seed_state()
                self.save()
                return
            with self.path.open("r", encoding="utf-8") as fp:
                self.state = json.load(fp)
            defaults = seed_state()
            changed = False
            for collection in COLLECTIONS:
                if collection not in self.state:
                    self.state[collection] = copy.deepcopy(defaults.get(collection, []))
                    changed = True
            if changed:
                self.save()

    def save(self) -> None:
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as fp:
                json.dump(self.state, fp, ensure_ascii=False, indent=2)
            tmp.replace(self.path)

    def all(self, collection: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self.state.setdefault(collection, []))

    def get(self, collection: str, item_id: str) -> dict[str, Any] | None:
        for item in self.state.setdefault(collection, []):
            if item.get("id") == item_id:
                return copy.deepcopy(item)
        return None

    def find_one(self, collection: str, **filters: Any) -> dict[str, Any] | None:
        for item in self.state.setdefault(collection, []):
            if all(item.get(key) == value for key, value in filters.items()):
                return copy.deepcopy(item)
        return None

    def create(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            item = copy.deepcopy(payload)
            item.setdefault("id", new_id())
            item.setdefault("created_at", iso_now())
            item.setdefault("updated_at", item.get("created_at"))
            self.state.setdefault(collection, []).append(item)
            self.save()
            return copy.deepcopy(item)

    def update(self, collection: str, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        with self.lock:
            for index, item in enumerate(self.state.setdefault(collection, [])):
                if item.get("id") == item_id:
                    updated = copy.deepcopy(item)
                    updated.update(copy.deepcopy(patch))
                    updated["id"] = item_id
                    updated["updated_at"] = iso_now()
                    self.state[collection][index] = updated
                    self.save()
                    return copy.deepcopy(updated)
        return None

    def append_child(self, collection: str, item_id: str, field: str, value: dict[str, Any]) -> dict[str, Any] | None:
        with self.lock:
            for item in self.state.setdefault(collection, []):
                if item.get("id") == item_id:
                    item.setdefault(field, []).append(copy.deepcopy(value))
                    item["updated_at"] = iso_now()
                    self.save()
                    return copy.deepcopy(item)
        return None

    def audit(
        self,
        gabinete_id: str,
        usuario_id: str | None,
        entidade: str,
        entidade_id: str | None,
        acao: str,
        payload_anterior: dict[str, Any] | None = None,
        payload_novo: dict[str, Any] | None = None,
    ) -> None:
        self.state.setdefault("auditoria", []).append(
            {
                "id": new_id(),
                "gabinete_id": gabinete_id,
                "usuario_id": usuario_id,
                "entidade": entidade,
                "entidade_id": entidade_id,
                "acao": acao,
                "payload_anterior": payload_anterior,
                "payload_novo": payload_novo,
                "created_at": iso_now(),
            }
        )
        self.save()
