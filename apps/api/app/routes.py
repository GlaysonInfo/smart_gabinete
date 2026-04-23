from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from .auth import create_token, hash_password, iso_now, verify_password
from .config import settings
from .deps import get_current_user, get_store
from .http import paginated, success
from .store import JsonStore, new_id


router = APIRouter()


def page_params(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    return max(1, page), min(max(1, page_size), 100)


def parse_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "sim", "yes", "ativo"}


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in user.items() if key != "senha_hash"}


def normalize_public_asset_url(value: str | None) -> str | None:
    if not value:
        return None
    rendered = str(value).replace("\\", "/").strip()
    if not rendered:
        return None
    if rendered.startswith(("http://", "https://", "/uploads-public/")):
        return rendered
    if rendered.startswith("data/uploads/"):
        return f"/uploads-public/{Path(rendered).name}"
    if "/" not in rendered:
        return f"/uploads-public/{rendered}"
    return rendered if rendered.startswith("/") else f"/{rendered.lstrip('/')}"


def upload_public_url(upload: dict[str, Any] | None) -> str | None:
    if not upload:
        return None
    return (
        normalize_public_asset_url(upload.get("url_publica"))
        or normalize_public_asset_url(upload.get("url_storage"))
        or normalize_public_asset_url(upload.get("nome_storage"))
    )


def token_bundle(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "access_token": create_token(user, "access"),
        "refresh_token": create_token(user, "refresh"),
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
    }


def list_response(
    request: Request,
    collection: str,
    repo: JsonStore,
    query: dict[str, Any],
    search_fields: tuple[str, ...],
    enrich=None,
) -> dict[str, Any]:
    page, page_size = page_params(int(query.get("page") or 1), int(query.get("page_size") or 20))
    items = repo.all(collection)
    search = (query.get("search") or "").strip().lower()
    if search:
        items = [
            item
            for item in items
            if any(search in str(item.get(field, "")).lower() for field in search_fields)
        ]

    ignored = {
        "page",
        "page_size",
        "sort_by",
        "sort_order",
        "search",
        "date_from",
        "date_to",
        "request",
        "repo",
        "current_user",
    }
    for key, value in query.items():
        if key in ignored or value in (None, ""):
            continue
        if key in {"ativo", "duplicidade_suspeita", "prioritario", "eh_agenda_vereador"}:
            bool_value = parse_bool(value)
            items = [item for item in items if item.get(key) is bool_value]
            continue
        items = [item for item in items if str(item.get(key)) == str(value)]

    date_from = query.get("date_from")
    date_to = query.get("date_to")
    if date_from or date_to:
        date_fields = ("created_at", "data_abertura", "data_inicio", "data_evento")
        filtered = []
        for item in items:
            date_value = next((item.get(field) for field in date_fields if item.get(field)), "")
            if date_from and date_value < date_from:
                    continue
            if date_to and date_value > date_to:
                continue
            filtered.append(item)
        items = filtered

    sort_by = query.get("sort_by") or "created_at"
    reverse = (query.get("sort_order") or "desc").lower() == "desc"
    items.sort(key=lambda item: str(item.get(sort_by, "")), reverse=reverse)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    if enrich:
        page_items = [enrich(item) for item in page_items]
    return paginated(request, page_items, page, page_size, total)


def not_found(entity: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} nao encontrado.")


def conflict(message: str) -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def business_rule(message: str) -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)


def require_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campos obrigatorios: {', '.join(missing)}.",
        )


def territory_name(repo: JsonStore, territory_id: str | None) -> str | None:
    if not territory_id:
        return None
    territory = repo.get("territorios", territory_id)
    return territory.get("nome") if territory else None


def user_name(repo: JsonStore, user_id: str | None) -> str | None:
    if not user_id:
        return None
    user = repo.get("usuarios", user_id)
    return user.get("nome") if user else None


def contact_name(repo: JsonStore, contact_id: str | None) -> str | None:
    if not contact_id:
        return None
    contact = repo.get("contatos", contact_id)
    return contact.get("nome") if contact else None


def category_name(repo: JsonStore, category_id: str | None) -> str | None:
    if not category_id:
        return None
    category = repo.get("categorias_demanda", category_id)
    return category.get("nome") if category else None


def normalized_territory_key(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
    normalized = normalized.replace("-", " ").strip()
    for prefix in ("regional ", "regiao "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return " ".join(normalized.split())


def territory_scope_matches(left: str | None, right: str | None) -> bool:
    left_key = normalized_territory_key(left)
    right_key = normalized_territory_key(right)
    return bool(left_key and right_key and left_key == right_key)


def resolve_heatmap_scope(
    territory_name: str | None,
    formal_territories_by_key: dict[str, dict[str, Any]],
) -> tuple[str, str | None, str | None, str]:
    fallback_name = territory_name or "Sem territorio"
    key = normalized_territory_key(fallback_name) or "sem territorio"
    formal = formal_territories_by_key.get(key)
    if formal:
        return formal.get("nome") or fallback_name, formal.get("id"), formal.get("tipo"), key
    return fallback_name, None, None, key


def ensure_heatmap_bucket(
    buckets: dict[str, dict[str, Any]],
    key: str,
    territory_name: str,
    territory_id: str | None = None,
    territory_type: str | None = None,
) -> dict[str, Any]:
    bucket = buckets.setdefault(
        key,
        {
            "territorio_id": territory_id,
            "territorio_nome": territory_name,
            "tipo": territory_type,
            "demandas": 0,
            "contatos": 0,
            "liderancas": 0,
            "score": 0,
        },
    )
    if territory_type == "REGIAO" or bucket.get("territorio_id") is None:
        if territory_id is not None:
            bucket["territorio_id"] = territory_id
        if territory_name:
            bucket["territorio_nome"] = territory_name
        if territory_type:
            bucket["tipo"] = territory_type
    return bucket


def active_contact(item: dict[str, Any]) -> bool:
    return item.get("status") not in {"EXCLUIDO", "INATIVO"}


def is_leadership_contact(item: dict[str, Any]) -> bool:
    return item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"


def is_strong_engagement_contact(item: dict[str, Any]) -> bool:
    return item.get("engajamento") in {"FORTE", "ALTO"}


def enrich_contact(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    photo_upload = repo.get("uploads", enriched.get("foto_upload_id")) if enriched.get("foto_upload_id") else None
    linked_user = repo.get("usuarios", enriched.get("usuario_id")) if enriched.get("usuario_id") else None
    user_photo_upload = repo.get("uploads", linked_user.get("foto_upload_id")) if linked_user and linked_user.get("foto_upload_id") else None
    linked_team = repo.get("equipes", enriched.get("equipe_id")) if enriched.get("equipe_id") else None
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    enriched["equipe_nome"] = linked_team.get("nome") if linked_team else None
    enriched["cadastrado_por_nome"] = user_name(repo, enriched.get("cadastrado_por_usuario_id"))
    enriched["foto_url_publica"] = upload_public_url(photo_upload) or normalize_public_asset_url(enriched.get("foto_url")) or upload_public_url(user_photo_upload)
    enriched["foto_nome_arquivo"] = (
        photo_upload.get("nome_original")
        if photo_upload
        else linked_user.get("foto_nome_arquivo") if linked_user and linked_user.get("foto_nome_arquivo") else None
    )
    enriched["tem_foto"] = bool(enriched.get("foto_url_publica"))
    return enriched


def enrich_user(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = public_user(item)
    photo_upload = repo.get("uploads", enriched.get("foto_upload_id")) if enriched.get("foto_upload_id") else None
    enriched["foto_url_publica"] = upload_public_url(photo_upload) or normalize_public_asset_url(enriched.get("foto_url"))
    enriched["foto_nome_arquivo"] = photo_upload.get("nome_original") if photo_upload else None
    enriched["tem_foto"] = bool(enriched.get("foto_url_publica"))
    return enriched


def enrich_demand(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    contact = repo.get("contatos", enriched.get("cidadao_id")) if enriched.get("cidadao_id") else None
    responsible = repo.get("usuarios", enriched.get("responsavel_usuario_id")) if enriched.get("responsavel_usuario_id") else None
    cv_upload = repo.get("uploads", enriched.get("cv_upload_id")) if enriched.get("cv_upload_id") else None
    linked_team = repo.get("equipes", enriched.get("equipe_id")) if enriched.get("equipe_id") else None
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    if not enriched["territorio_nome"] and contact:
        enriched["territorio_nome"] = territory_name(repo, contact.get("territorio_id")) or contact.get("bairro")
        enriched["territorio_id"] = enriched.get("territorio_id") or contact.get("territorio_id")
    enriched["cidadao_nome"] = contact.get("nome") if contact else contact_name(repo, enriched.get("cidadao_id"))
    enriched["cidadao_telefone"] = contact.get("telefone_principal") if contact else None
    enriched["categoria_nome"] = category_name(repo, enriched.get("categoria_id"))
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    enriched["equipe_nome"] = linked_team.get("nome") if linked_team else None
    enriched["gerada_por_nome"] = user_name(repo, enriched.get("gerada_por_usuario_id"))
    enriched["cidadao_foto_url"] = enrich_contact(repo, contact).get("foto_url_publica") if contact else None
    enriched["responsavel_foto_url"] = enrich_user(repo, responsible).get("foto_url_publica") if responsible else None
    if cv_upload:
        enriched["cv_nome_arquivo"] = cv_upload.get("nome_original")
        enriched["cv_url_publica"] = upload_public_url(cv_upload)
    elif enriched.get("cv_url"):
        enriched["cv_url_publica"] = normalize_public_asset_url(enriched.get("cv_url"))
    if enriched.get("status") in {"CONCLUIDA", "CANCELADA"}:
        enriched["criticidade_derivada"] = "BAIXA"
    elif enriched.get("prioridade") == "CRITICA":
        enriched["criticidade_derivada"] = "CRITICA"
    elif enriched.get("prioridade") == "ALTA":
        enriched["criticidade_derivada"] = "ALTA"
    else:
        enriched["criticidade_derivada"] = "NORMAL"
    sla_snapshot = demand_sla_snapshot(enriched, get_sla_settings(repo, enriched.get("gabinete_id")))
    enriched["sla_prazo_horas"] = sla_snapshot["prazo_horas"]
    enriched["sla_horas_decorridas"] = sla_snapshot["horas_decorridas"]
    enriched["sla_horas_restantes"] = sla_snapshot["horas_restantes"]
    enriched["sla_status"] = sla_snapshot["status"]
    enriched["sla_data_calculada"] = sla_snapshot["prazo_em"]
    return enriched


def enrich_interaction(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["cidadao_nome"] = contact_name(repo, enriched.get("cidadao_id"))
    enriched["demanda_titulo"] = None
    if enriched.get("demanda_id"):
        demand = repo.get("demandas", enriched.get("demanda_id"))
        enriched["demanda_titulo"] = demand.get("titulo") if demand else None
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    return enriched


def contact_completeness_score(item: dict[str, Any]) -> float:
    checkpoints = [
        bool(item.get("nome")),
        bool(item.get("telefone_principal")),
        bool(item.get("email")),
        bool(item.get("territorio_id") or item.get("bairro")),
        bool(item.get("logradouro")),
        bool(item.get("nivel_relacionamento")),
        bool(item.get("engajamento")),
        bool(item.get("voto_2028")),
    ]
    return sum(1 for checkpoint in checkpoints if checkpoint) / len(checkpoints)


def contact_engagement_score(item: dict[str, Any]) -> int:
    mapping = {
        "FRIO": 25,
        "MORNO": 45,
        "MEDIO": 70,
        "ALTO": 90,
        "FORTE": 100,
    }
    return mapping.get(str(item.get("engajamento") or "FRIO").upper(), 25)


def team_territory_ids(team: dict[str, Any], members: list[dict[str, Any]]) -> set[str]:
    ids = {
        scope.get("territorio_id")
        for scope in team.get("escopos", [])
        if scope.get("escopo_tipo") == "TERRITORIO" and scope.get("territorio_id")
    }
    for member in members:
        ids.update(
            scope.get("territorio_id")
            for scope in member.get("escopos", [])
            if scope.get("escopo_tipo") == "TERRITORIO" and scope.get("territorio_id")
        )
    return {item for item in ids if item}


def team_productivity_snapshot(repo: JsonStore, team: dict[str, Any]) -> dict[str, Any]:
    members = [item for item in repo.all("usuarios") if item.get("equipe_id") == team.get("id") and item.get("ativo", True)]
    member_ids = {item.get("id") for item in members if item.get("id")}
    territory_ids = team_territory_ids(team, members)
    contacts = [
        enrich_contact(repo, item)
        for item in repo.all("contatos")
        if item.get("status") != "EXCLUIDO"
        and (item.get("equipe_id") == team.get("id") or item.get("cadastrado_por_usuario_id") in member_ids)
    ]
    demands = [
        enrich_demand(repo, item)
        for item in repo.all("demandas")
        if item.get("status") != "EXCLUIDO"
        and (item.get("equipe_id") == team.get("id") or item.get("gerada_por_usuario_id") in member_ids)
    ]
    completeness = round((sum(contact_completeness_score(item) for item in contacts) / len(contacts)) * 100, 1) if contacts else 0.0
    engagement = round(sum(contact_engagement_score(item) for item in contacts) / len(contacts), 1) if contacts else 0.0
    strong_engagement = len([item for item in contacts if str(item.get("engajamento") or "").upper() in {"FORTE", "ALTO"}])
    qualified = len([item for item in contacts if contact_completeness_score(item) >= 0.75])
    open_demands = len([item for item in demands if item.get("status") in {"ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"}])
    return {
        "membros_ativos": len(members),
        "territorios_ids": sorted(territory_ids),
        "territorios_nomes": [territory_name(repo, territory_id) or territory_id for territory_id in sorted(territory_ids)],
        "cadastros": len(contacts),
        "demandas": len(demands),
        "demandas_abertas": open_demands,
        "cadastros_qualificados": qualified,
        "completude_media": completeness,
        "engajamento_medio": engagement,
        "engajamento_forte": strong_engagement,
    }


def enrich_team(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["supervisor_nome"] = user_name(repo, enriched.get("supervisor_usuario_id"))
    enriched["produtividade"] = team_productivity_snapshot(repo, enriched)
    return enriched


def enrich_agenda(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    return enriched


def enrich_proposition(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    return enriched


def normalize_amendment_status(value: str | None) -> str:
    mapping = {
        "INDICACAO": "PLEITEADA",
        "PLEITEADA": "PLEITEADA",
        "APROVADA": "APROVADA",
        "EMPENHO": "EMPENHADA",
        "EMPENHADA": "EMPENHADA",
        "LIQUIDACAO": "EMPENHADA",
        "PAGAMENTO": "EMPENHADA",
        "ENTREGUE": "EMPENHADA",
    }
    return mapping.get(str(value or "PLEITEADA").upper(), "PLEITEADA")


def enrich_amendment(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    indicated = float(enriched.get("valor_indicado") or 0)
    approved = float(enriched.get("valor_aprovado") or enriched.get("valor_empenhado") or 0)
    committed = float(enriched.get("valor_empenhado") or 0)
    status_name = normalize_amendment_status(enriched.get("status_execucao"))
    if not approved and status_name in {"APROVADA", "EMPENHADA"}:
        approved = indicated
    enriched["status_execucao"] = status_name
    enriched["valor_aprovado"] = approved
    enriched["data_empenho"] = enriched.get("data_empenho") or (enriched.get("data_ultima_movimentacao") if status_name == "EMPENHADA" else None)
    enriched["percentual_aprovado"] = round((approved / indicated) * 100, 1) if indicated else 0
    enriched["percentual_empenhado"] = round((committed / max(approved, 1)) * 100, 1) if approved else 0
    return enriched


def format_currency_brl(value: float | int | str | None) -> str:
    amount = float(value or 0)
    return f"R$ {amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def format_date_br(value: str | None) -> str:
    parsed = parse_iso_datetime(value)
    return parsed.astimezone(timezone.utc).strftime("%d/%m/%Y") if parsed else "sem data"


def days_since(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - parsed).days)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def sla_hours_by_priority(priority: str | None, config: dict[str, Any] | None = None) -> int:
    resolved = config or {
        "critica_horas": settings.sla_critical_hours,
        "alta_horas": settings.sla_high_hours,
        "media_horas": settings.sla_medium_hours,
        "baixa_horas": settings.sla_low_hours,
    }
    mapping = {
        "CRITICA": int(resolved.get("critica_horas", settings.sla_critical_hours)),
        "ALTA": int(resolved.get("alta_horas", settings.sla_high_hours)),
        "MEDIA": int(resolved.get("media_horas", settings.sla_medium_hours)),
        "BAIXA": int(resolved.get("baixa_horas", settings.sla_low_hours)),
    }
    return mapping.get((priority or "MEDIA").upper(), int(resolved.get("media_horas", settings.sla_medium_hours)))


def demand_opened_at(item: dict[str, Any]) -> datetime | None:
    return parse_iso_datetime(item.get("data_abertura") or item.get("created_at"))


def demand_sla_deadline(item: dict[str, Any], config: dict[str, Any] | None = None) -> datetime | None:
    explicit_deadline = parse_iso_datetime(item.get("sla_data"))
    if explicit_deadline:
        return explicit_deadline
    opened_at = demand_opened_at(item)
    if not opened_at:
        return None
    return opened_at + timedelta(hours=sla_hours_by_priority(item.get("prioridade"), config))


def demand_sla_snapshot(item: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    deadline = demand_sla_deadline(item, config)
    opened_at = demand_opened_at(item)
    closed_at = parse_iso_datetime(item.get("data_conclusao")) if item.get("status") == "CONCLUIDA" else None
    reference_time = closed_at or datetime.now(timezone.utc)
    elapsed_hours = None
    if opened_at:
        elapsed_hours = max(0, round((reference_time - opened_at).total_seconds() / 3600, 1))
    remaining_hours = None
    if deadline:
        remaining_hours = round((deadline - reference_time).total_seconds() / 3600, 1)

    if item.get("status") in {"CONCLUIDA", "CANCELADA", "ARQUIVADA"}:
        status_name = "CONCLUIDO_NO_PRAZO"
        if remaining_hours is not None and remaining_hours < 0:
            status_name = "CONCLUIDO_EM_ATRASO"
    elif remaining_hours is None:
        status_name = "SEM_PRAZO"
    elif remaining_hours < 0:
        status_name = "VENCIDO"
    elif elapsed_hours is not None and elapsed_hours >= sla_hours_by_priority(item.get("prioridade"), config) * float((config or {}).get("janela_risco_percentual", settings.sla_warning_ratio)):
        status_name = "EM_RISCO"
    else:
        status_name = "NO_PRAZO"

    return {
        "prazo_horas": sla_hours_by_priority(item.get("prioridade"), config),
        "prazo_em": deadline.isoformat() if deadline else None,
        "horas_decorridas": elapsed_hours,
        "horas_restantes": remaining_hours,
        "status": status_name,
    }


def get_sla_settings(repo: JsonStore, gabinete_id: str | None = None) -> dict[str, Any]:
    filters = {"chave": "sla_atendimento"}
    if gabinete_id:
        filters["gabinete_id"] = gabinete_id
    config = repo.find_one("configuracoes", **filters)
    values = (config or {}).get("valor") or {}
    return {
        "critica_horas": int(values.get("critica_horas", settings.sla_critical_hours)),
        "alta_horas": int(values.get("alta_horas", settings.sla_high_hours)),
        "media_horas": int(values.get("media_horas", settings.sla_medium_hours)),
        "baixa_horas": int(values.get("baixa_horas", settings.sla_low_hours)),
        "janela_risco_percentual": float(values.get("janela_risco_percentual", settings.sla_warning_ratio)),
    }


def ensure_sla_config(repo: JsonStore, gabinete_id: str) -> dict[str, Any]:
    existing = repo.find_one("configuracoes", chave="sla_atendimento", gabinete_id=gabinete_id)
    if existing:
        return existing
    return repo.create(
        "configuracoes",
        {
            "gabinete_id": gabinete_id,
            "chave": "sla_atendimento",
            "valor": get_sla_settings(repo, gabinete_id),
        },
    )


def record_sla_history(repo: JsonStore, gabinete_id: str, demanda: dict[str, Any], motivo: str) -> None:
    snapshot = demand_sla_snapshot(demanda, get_sla_settings(repo, gabinete_id))
    repo.create(
        "sla_historico",
        {
            "gabinete_id": gabinete_id,
            "demanda_id": demanda.get("id"),
            "motivo": motivo,
            "referencia_mes": datetime.now(timezone.utc).strftime("%Y-%m"),
            "prioridade": demanda.get("prioridade"),
            "status_demanda": demanda.get("status"),
            "status_sla": snapshot.get("status"),
            "horas_restantes": snapshot.get("horas_restantes"),
            "prazo_horas": snapshot.get("prazo_horas"),
            "territorio_id": demanda.get("territorio_id"),
            "territorio_nome": demanda.get("territorio_nome"),
        },
    )


def aggregate_sla_history(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_month: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = entry.get("referencia_mes") or "sem-mes"
        bucket = by_month.setdefault(
            key,
            {
                "mes": key,
                "total": 0,
                "no_prazo": 0,
                "em_risco": 0,
                "vencido": 0,
                "concluido_no_prazo": 0,
                "concluido_em_atraso": 0,
            },
        )
        bucket["total"] += 1
        status_name = entry.get("status_sla")
        if status_name == "NO_PRAZO":
            bucket["no_prazo"] += 1
        elif status_name == "EM_RISCO":
            bucket["em_risco"] += 1
        elif status_name == "VENCIDO":
            bucket["vencido"] += 1
        elif status_name == "CONCLUIDO_NO_PRAZO":
            bucket["concluido_no_prazo"] += 1
        elif status_name == "CONCLUIDO_EM_ATRASO":
            bucket["concluido_em_atraso"] += 1
    return [by_month[key] for key in sorted(by_month.keys(), reverse=True)][:6]


def ensure_sla_history(repo: JsonStore, gabinete_id: str) -> list[dict[str, Any]]:
    entries = [item for item in repo.all("sla_historico") if item.get("gabinete_id") == gabinete_id]
    if entries:
        return entries
    for demanda in [item for item in repo.all("demandas") if item.get("gabinete_id") == gabinete_id and item.get("status") != "EXCLUIDO"]:
        record_sla_history(repo, gabinete_id, enrich_demand(repo, demanda), "BACKFILL")
    return [item for item in repo.all("sla_historico") if item.get("gabinete_id") == gabinete_id]


def aggregate_sentiment(sentiments: list[dict[str, Any]]) -> dict[str, Any]:
    if not sentiments:
        return {
            "positivo": 0,
            "neutro": 0,
            "negativo": 0,
            "alerta": "Sem dados coletados.",
            "tema": "Sem tema monitorado",
            "canal": "Sem canal",
            "periodo": "Sem janela",
            "coletado_em": None,
            "amostras": 0,
            "canais": [],
            "periodos": [],
            "territorios": [],
        }

    total_positivo = sum(float(item.get("positivo") or 0) for item in sentiments)
    total_neutro = sum(float(item.get("neutro") or 0) for item in sentiments)
    total_negativo = sum(float(item.get("negativo") or 0) for item in sentiments)
    total = max(1.0, total_positivo + total_neutro + total_negativo)
    theme_counts: dict[str, int] = {}
    channel_counts: dict[str, int] = {}
    period_counts: dict[str, int] = {}
    territory_counts: dict[str, int] = {}
    latest = max(sentiments, key=lambda item: str(item.get("coletado_em") or item.get("updated_at") or ""))
    for item in sentiments:
        theme = item.get("tema") or "Sem tema"
        channel = item.get("canal") or "Sem canal"
        period = item.get("periodo") or "Sem janela"
        territory = item.get("territorio_nome") or item.get("territorio_id") or "Geral"
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
        channel_counts[channel] = channel_counts.get(channel, 0) + 1
        period_counts[period] = period_counts.get(period, 0) + 1
        territory_counts[territory] = territory_counts.get(territory, 0) + 1

    dominant_theme = max(theme_counts, key=theme_counts.get)
    dominant_channel = max(channel_counts, key=channel_counts.get)
    dominant_period = max(period_counts, key=period_counts.get)
    return {
        "positivo": round(total_positivo / total * 100),
        "neutro": round(total_neutro / total * 100),
        "negativo": round(total_negativo / total * 100),
        "alerta": latest.get("alerta") or "Sem alerta de sentimento.",
        "tema": dominant_theme,
        "canal": dominant_channel,
        "periodo": latest.get("periodo") or dominant_period,
        "coletado_em": latest.get("coletado_em") or latest.get("updated_at"),
        "amostras": len(sentiments),
        "canais": [{"canal": key, "quantidade": value} for key, value in sorted(channel_counts.items(), key=lambda row: row[1], reverse=True)],
        "periodos": [{"periodo": key, "quantidade": value} for key, value in sorted(period_counts.items(), key=lambda row: row[1], reverse=True)],
        "territorios": [{"territorio": key, "quantidade": value} for key, value in sorted(territory_counts.items(), key=lambda row: row[1], reverse=True)],
    }


def select_sentiments(
    sentiments: list[dict[str, Any]],
    canal: str | None = None,
    periodo: str | None = None,
    territorio: str | None = None,
) -> list[dict[str, Any]]:
    filtered = sentiments
    if canal:
        filtered = [item for item in filtered if (item.get("canal") or "Sem canal") == canal]
    if periodo:
        filtered = [item for item in filtered if (item.get("periodo") or "Sem janela") == periodo]
    if territorio:
        filtered = [
            item
            for item in filtered
            if territory_scope_matches(item.get("territorio_nome") or item.get("territorio_id") or "Geral", territorio)
        ]
    return filtered or sentiments


def pressure_level(score: int | float | None) -> str:
    resolved = float(score or 0)
    if resolved >= 9:
        return "ALTA"
    if resolved >= 4:
        return "MEDIA"
    return "BAIXA"


def enrich_office(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    enriched["demanda_titulo"] = None
    if enriched.get("demanda_id"):
        demand = repo.get("demandas", enriched.get("demanda_id"))
        enriched["demanda_titulo"] = demand.get("titulo") if demand else None
    base_date = enriched.get("data_envio") or enriched.get("created_at")
    enriched["dias_sem_resposta"] = days_since(base_date) if enriched.get("status") not in {"RESPONDIDO", "CONCLUIDO"} else 0
    return enriched


def create_history(
    repo: JsonStore,
    demanda_id: str,
    user_id: str | None,
    acao: str,
    status_anterior: str | None,
    status_novo: str | None,
    observacao: str | None = None,
    dados_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return repo.create(
        "historico_demanda",
        {
            "demanda_id": demanda_id,
            "usuario_id": user_id,
            "acao": acao,
            "status_anterior": status_anterior,
            "status_novo": status_novo,
            "observacao": observacao,
            "dados_json": dados_json or {},
            "created_at": iso_now(),
        },
    )


def validate_territory(repo: JsonStore, payload: dict[str, Any], current_id: str | None = None) -> None:
    tipo = payload.get("tipo")
    parent_id = payload.get("parent_id")
    if tipo == "REGIAO" and parent_id:
        business_rule("REGIAO nao pode ter parent_id.")
    if tipo in {"BAIRRO", "MICROAREA"} and not parent_id:
        business_rule(f"{tipo} deve ter parent_id.")
    if parent_id == current_id:
        business_rule("Territorio nao pode referenciar a si mesmo.")
    if parent_id:
        parent = repo.get("territorios", parent_id)
        if not parent:
            business_rule("parent_id invalido para territorio.")
        if tipo == "BAIRRO" and parent.get("tipo") != "REGIAO":
            business_rule("BAIRRO deve ser filho de REGIAO.")
        if tipo == "MICROAREA" and parent.get("tipo") != "BAIRRO":
            business_rule("MICROAREA deve ser filha de BAIRRO.")


def build_territory_tree(repo: JsonStore) -> list[dict[str, Any]]:
    territories = repo.all("territorios")
    by_parent: dict[str | None, list[dict[str, Any]]] = {}
    for territory in territories:
        by_parent.setdefault(territory.get("parent_id"), []).append(territory)

    def node(item: dict[str, Any]) -> dict[str, Any]:
        children = [node(child) for child in by_parent.get(item["id"], [])]
        return {
            "id": item["id"],
            "nome": item["nome"],
            "tipo": item["tipo"],
            "parent_id": item.get("parent_id"),
            "ativo": item.get("ativo", True),
            "children": children,
        }

    return [node(item) for item in by_parent.get(None, [])]


@router.post("/auth/login")
def auth_login(
    request: Request,
    payload: dict[str, Any] = Body(...),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("email_login", "senha"))
    user = repo.find_one("usuarios", email_login=payload["email_login"])
    if not user or not verify_password(payload["senha"], user.get("senha_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas.")
    if not user.get("ativo", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inativo.")
    user = repo.update("usuarios", user["id"], {"ultimo_login": iso_now()}) or user
    repo.audit(user["gabinete_id"], user["id"], "usuario", user["id"], "LOGIN")
    data = token_bundle(user)
    data["user"] = public_user(user)
    return success(request, data)


@router.post("/auth/refresh")
def auth_refresh(
    request: Request,
    payload: dict[str, Any] = Body(...),
    repo: JsonStore = Depends(get_store),
):
    from .auth import decode_token

    require_fields(payload, ("refresh_token",))
    decoded = decode_token(payload["refresh_token"], "refresh")
    user = repo.get("usuarios", decoded["sub"])
    if not user or not user.get("ativo", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inativo ou inexistente.")
    return success(request, token_bundle(user))


@router.post("/auth/logout", status_code=204)
def auth_logout(
    payload: dict[str, Any] = Body(default={}),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", current_user["id"], "LOGOUT", payload_novo=payload)
    return Response(status_code=204)


@router.get("/auth/me")
def auth_me(request: Request, current_user: dict[str, Any] = Depends(get_current_user)):
    return success(request, public_user(current_user))


@router.get("/usuarios")
def list_users(
    request: Request,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str | None = None,
    sort_order: str | None = None,
    perfil: str | None = None,
    equipe_id: str | None = None,
    ativo: bool | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    query = locals().copy()
    return list_response(
        request,
        "usuarios",
        repo,
        query,
        ("nome", "email_login", "perfil"),
        enrich=lambda item: enrich_user(repo, item),
    )


@router.post("/usuarios", status_code=201)
def create_user(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome", "email_login", "perfil"))
    if repo.find_one("usuarios", email_login=payload["email_login"]):
        conflict("email_login ja cadastrado.")
    password = payload.pop("senha", "Senha@123")
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "senha_hash": hash_password(password),
        "ativo": payload.get("ativo", True),
        "mfa_habilitado": payload.get("mfa_habilitado", False),
    }
    created = repo.create("usuarios", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", created["id"], "CREATE", payload_novo=enrich_user(repo, created))
    return success(request, enrich_user(repo, created))


@router.get("/usuarios/{usuario_id}")
def get_user_by_id(
    request: Request,
    usuario_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    user = repo.get("usuarios", usuario_id)
    if not user:
        not_found("Usuario")
    return success(request, enrich_user(repo, user))


@router.put("/usuarios/{usuario_id}")
def update_user(
    request: Request,
    usuario_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("usuarios", usuario_id)
    if not previous:
        not_found("Usuario")
    if "email_login" in payload and payload["email_login"] != previous.get("email_login"):
        if repo.find_one("usuarios", email_login=payload["email_login"]):
            conflict("email_login ja cadastrado.")
    payload.pop("senha_hash", None)
    if "senha" in payload:
        payload["senha_hash"] = hash_password(payload.pop("senha"))
    updated = repo.update("usuarios", usuario_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", usuario_id, "UPDATE", enrich_user(repo, previous), enrich_user(repo, updated))
    return success(request, enrich_user(repo, updated))


@router.patch("/usuarios/{usuario_id}/status")
def patch_user_status(
    request: Request,
    usuario_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("usuarios", usuario_id):
        not_found("Usuario")
    updated = repo.update("usuarios", usuario_id, {"ativo": bool(payload.get("ativo"))})
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", usuario_id, "STATUS", payload_novo={"ativo": updated["ativo"]})
    return success(request, {"id": usuario_id, "ativo": updated["ativo"]})


@router.post("/usuarios/{usuario_id}/reset-senha", status_code=202)
def request_user_password_reset(
    request: Request,
    usuario_id: str,
    payload: dict[str, Any] = Body(default={}),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("usuarios", usuario_id):
        not_found("Usuario")
    temporary_password = str(payload.get("nova_senha_temporaria") or "").strip()
    if len(temporary_password) < 8:
        business_rule("Informe nova_senha_temporaria com ao menos 8 caracteres.")
    repo.update("usuarios", usuario_id, {"senha_hash": hash_password(temporary_password)})
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", usuario_id, "RESET_SENHA", payload_novo=payload)
    return success(request, {"status": "RESET_CONCLUIDO"})


@router.get("/equipes")
def list_teams(
    request: Request,
    search: str | None = None,
    ativo: bool | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return success(
        request,
        [enrich_team(repo, item) for item in list_response(request, "equipes", repo, locals().copy(), ("nome", "descricao"))["data"]],
    )


@router.post("/equipes", status_code=201)
def create_team(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome",))
    if payload.get("supervisor_usuario_id") and not repo.get("usuarios", payload["supervisor_usuario_id"]):
        business_rule("supervisor_usuario_id invalido para equipe.")
    item = {**payload, "gabinete_id": current_user["gabinete_id"], "ativo": payload.get("ativo", True)}
    created = repo.create("equipes", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "equipe", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_team(repo, created))


@router.get("/equipes/{equipe_id}")
def get_team_by_id(
    request: Request,
    equipe_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    team = repo.get("equipes", equipe_id)
    if not team:
        not_found("Equipe")
    return success(request, enrich_team(repo, team))


@router.put("/equipes/{equipe_id}")
def update_team(
    request: Request,
    equipe_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("equipes", equipe_id)
    if not previous:
        not_found("Equipe")
    if payload.get("supervisor_usuario_id") and not repo.get("usuarios", payload["supervisor_usuario_id"]):
        business_rule("supervisor_usuario_id invalido para equipe.")
    updated = repo.update("equipes", equipe_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "equipe", equipe_id, "UPDATE", previous, updated)
    return success(request, enrich_team(repo, updated))


@router.get("/auditoria")
def list_audit_events(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    usuario_id: str | None = None,
    entidade: str | None = None,
    acao: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "auditoria", repo, locals().copy(), ("entidade", "acao"))


@router.get("/territorios/tree")
def get_territory_tree(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return success(request, build_territory_tree(repo))


@router.get("/territorios")
def list_territories(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    tipo: str | None = None,
    parent_id: str | None = None,
    ativo: bool | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "territorios", repo, locals().copy(), ("nome", "tipo", "codigo_externo"))


@router.post("/territorios", status_code=201)
def create_territory(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome", "tipo"))
    validate_territory(repo, payload)
    item = {**payload, "gabinete_id": current_user["gabinete_id"], "ativo": payload.get("ativo", True)}
    created = repo.create("territorios", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "territorio", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/territorios/{territorio_id}")
def get_territory_by_id(
    request: Request,
    territorio_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    territory = repo.get("territorios", territorio_id)
    if not territory:
        not_found("Territorio")
    return success(request, territory)


@router.put("/territorios/{territorio_id}")
def update_territory(
    request: Request,
    territorio_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("territorios", territorio_id)
    if not previous:
        not_found("Territorio")
    merged = {**previous, **payload}
    validate_territory(repo, merged, territorio_id)
    updated = repo.update("territorios", territorio_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "territorio", territorio_id, "UPDATE", previous, updated)
    return success(request, updated)


@router.patch("/territorios/{territorio_id}/status")
def patch_territory_status(
    request: Request,
    territorio_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("territorios", territorio_id):
        not_found("Territorio")
    updated = repo.update("territorios", territorio_id, {"ativo": bool(payload.get("ativo"))})
    repo.audit(current_user["gabinete_id"], current_user["id"], "territorio", territorio_id, "STATUS", payload_novo={"ativo": updated["ativo"]})
    return success(request, updated)


@router.get("/contatos")
def list_contacts(
    request: Request,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str | None = None,
    sort_order: str | None = None,
    territorio_id: str | None = None,
    status: str | None = None,
    tipo_contato: str | None = None,
    duplicidade_suspeita: bool | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    response = list_response(
        request,
        "contatos",
        repo,
        locals().copy(),
        ("nome", "cpf", "telefone_principal", "email", "bairro"),
        enrich=lambda item: enrich_contact(repo, item),
    )
    if not status:
        response["data"] = [item for item in response["data"] if item.get("status") != "EXCLUIDO"]
        response["meta"]["total"] = len(response["data"])
    return response


@router.post("/contatos", status_code=201)
def create_contact(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome",))
    if payload.get("cpf") and repo.find_one("contatos", cpf=payload["cpf"]):
        conflict("CPF ja cadastrado.")
    if payload.get("territorio_id") and not repo.get("territorios", payload["territorio_id"]):
        business_rule("territorio_id invalido para contato.")
    if payload.get("equipe_id") and not repo.get("equipes", payload["equipe_id"]):
        business_rule("equipe_id invalido para contato.")
    phone = payload.get("telefone_principal")
    name = payload.get("nome", "").strip().lower()
    duplicate = any(
        item.get("nome", "").strip().lower() == name and phone and item.get("telefone_principal") == phone
        for item in repo.all("contatos")
    )
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "origem_cadastro": payload.get("origem_cadastro", "WEB_INTERNO"),
        "equipe_id": payload.get("equipe_id") or current_user.get("equipe_id"),
        "cadastrado_por_usuario_id": payload.get("cadastrado_por_usuario_id") or current_user["id"],
        "tipo_contato": payload.get("tipo_contato", "CIDADAO"),
        "status": "DUPLICIDADE_SUSPEITA" if duplicate else payload.get("status", "ATIVO"),
        "duplicidade_suspeita": duplicate,
        "nivel_relacionamento": payload.get("nivel_relacionamento", "CONTATO"),
        "influencia": payload.get("influencia", "BAIXA"),
        "engajamento": payload.get("engajamento", "FRIO"),
        "voto_2028": payload.get("voto_2028", "INDEFINIDO"),
        "prioridade_politica": payload.get("prioridade_politica", "MEDIA"),
        "origem_politica": payload.get("origem_politica", "DECLARADO"),
    }
    created = repo.create("contatos", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "contato", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_contact(repo, created))


@router.get("/contatos/{contato_id}")
def get_contact_by_id(
    request: Request,
    contato_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    contact = repo.get("contatos", contato_id)
    if not contact:
        not_found("Contato")
    demand_count = len([item for item in repo.all("demandas") if item.get("cidadao_id") == contato_id])
    agenda_count = len(
        [
            item
            for item in repo.all("agenda_eventos")
            if any(p.get("cidadao_id") == contato_id for p in item.get("participantes", []))
        ]
    )
    document_count = len([item for item in repo.all("documentos") if item.get("demanda_id")])
    detail = enrich_contact(repo, contact)
    detail["consentimentos"] = [item for item in repo.all("consentimentos") if item.get("cidadao_id") == contato_id]
    detail["tags"] = detail.get("tags", [])
    detail["resumo"] = {
        "total_demandas": demand_count,
        "total_agendas": agenda_count,
        "total_documentos": document_count,
    }
    return success(request, detail)


@router.put("/contatos/{contato_id}")
def update_contact(
    request: Request,
    contato_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("contatos", contato_id)
    if not previous:
        not_found("Contato")
    if payload.get("cpf") and payload.get("cpf") != previous.get("cpf"):
        if repo.find_one("contatos", cpf=payload["cpf"]):
            conflict("CPF ja cadastrado.")
    if payload.get("territorio_id") and not repo.get("territorios", payload["territorio_id"]):
        business_rule("territorio_id invalido para contato.")
    if payload.get("equipe_id") and not repo.get("equipes", payload["equipe_id"]):
        business_rule("equipe_id invalido para contato.")
    updated = repo.update("contatos", contato_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "contato", contato_id, "UPDATE", previous, updated)
    return success(request, enrich_contact(repo, updated))


@router.patch("/contatos/{contato_id}/status")
def patch_contact_status(
    request: Request,
    contato_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("contatos", contato_id):
        not_found("Contato")
    require_fields(payload, ("status",))
    updated = repo.update("contatos", contato_id, {"status": payload["status"]})
    repo.audit(current_user["gabinete_id"], current_user["id"], "contato", contato_id, "STATUS", payload_novo=payload)
    return success(request, enrich_contact(repo, updated))


@router.delete("/contatos/{contato_id}")
def delete_contact(
    request: Request,
    contato_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("contatos", contato_id)
    if not previous:
        not_found("Contato")
    updated = repo.update("contatos", contato_id, {"status": "EXCLUIDO", "deleted_at": iso_now(), "deleted_by": current_user["id"]})
    repo.audit(current_user["gabinete_id"], current_user["id"], "contato", contato_id, "DELETE", previous, updated)
    return success(request, enrich_contact(repo, updated))


@router.get("/contatos/{contato_id}/consentimentos")
def list_contact_consents(
    request: Request,
    contato_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("contatos", contato_id):
        not_found("Contato")
    items = [item for item in repo.all("consentimentos") if item.get("cidadao_id") == contato_id]
    return success(request, items)


@router.post("/contatos/{contato_id}/consentimentos", status_code=201)
def create_contact_consent(
    request: Request,
    contato_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("contatos", contato_id):
        not_found("Contato")
    require_fields(payload, ("canal", "consentido", "finalidade"))
    item = {
        **payload,
        "cidadao_id": contato_id,
        "registrado_em": iso_now(),
        "registrado_por": current_user["id"],
    }
    created = repo.create("consentimentos", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "consentimento", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/demandas")
def list_demands(
    request: Request,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    prioridade: str | None = None,
    categoria_id: str | None = None,
    territorio_id: str | None = None,
    responsavel_usuario_id: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    response = list_response(
        request,
        "demandas",
        repo,
        locals().copy(),
        ("titulo", "descricao", "status", "prioridade"),
        enrich=lambda item: enrich_demand(repo, item),
    )
    if not status:
        response["data"] = [item for item in response["data"] if item.get("status") != "EXCLUIDO"]
        response["meta"]["total"] = len(response["data"])
    return response


@router.post("/demandas", status_code=201)
def create_demand(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("cidadao_id", "titulo", "descricao"))
    contact = repo.get("contatos", payload["cidadao_id"])
    if not contact:
        business_rule("Toda demanda deve estar vinculada a um demandante cadastrado.")
    if payload.get("territorio_id") and not repo.get("territorios", payload["territorio_id"]):
        business_rule("territorio_id invalido para demanda.")
    if payload.get("equipe_id") and not repo.get("equipes", payload["equipe_id"]):
        business_rule("equipe_id invalido para demanda.")
    if payload.get("responsavel_usuario_id") and not repo.get("usuarios", payload["responsavel_usuario_id"]):
        business_rule("responsavel_usuario_id invalido para demanda.")
    opened_at = iso_now()
    opened_at_dt = parse_iso_datetime(opened_at) or datetime.now(timezone.utc)
    sla_config = get_sla_settings(repo, current_user["gabinete_id"])
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "territorio_id": payload.get("territorio_id") or contact.get("territorio_id"),
        "status": payload.get("status", "ABERTA"),
        "prioridade": payload.get("prioridade", "MEDIA"),
        "origem_cadastro": payload.get("origem_cadastro", "WEB_INTERNO"),
        "equipe_id": payload.get("equipe_id") or current_user.get("equipe_id") or contact.get("equipe_id"),
        "gerada_por_usuario_id": payload.get("gerada_por_usuario_id") or current_user["id"],
        "responsavel_usuario_id": payload.get("responsavel_usuario_id") or current_user["id"],
        "sla_data": payload.get("sla_data") or (opened_at_dt + timedelta(hours=sla_hours_by_priority(payload.get("prioridade", "MEDIA"), sla_config))).isoformat(),
        "data_abertura": opened_at,
        "data_conclusao": None,
        "tags": payload.get("tags", []),
        "anexos": payload.get("anexos", []),
        "beneficiario_nome": payload.get("beneficiario_nome"),
        "tipo_vaga_pretendida": payload.get("tipo_vaga_pretendida"),
        "vaga_outros_descricao": payload.get("vaga_outros_descricao"),
        "cv_upload_id": payload.get("cv_upload_id"),
        "cv_url": payload.get("cv_url"),
    }
    created = repo.create("demandas", item)
    record_sla_history(repo, current_user["gabinete_id"], enrich_demand(repo, created), "CREATE")
    create_history(repo, created["id"], current_user["id"], "CREATE", None, created["status"], "Demanda criada.")
    repo.audit(current_user["gabinete_id"], current_user["id"], "demanda", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_demand(repo, created))


@router.get("/demandas/{demanda_id}")
def get_demand_by_id(
    request: Request,
    demanda_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    demand = repo.get("demandas", demanda_id)
    if not demand:
        not_found("Demanda")
    return success(request, enrich_demand(repo, demand))


@router.put("/demandas/{demanda_id}")
def update_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    patch = dict(payload)
    if patch.get("territorio_id") and not repo.get("territorios", patch["territorio_id"]):
        business_rule("territorio_id invalido para demanda.")
    if patch.get("equipe_id") and not repo.get("equipes", patch["equipe_id"]):
        business_rule("equipe_id invalido para demanda.")
    if patch.get("responsavel_usuario_id") and not repo.get("usuarios", patch["responsavel_usuario_id"]):
        business_rule("responsavel_usuario_id invalido para demanda.")
    if patch.get("status") == "CONCLUIDA" and not patch.get("data_conclusao"):
        patch["data_conclusao"] = iso_now()
    if patch.get("status") == "ARQUIVADA" and not patch.get("data_arquivamento"):
        patch["data_arquivamento"] = iso_now()
    updated = repo.update("demandas", demanda_id, patch)
    if updated:
        record_sla_history(repo, current_user["gabinete_id"], enrich_demand(repo, updated), "UPDATE")
    if previous.get("status") != updated.get("status"):
        create_history(repo, demanda_id, current_user["id"], "STATUS_CHANGE", previous.get("status"), updated.get("status"), payload.get("observacao"))
    repo.audit(current_user["gabinete_id"], current_user["id"], "demanda", demanda_id, "UPDATE", previous, updated)
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/assumir")
def assume_demand(
    request: Request,
    demanda_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    if not previous.get("cidadao_id"):
        business_rule("Regularize o demandante antes de iniciar atendimento.")
    updated = repo.update("demandas", demanda_id, {"responsavel_usuario_id": current_user["id"], "status": "EM_ATENDIMENTO"})
    if updated:
        record_sla_history(repo, current_user["gabinete_id"], enrich_demand(repo, updated), "START_SERVICE")
    create_history(repo, demanda_id, current_user["id"], "START_SERVICE", previous.get("status"), "EM_ATENDIMENTO", "Atendimento iniciado pelo responsavel.")
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/arquivar")
def archive_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(default={}),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update(
        "demandas",
        demanda_id,
        {"status": "ARQUIVADA", "motivo_arquivamento": payload.get("motivo") or "Arquivada pela equipe.", "data_arquivamento": iso_now()},
    )
    if updated:
        record_sla_history(repo, current_user["gabinete_id"], enrich_demand(repo, updated), "ARCHIVE")
    create_history(repo, demanda_id, current_user["id"], "ARCHIVE", previous.get("status"), "ARQUIVADA", payload.get("motivo"))
    repo.audit(current_user["gabinete_id"], current_user["id"], "demanda", demanda_id, "ARCHIVE", previous, updated)
    return success(request, enrich_demand(repo, updated))


@router.delete("/demandas/{demanda_id}")
def delete_demand(
    request: Request,
    demanda_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update("demandas", demanda_id, {"status": "EXCLUIDO", "deleted_at": iso_now(), "deleted_by": current_user["id"]})
    create_history(repo, demanda_id, current_user["id"], "DELETE", previous.get("status"), "EXCLUIDO", "Exclusao logica.")
    repo.audit(current_user["gabinete_id"], current_user["id"], "demanda", demanda_id, "DELETE", previous, updated)
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/atribuir")
def assign_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("responsavel_usuario_id",))
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update("demandas", demanda_id, {"responsavel_usuario_id": payload["responsavel_usuario_id"], "status": "EM_ATENDIMENTO"})
    create_history(repo, demanda_id, current_user["id"], "ASSIGN", previous.get("status"), "EM_ATENDIMENTO", payload.get("observacao"))
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/repriorizar")
def reprioritize_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("prioridade", "motivo"))
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update("demandas", demanda_id, {"prioridade": payload["prioridade"]})
    create_history(repo, demanda_id, current_user["id"], "REPRIORITIZE", previous.get("status"), previous.get("status"), payload.get("motivo"))
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/encaminhar", status_code=201)
def forward_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("tipo", "descricao"))
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    item = {**payload, "demanda_id": demanda_id, "status": "ABERTO", "created_by": current_user["id"]}
    created = repo.create("encaminhamentos", item)
    repo.update("demandas", demanda_id, {"status": "ENCAMINHADA"})
    create_history(repo, demanda_id, current_user["id"], "FORWARD", previous.get("status"), "ENCAMINHADA", payload.get("descricao"))
    return success(request, created)


@router.post("/demandas/{demanda_id}/concluir")
def conclude_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("observacao",))
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update("demandas", demanda_id, {"status": "CONCLUIDA", "data_conclusao": iso_now()})
    create_history(repo, demanda_id, current_user["id"], "CONCLUDE", previous.get("status"), "CONCLUIDA", payload.get("observacao"))
    return success(request, enrich_demand(repo, updated))


@router.post("/demandas/{demanda_id}/reabrir")
def reopen_demand(
    request: Request,
    demanda_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("motivo_reabertura",))
    previous = repo.get("demandas", demanda_id)
    if not previous:
        not_found("Demanda")
    updated = repo.update("demandas", demanda_id, {"status": "REABERTA", "motivo_reabertura": payload["motivo_reabertura"], "data_conclusao": None})
    create_history(repo, demanda_id, current_user["id"], "REOPEN", previous.get("status"), "REABERTA", payload.get("motivo_reabertura"))
    return success(request, enrich_demand(repo, updated))


@router.get("/demandas/{demanda_id}/historico")
def list_demand_history(
    request: Request,
    demanda_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("demandas", demanda_id):
        not_found("Demanda")
    items = [item for item in repo.all("historico_demanda") if item.get("demanda_id") == demanda_id]
    for item in items:
        item["usuario"] = {"id": item.get("usuario_id"), "nome": user_name(repo, item.get("usuario_id"))}
    return success(request, items)


@router.get("/agenda")
def list_agenda(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    tipo_agenda_id: str | None = None,
    tipo_agenda: str | None = None,
    status: str | None = None,
    territorio_id: str | None = None,
    responsavel_usuario_id: str | None = None,
    eh_agenda_vereador: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(
        request,
        "agenda_eventos",
        repo,
        locals().copy(),
        ("titulo", "descricao", "local_texto", "tipo_agenda"),
        enrich=lambda item: enrich_agenda(repo, item),
    )


@router.post("/agenda-eventos", status_code=201)
def create_agenda_event(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "status", "data_inicio", "data_fim"))
    if payload["data_fim"] < payload["data_inicio"]:
        business_rule("data_fim deve ser maior ou igual a data_inicio.")
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "participantes": payload.get("participantes", []),
        "eh_agenda_vereador": payload.get("eh_agenda_vereador", False),
        "tipo_agenda": payload.get("tipo_agenda", "REUNIAO_BASE"),
        "publico_estimado": payload.get("publico_estimado"),
        "relatorio_execucao": payload.get("relatorio_execucao"),
        "anexos": payload.get("anexos", []),
    }
    created = repo.create("agenda_eventos", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "agenda_evento", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/agenda-eventos/{evento_id}")
def get_agenda_event(
    request: Request,
    evento_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    item = repo.get("agenda_eventos", evento_id)
    if not item:
        not_found("Evento")
    return success(request, item)


@router.put("/agenda-eventos/{evento_id}")
def update_agenda_event(
    request: Request,
    evento_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("agenda_eventos", evento_id)
    if not previous:
        not_found("Evento")
    merged = {**previous, **payload}
    if merged.get("data_fim") and merged.get("data_inicio") and merged["data_fim"] < merged["data_inicio"]:
        business_rule("data_fim deve ser maior ou igual a data_inicio.")
    updated = repo.update("agenda_eventos", evento_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "agenda_evento", evento_id, "UPDATE", previous, updated)
    return success(request, updated)


@router.patch("/agenda-eventos/{evento_id}/status")
def patch_agenda_status(
    request: Request,
    evento_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("agenda_eventos", evento_id):
        not_found("Evento")
    require_fields(payload, ("status",))
    updated = repo.update("agenda_eventos", evento_id, {"status": payload["status"]})
    return success(request, updated)


@router.post("/agenda-eventos/{evento_id}/notificar", status_code=202)
def notify_agenda_event(
    request: Request,
    evento_id: str,
    payload: dict[str, Any] = Body(default={}),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    if not repo.get("agenda_eventos", evento_id):
        not_found("Evento")
    for user_id in payload.get("usuarios_ids", []):
        repo.create(
            "notificacoes",
            {
                "gabinete_id": current_user["gabinete_id"],
                "usuario_id": user_id,
                "tipo": "AGENDA",
                "titulo": "Notificacao de agenda",
                "mensagem": f"Evento {evento_id} possui atualizacao.",
                "lida": False,
                "referencia_tipo": "agenda_evento",
                "referencia_id": evento_id,
            },
        )
    return success(request, {"status": "NOTIFICACAO_ENFILEIRADA"})


@router.get("/interacoes")
def list_interactions(
    request: Request,
    search: str | None = None,
    cidadao_id: str | None = None,
    demanda_id: str | None = None,
    tipo_interacao: str | None = None,
    canal_contato: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(
        request,
        "interacoes",
        repo,
        locals().copy(),
        ("assunto", "descricao_detalhada", "tipo_interacao", "canal_contato"),
        enrich=lambda item: enrich_interaction(repo, item),
    )


@router.post("/interacoes", status_code=201)
def create_interaction(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("cidadao_id", "tipo_interacao", "assunto"))
    if not repo.get("contatos", payload["cidadao_id"]):
        business_rule("Interacao deve estar vinculada a um contato cadastrado.")
    if payload.get("demanda_id") and not repo.get("demandas", payload["demanda_id"]):
        business_rule("demanda_id invalido para interacao.")
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "status": payload.get("status", "REGISTRADA"),
        "prioridade": payload.get("prioridade", "MEDIA"),
        "responsavel_usuario_id": payload.get("responsavel_usuario_id") or current_user["id"],
        "data_contato": payload.get("data_contato") or iso_now(),
    }
    created = repo.create("interacoes", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "interacao", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_interaction(repo, created))


@router.get("/proposicoes")
def list_propositions(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    etapa_kanban: str | None = None,
    tema: str | None = None,
    tipo: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(
        request,
        "proposicoes",
        repo,
        locals().copy(),
        ("titulo", "numero", "tema", "status", "etapa_kanban"),
        enrich=lambda item: enrich_proposition(repo, item),
    )


@router.post("/proposicoes", status_code=201)
def create_proposition(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "tipo", "status"))
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "etapa_kanban": payload.get("etapa_kanban") or payload.get("status"),
        "responsavel_usuario_id": payload.get("responsavel_usuario_id") or current_user["id"],
        "discursos": payload.get("discursos", []),
        "tags": payload.get("tags", []),
    }
    created = repo.create("proposicoes", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "proposicao", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_proposition(repo, created))


@router.get("/emendas")
def list_amendments(
    request: Request,
    search: str | None = None,
    status_execucao: str | None = None,
    tipo_emenda: str | None = None,
    area: str | None = None,
    territorio_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(
        request,
        "emendas",
        repo,
        locals().copy(),
        ("titulo", "numero", "beneficiario", "objeto", "area"),
        enrich=lambda item: enrich_amendment(repo, item),
    )


@router.post("/emendas", status_code=201)
def create_amendment(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "numero", "valor_indicado"))
    status_name = normalize_amendment_status(payload.get("status_execucao"))
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "valor_aprovado": float(payload.get("valor_aprovado") or 0),
        "valor_empenhado": float(payload.get("valor_empenhado") or 0),
        "status_execucao": status_name,
        "data_empenho": payload.get("data_empenho"),
        "documentos": payload.get("documentos", []),
        "fotos": payload.get("fotos", []),
    }
    item["valor_indicado"] = float(item["valor_indicado"])
    created = repo.create("emendas", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "emenda", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_amendment(repo, created))


@router.get("/oficios")
def list_offices(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    demanda_id: str | None = None,
    orgao_destino: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(
        request,
        "oficios",
        repo,
        locals().copy(),
        ("numero", "titulo", "assunto", "orgao_destino", "status"),
        enrich=lambda item: enrich_office(repo, item),
    )


@router.post("/oficios", status_code=201)
def create_office(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "orgao_destino", "assunto"))
    if payload.get("demanda_id") and not repo.get("demandas", payload["demanda_id"]):
        business_rule("demanda_id invalido para oficio.")
    year = datetime.now().year
    count = len(repo.all("oficios")) + 1
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "numero": payload.get("numero") or f"OF-{year}-{count:03d}",
        "status": payload.get("status", "RASCUNHO"),
        "responsavel_usuario_id": payload.get("responsavel_usuario_id") or current_user["id"],
        "data_envio": payload.get("data_envio"),
        "resposta": payload.get("resposta"),
    }
    created = repo.create("oficios", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "oficio", created["id"], "CREATE", payload_novo=created)
    return success(request, enrich_office(repo, created))


@router.get("/configuracoes/sla")
def get_sla_configuration(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    item = ensure_sla_config(repo, current_user["gabinete_id"])
    return success(request, item.get("valor") or get_sla_settings(repo, current_user["gabinete_id"]))


@router.put("/configuracoes/sla")
def update_sla_configuration(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    existing = ensure_sla_config(repo, current_user["gabinete_id"])
    merged = {
        **(existing.get("valor") or get_sla_settings(repo, current_user["gabinete_id"])),
        **payload,
    }
    for key in ("critica_horas", "alta_horas", "media_horas", "baixa_horas"):
        merged[key] = int(merged.get(key) or 0)
        if merged[key] <= 0:
            business_rule(f"{key} deve ser maior que zero.")
    merged["janela_risco_percentual"] = float(merged.get("janela_risco_percentual") or settings.sla_warning_ratio)
    if not 0 < merged["janela_risco_percentual"] < 1:
        business_rule("janela_risco_percentual deve ficar entre 0 e 1.")
    updated = repo.update("configuracoes", existing["id"], {"valor": merged})
    settings.sla_critical_hours = merged["critica_horas"]
    settings.sla_high_hours = merged["alta_horas"]
    settings.sla_medium_hours = merged["media_horas"]
    settings.sla_low_hours = merged["baixa_horas"]
    settings.sla_warning_ratio = merged["janela_risco_percentual"]
    repo.audit(current_user["gabinete_id"], current_user["id"], "configuracao_sla", existing["id"], "UPDATE", existing, updated)
    return success(request, merged)


@router.get("/sla/historico")
def get_sla_history(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    entries = ensure_sla_history(repo, current_user["gabinete_id"])
    return success(request, {"ultimos_registros": entries[-20:], "resumo_mensal": aggregate_sla_history(entries)})


@router.get("/sentimento-social/resumo")
def get_sentiment_summary(
    request: Request,
    canal: str | None = None,
    periodo: str | None = None,
    territorio: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    sentiments = [
        item
        for item in repo.all("sentimento_social")
        if item.get("gabinete_id") == current_user["gabinete_id"]
    ]
    selected = select_sentiments(sentiments, canal, periodo, territorio)
    summary = aggregate_sentiment(selected)
    summary["filtros_aplicados"] = {
        "canal": canal,
        "periodo": periodo,
        "territorio": territorio,
    }
    return success(request, summary)


@router.get("/political-os/overview")
def political_os_overview(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    contacts = [item for item in repo.all("contatos") if active_contact(item)]
    demands = [enrich_demand(repo, item) for item in repo.all("demandas") if item.get("status") != "EXCLUIDO"]
    agenda = [enrich_agenda(repo, item) for item in repo.all("agenda_eventos")]
    propositions = repo.all("proposicoes")
    amendments = [enrich_amendment(repo, item) for item in repo.all("emendas")]
    offices = [enrich_office(repo, item) for item in repo.all("oficios")]
    sentiments = repo.all("sentimento_social")
    convenios = repo.all("editais_convenios")
    sla_config = get_sla_settings(repo, current_user["gabinete_id"])

    open_status = {"ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"}
    open_demands = [item for item in demands if item.get("status") in open_status]
    open_demand_sla = [(item, demand_sla_snapshot(item, sla_config)) for item in open_demands]
    sla_overdue = [item for item, snapshot in open_demand_sla if snapshot.get("status") == "VENCIDO"]
    sla_risk = [item for item, snapshot in open_demand_sla if snapshot.get("status") == "EM_RISCO"]
    completed_demands = [item for item in demands if item.get("status") in {"CONCLUIDA", "CANCELADA", "ARQUIVADA"}]
    completed_sla = [(item, demand_sla_snapshot(item, sla_config)) for item in completed_demands]
    completed_on_time = [item for item, snapshot in completed_sla if snapshot.get("status") == "CONCLUIDO_NO_PRAZO"]
    completed_late = [item for item, snapshot in completed_sla if snapshot.get("status") == "CONCLUIDO_EM_ATRASO"]
    leaders = [item for item in contacts if is_leadership_contact(item)]
    strong_engagement = [item for item in contacts if is_strong_engagement_contact(item)]

    territories = repo.all("territorios")
    formal_territories_by_key = {
        normalized_territory_key(item.get("nome")): item
        for item in territories
        if item.get("tipo") == "REGIAO"
    }
    heatmap_by_key: dict[str, dict[str, Any]] = {}
    for territory in territories:
        territory_demands = [item for item in demands if item.get("territorio_id") == territory["id"]]
        territory_contacts = [item for item in contacts if item.get("territorio_id") == territory["id"]]
        if not territory_demands and not territory_contacts:
            continue
        score = len(territory_demands) * 3 + len([item for item in territory_contacts if is_leadership_contact(item)]) * 2 + len(territory_contacts)
        scope_name, scope_id, scope_type, scope_key = resolve_heatmap_scope(territory.get("nome"), formal_territories_by_key)
        bucket = ensure_heatmap_bucket(
            heatmap_by_key,
            scope_key,
            scope_name,
            scope_id or territory.get("id"),
            scope_type or territory.get("tipo"),
        )
        bucket["demandas"] += len(territory_demands)
        bucket["contatos"] += len(territory_contacts)
        bucket["liderancas"] += len([item for item in territory_contacts if is_leadership_contact(item)])
        bucket["score"] += score

    for contact in contacts:
        if contact.get("territorio_id"):
            continue
        bairro = contact.get("bairro") or "Sem bairro"
        scope_name, scope_id, scope_type, scope_key = resolve_heatmap_scope(bairro, formal_territories_by_key)
        bucket = ensure_heatmap_bucket(heatmap_by_key, scope_key, scope_name, scope_id, scope_type or "BAIRRO")
        bucket["contatos"] += 1
        bucket["liderancas"] += 1 if is_leadership_contact(contact) else 0
        bucket["score"] += 2 if is_leadership_contact(contact) else 1
    for demand in demands:
        if demand.get("territorio_id"):
            continue
        contact = repo.get("contatos", demand.get("cidadao_id")) if demand.get("cidadao_id") else None
        bairro = demand.get("bairro") or (contact or {}).get("bairro") or "Sem territorio"
        scope_name, scope_id, scope_type, scope_key = resolve_heatmap_scope(bairro, formal_territories_by_key)
        bucket = ensure_heatmap_bucket(heatmap_by_key, scope_key, scope_name, scope_id, scope_type or "BAIRRO")
        bucket["demandas"] += 1
        bucket["score"] += 3

    heatmap = list(heatmap_by_key.values())
    for item in heatmap:
        item["nivel_pressao"] = pressure_level(item.get("score"))
    if not heatmap:
        for contact in contacts:
            bairro = contact.get("bairro") or "Sem bairro"
            scope_name, scope_id, scope_type, scope_key = resolve_heatmap_scope(bairro, formal_territories_by_key)
            bucket = ensure_heatmap_bucket(heatmap_by_key, scope_key, scope_name, scope_id, scope_type or "BAIRRO")
            bucket["contatos"] += 1
            bucket["liderancas"] += 1 if is_leadership_contact(contact) else 0
            bucket["score"] += 2 if is_leadership_contact(contact) else 1
        heatmap = list(heatmap_by_key.values())
    heatmap.sort(key=lambda item: item.get("score", 0), reverse=True)

    amendment_totals = {
        "valor_indicado": sum(float(item.get("valor_indicado") or 0) for item in amendments),
        "valor_aprovado": sum(float(item.get("valor_aprovado") or 0) for item in amendments),
        "valor_empenhado": sum(float(item.get("valor_empenhado") or 0) for item in amendments),
        "aprovadas": len([item for item in amendments if item.get("status_execucao") in {"APROVADA", "EMPENHADA"}]),
        "empenhadas": len([item for item in amendments if item.get("status_execucao") == "EMPENHADA"]),
        "ultima_data_empenho": max((item.get("data_empenho") for item in amendments if item.get("data_empenho")), default=None),
    }

    kanban: dict[str, int] = {}
    for proposition in propositions:
        etapa = proposition.get("etapa_kanban") or proposition.get("status") or "SEM_ETAPA"
        kanban[etapa] = kanban.get(etapa, 0) + 1

    pending_offices = [
        item
        for item in offices
        if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"} and (item.get("dias_sem_resposta") or 0) >= 15
    ]
    alerts = []
    for office in pending_offices[:4]:
        linked_demand = repo.get("demandas", office.get("demanda_id")) if office.get("demanda_id") else None
        linked_demand = enrich_demand(repo, linked_demand) if linked_demand else None
        alerts.append(
            {
                "tipo": "OFICIO",
                "titulo": office.get("titulo"),
                "descricao": f"Cobrar {office.get('orgao_destino')} hoje. {office.get('dias_sem_resposta')}d sem resposta.",
                "action": "open-office",
                "entity_id": office.get("id"),
                "section": "oficios",
                "filtro_contexto": "pending-offices",
                "territorio_id": linked_demand.get("territorio_id") if linked_demand else None,
                "territorio_nome": linked_demand.get("territorio_nome") if linked_demand else None,
            }
        )
    for demand in sorted(open_demands, key=lambda item: ({"VENCIDO": 0, "EM_RISCO": 1}.get(item.get("sla_status"), 2), item.get("prioridade") != "CRITICA"))[:4]:
        sla_label = demand.get("sla_status")
        if sla_label == "VENCIDO":
            description = f"Priorizar retorno. SLA vencido ha {abs(int(demand.get('sla_horas_restantes') or 0))}h."
            context_filter = "sla-overdue"
        elif sla_label == "EM_RISCO":
            description = f"Definir proximo passo hoje. Restam {max(0, int(demand.get('sla_horas_restantes') or 0))}h de SLA."
            context_filter = "sla-risk"
        else:
            description = f"Revisar andamento em {demand.get('status')} e confirmar devolutiva."
            context_filter = "open-demands"
        alerts.append(
            {
                "tipo": "DEMANDA",
                "titulo": demand.get("titulo"),
                "descricao": description,
                "action": "open-demand",
                "entity_id": demand.get("id"),
                "section": "atendimento",
                "filtro_contexto": context_filter,
                "territorio_id": demand.get("territorio_id"),
                "territorio_nome": demand.get("territorio_nome"),
            }
        )
    for convenio in convenios[:2]:
        alerts.append(
            {
                "tipo": "CONVENIO",
                "titulo": convenio.get("titulo"),
                "descricao": f"Validar aderencia politica e prazo com {convenio.get('orgao')}.",
                "action": "open-emendas",
                "entity_id": convenio.get("id"),
                "section": "emendas",
                "filtro_contexto": "amendments",
                "territorio_nome": convenio.get("municipio_alvo"),
            }
        )

    sentiment_snapshot = aggregate_sentiment(sentiments)
    sla_history = ensure_sla_history(repo, current_user["gabinete_id"])
    data = {
        "cards": {
            "demandas_abertas": len(open_demands),
            "sla_em_risco": len(sla_risk),
            "sla_vencido": len(sla_overdue),
            "contatos": len(contacts),
            "liderancas": len(leaders),
            "engajamento_forte": len(strong_engagement),
            "agenda_pendente": len([item for item in agenda if item.get("status") not in {"REALIZADO", "CANCELADO"}]),
            "oficios_pendentes": len([item for item in offices if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}]),
        },
        "sla": {
            "configuracao": sla_config,
            "resumo": {
                "monitoradas": len(open_demands),
                "no_prazo": len([item for item, snapshot in open_demand_sla if snapshot.get("status") == "NO_PRAZO"]),
                "em_risco": len(sla_risk),
                "vencidas": len(sla_overdue),
                "concluidas_no_prazo": len(completed_on_time),
                "concluidas_em_atraso": len(completed_late),
            },
            "fila": [
                {
                    "id": item.get("id"),
                    "titulo": item.get("titulo"),
                    "prioridade": item.get("prioridade"),
                    "status": item.get("status"),
                    "cidadao_nome": item.get("cidadao_nome"),
                    "territorio_nome": item.get("territorio_nome"),
                    "sla_status": snapshot.get("status"),
                    "horas_restantes": snapshot.get("horas_restantes"),
                    "prazo_horas": snapshot.get("prazo_horas"),
                }
                for item, snapshot in sorted(
                    open_demand_sla,
                    key=lambda pair: ({"VENCIDO": 0, "EM_RISCO": 1, "NO_PRAZO": 2}.get(pair[1].get("status"), 3), pair[1].get("horas_restantes") if pair[1].get("horas_restantes") is not None else 999999),
                )[:5]
            ],
            "historico_mensal": aggregate_sla_history(sla_history),
        },
        "heatmap": heatmap[:8],
        "equipes_produtividade": [
            enrich_team(repo, team)
            for team in sorted(
                repo.all("equipes"),
                key=lambda entry: team_productivity_snapshot(repo, entry).get("cadastros", 0)
                + team_productivity_snapshot(repo, entry).get("demandas", 0),
                reverse=True,
            )[:6]
        ],
        "sentimento": sentiment_snapshot,
        "emendas": amendment_totals,
        "legislativo": [{"etapa": key, "quantidade": value} for key, value in kanban.items()],
        "alertas": alerts[:8],
    }
    return success(request, data)


@router.get("/documentos-juridicos")
def list_legal_documents(
    request: Request,
    tipo: str | None = None,
    status: str | None = None,
    demanda_id: str | None = None,
    autor_usuario_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "documentos", repo, locals().copy(), ("titulo", "tipo", "status"))


@router.post("/pareceres", status_code=201)
def create_parecer(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "status"))
    now = iso_now()
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "tipo": "PARECER",
        "versao_atual": 1,
        "autor_usuario_id": current_user["id"],
        "versoes": [{"id": new_id(), "numero_versao": 1, "resumo_alteracao": "Versao inicial", "created_at": now}],
    }
    created = repo.create("documentos", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "documento", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/pareceres/{documento_id}")
def get_parecer(
    request: Request,
    documento_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    item = repo.get("documentos", documento_id)
    if not item or item.get("tipo") != "PARECER":
        not_found("Parecer")
    return success(request, item)


@router.put("/pareceres/{documento_id}")
def update_parecer(
    request: Request,
    documento_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("documentos", documento_id)
    if not previous or previous.get("tipo") != "PARECER":
        not_found("Parecer")
    updated = repo.update("documentos", documento_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "documento", documento_id, "UPDATE", previous, updated)
    return success(request, updated)


@router.get("/protocolos")
def list_protocols(
    request: Request,
    tipo_protocolo_id: str | None = None,
    status: str | None = None,
    responsavel_usuario_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "protocolos", repo, locals().copy(), ("titulo", "numero", "status"))


@router.post("/protocolos", status_code=201)
def create_protocol(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "status"))
    created = repo.create("protocolos", {**payload, "gabinete_id": current_user["gabinete_id"]})
    repo.audit(current_user["gabinete_id"], current_user["id"], "protocolo", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/protocolos/{protocolo_id}")
def get_protocol(
    request: Request,
    protocolo_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    item = repo.get("protocolos", protocolo_id)
    if not item:
        not_found("Protocolo")
    return success(request, item)


@router.put("/protocolos/{protocolo_id}")
def update_protocol(
    request: Request,
    protocolo_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("protocolos", protocolo_id)
    if not previous:
        not_found("Protocolo")
    updated = repo.update("protocolos", protocolo_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "protocolo", protocolo_id, "UPDATE", previous, updated)
    return success(request, updated)


@router.get("/tarefas")
def list_tasks(
    request: Request,
    status: str | None = None,
    responsavel_usuario_id: str | None = None,
    prioridade: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "tarefas", repo, locals().copy(), ("titulo", "descricao", "status"))


@router.post("/tarefas", status_code=201)
def create_task(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("titulo", "responsavel_usuario_id", "prioridade", "status"))
    created = repo.create("tarefas", {**payload, "gabinete_id": current_user["gabinete_id"]})
    repo.audit(current_user["gabinete_id"], current_user["id"], "tarefa", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/projetos")
def list_projects(
    request: Request,
    status: str | None = None,
    prioritario: bool | None = None,
    territorio_id: str | None = None,
    responsavel_usuario_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    return list_response(request, "projetos", repo, locals().copy(), ("nome", "descricao", "status"))


@router.post("/projetos", status_code=201)
def create_project(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome", "status"))
    created = repo.create("projetos", {**payload, "gabinete_id": current_user["gabinete_id"], "prioritario": payload.get("prioritario", False)})
    repo.audit(current_user["gabinete_id"], current_user["id"], "projeto", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.get("/projetos/{projeto_id}")
def get_project(
    request: Request,
    projeto_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    item = repo.get("projetos", projeto_id)
    if not item:
        not_found("Projeto")
    return success(request, item)


@router.put("/projetos/{projeto_id}")
def update_project(
    request: Request,
    projeto_id: str,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    previous = repo.get("projetos", projeto_id)
    if not previous:
        not_found("Projeto")
    updated = repo.update("projetos", projeto_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "projeto", projeto_id, "UPDATE", previous, updated)
    return success(request, updated)


@router.get("/territorial/dashboard")
def territorial_dashboard(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    regiao_id: str | None = None,
    bairro_id: str | None = None,
    microarea_id: str | None = None,
    tema: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    demands = repo.all("demandas")
    events = repo.all("agenda_eventos")
    territories = repo.all("territorios")
    by_territory = []
    for territory in territories:
        count = len([item for item in demands if item.get("territorio_id") == territory["id"]])
        if count:
            by_territory.append({"territorio_id": territory["id"], "territorio_nome": territory["nome"], "quantidade_demandas": count})
    themes: dict[str, int] = {}
    for demand in demands:
        category = category_name(repo, demand.get("categoria_id")) or "Sem categoria"
        themes[category] = themes.get(category, 0) + 1
    data = {
        "cards": {
            "quantidade_demandas": len(demands),
            "quantidade_visitas": 0,
            "quantidade_eventos": len(events),
            "tempo_medio_atendimento_horas": None,
        },
        "mapa": by_territory,
        "temas": [{"tema": key, "quantidade": value} for key, value in themes.items()],
    }
    return success(request, data)


@router.get("/relatorios/catalogo")
def report_catalog(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    return success(
        request,
        [
            {"codigo": "operacional", "nome": "Relatorio Operacional", "categorias": ["OPERACIONAL"], "formatos": ["json", "pdf", "xlsx"]},
            {"codigo": "juridico", "nome": "Relatorio Juridico", "categorias": ["JURIDICO"], "formatos": ["json", "pdf"]},
            {"codigo": "territorial", "nome": "Relatorio Territorial", "categorias": ["TERRITORIAL"], "formatos": ["json", "pdf"]},
            {"codigo": "executivo", "nome": "Relatorio Executivo", "categorias": ["EXECUTIVO"], "formatos": ["json", "pdf"]},
        ],
    )


@router.post("/uploads", status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    contexto: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    digest = hashlib.sha256(contents).hexdigest()
    storage_name = f"{new_id()}-{Path(file.filename or 'arquivo').name}"
    storage_path = settings.upload_dir / storage_name
    storage_path.write_bytes(contents)
    try:
        storage_reference = str(storage_path.relative_to(settings.root_dir)).replace("\\", "/")
    except ValueError:
        storage_reference = storage_name
    item = {
        "gabinete_id": current_user["gabinete_id"],
        "nome_original": file.filename,
        "nome_storage": storage_name,
        "mime_type": file.content_type or "application/octet-stream",
        "tamanho_bytes": len(contents),
        "hash_sha256": digest,
        "url_storage": storage_reference,
        "contexto": contexto,
        "uploaded_by": current_user["id"],
        "uploaded_at": iso_now(),
        "ativo": True,
        "url_publica": f"/uploads-public/{storage_name}",
    }
    created = repo.create("uploads", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "upload", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


@router.post("/mobile/sync")
def mobile_sync(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("items",))
    processed = []
    errors = []
    for item in payload.get("items", []):
        client_id = item.get("client_generated_id")
        entity = item.get("entidade")
        existing = next(
            (
                sync
                for sync in repo.all("sync_mobile")
                if sync.get("usuario_id") == current_user["id"]
                and sync.get("client_generated_id") == client_id
                and sync.get("entidade") == entity
            ),
            None,
        )
        if existing:
            processed.append({"client_generated_id": client_id, "entidade": entity, "entidade_id": existing.get("entidade_id"), "status": "PROCESSADO"})
            continue
        try:
            body = item.get("payload") or {}
            if entity == "contato":
                created = repo.create(
                    "contatos",
                    {
                        **body,
                        "gabinete_id": current_user["gabinete_id"],
                        "equipe_id": body.get("equipe_id") or current_user.get("equipe_id"),
                        "cadastrado_por_usuario_id": body.get("cadastrado_por_usuario_id") or current_user["id"],
                        "origem_cadastro": body.get("origem_cadastro", "MOBILE_CAMPO"),
                        "status": body.get("status", "ATIVO"),
                        "duplicidade_suspeita": False,
                    },
                )
            elif entity == "demanda":
                if not body.get("cidadao_id") or not repo.get("contatos", body["cidadao_id"]):
                    raise ValueError("Toda demanda mobile deve estar vinculada a um demandante cadastrado.")
                opened_at = iso_now()
                opened_at_dt = parse_iso_datetime(opened_at) or datetime.now(timezone.utc)
                sla_config = get_sla_settings(repo, current_user["gabinete_id"])
                created = repo.create(
                    "demandas",
                    {
                        **body,
                        "gabinete_id": current_user["gabinete_id"],
                        "equipe_id": body.get("equipe_id") or current_user.get("equipe_id") or repo.get("contatos", body["cidadao_id"]).get("equipe_id"),
                        "gerada_por_usuario_id": body.get("gerada_por_usuario_id") or current_user["id"],
                        "origem_cadastro": body.get("origem_cadastro", "MOBILE_CAMPO"),
                        "status": body.get("status", "ABERTA"),
                        "prioridade": body.get("prioridade", "MEDIA"),
                        "sla_data": body.get("sla_data") or (opened_at_dt + timedelta(hours=sla_hours_by_priority(body.get("prioridade", "MEDIA"), sla_config))).isoformat(),
                        "data_abertura": opened_at,
                    },
                )
                record_sla_history(repo, current_user["gabinete_id"], enrich_demand(repo, created), "MOBILE_SYNC")
                create_history(repo, created["id"], current_user["id"], "MOBILE_SYNC", None, created.get("status"), "Criada via sincronizacao mobile.")
            else:
                raise ValueError("Entidade nao suportada.")
            repo.create(
                "sync_mobile",
                {
                    "gabinete_id": current_user["gabinete_id"],
                    "usuario_id": current_user["id"],
                    "client_generated_id": client_id,
                    "entidade": entity,
                    "entidade_id": created["id"],
                    "status": "PROCESSADO",
                },
            )
            processed.append({"client_generated_id": client_id, "entidade": entity, "entidade_id": created["id"], "status": "PROCESSADO"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"client_generated_id": client_id, "entidade": entity, "status": "ERRO", "message": str(exc)})
    return success(request, {"processed": processed, "errors": errors})


def module_label(modulo: str | None) -> str:
    labels = {
        "executivo": "Comando Central",
        "atendimento": "Atendimento",
        "crm": "Relacionamento",
        "agenda": "Agenda",
        "legislativo": "Legislativo",
        "emendas": "Emendas",
        "oficios": "Oficios",
        "cadastros": "Cadastros",
        "compliance": "Conformidade",
        "mobile": "Aplicativo",
    }
    return labels.get(modulo or "", "Operacao")


def ai_action(
    titulo: str,
    descricao: str,
    label: str,
    action: str,
    section: str,
    entity_id: str | None = None,
) -> dict[str, Any]:
    description_map = {
        "focus-demand-edit": "Ajuste o cadastro e siga.",
        "focus-demand-assignee": "Defina o dono agora.",
        "open-contact": "Use o historico do contato.",
        "open-demand": "Abra a fila e avance.",
        "focus-interaction-form": "Registre um novo contato.",
        "focus-demand-create": "Converta em demanda.",
        "focus-contact-edit": "Corrija o cadastro.",
        "focus-agenda-report": "Feche o registro.",
        "open-agenda": "Revise a agenda.",
        "open-office": "Veja o oficio.",
        "open-emendas": "Revise a carteira.",
        "open-legislative": "Revise a pauta.",
        "open-compliance": "Veja o registro.",
        "open-mobile": "Confira a sincronizacao.",
        "focus-agenda-create-sentiment": "Abra uma resposta curta.",
        "open-territory-demand-list": "Veja o recorte local.",
        "focus-contact-create-territory": "Cadastre a base local.",
        "focus-demand-create-territory": "Abra a demanda local.",
    }
    label_map = {
        "focus-demand-edit": "Editar",
        "focus-demand-assignee": "Atribuir",
        "open-contact": "Abrir CRM",
        "open-demand": "Abrir",
        "focus-interaction-form": "Registrar",
        "focus-demand-create": "Criar",
        "focus-contact-edit": "Editar",
        "focus-agenda-report": "Fechar",
        "open-agenda": "Abrir",
        "open-office": "Abrir",
        "open-emendas": "Abrir",
        "open-legislative": "Abrir",
        "open-compliance": "Abrir",
        "open-mobile": "Abrir",
        "focus-agenda-create-sentiment": "Criar",
        "open-territory-demand-list": "Abrir",
        "focus-contact-create-territory": "Cadastrar",
        "focus-demand-create-territory": "Criar",
    }
    return {
        "titulo": titulo,
        "descricao": description_map.get(action, descricao),
        "label": label_map.get(action, label),
        "action": action,
        "section": section,
        "entity_id": entity_id,
    }


def ai_resolve_context(repo: JsonStore, payload: dict[str, Any]) -> dict[str, Any]:
    contexto_tipo = payload.get("contexto_tipo") or "modulo"
    contexto_id = payload.get("contexto_id")
    modulo = payload.get("modulo") or "executivo"
    origem = payload.get("origem") or "painel"
    filtro = payload.get("filtro")

    if contexto_tipo == "demanda":
        if not contexto_id:
            business_rule("Contexto de demanda exige contexto_id.")
        demand = repo.get("demandas", contexto_id)
        if not demand:
            not_found("Demanda")
        item = enrich_demand(repo, demand)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "atendimento",
            "origem": origem,
            "filtro": filtro,
            "rotulo": item.get("titulo") or "Demanda",
            "subtitulo": f"{item.get('cidadao_nome') or 'Demandante pendente'} - {item.get('territorio_nome') or 'Sem territorio'}",
            "item": item,
        }

    if contexto_tipo == "contato":
        if not contexto_id:
            business_rule("Contexto de contato exige contexto_id.")
        contact = repo.get("contatos", contexto_id)
        if not contact:
            not_found("Contato")
        item = enrich_contact(repo, contact)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "crm",
            "origem": origem,
            "filtro": filtro,
            "rotulo": item.get("nome") or "Contato",
            "subtitulo": f"{item.get('nivel_relacionamento') or 'CONTATO'} - {item.get('territorio_nome') or item.get('bairro') or 'Sem territorio'}",
            "item": item,
        }

    if contexto_tipo == "agenda":
        if not contexto_id:
            business_rule("Contexto de agenda exige contexto_id.")
        agenda = repo.get("agenda_eventos", contexto_id)
        if not agenda:
            not_found("Compromisso")
        item = enrich_agenda(repo, agenda)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "agenda",
            "origem": origem,
            "filtro": filtro,
            "rotulo": item.get("titulo") or "Compromisso",
            "subtitulo": f"{item.get('local_texto') or 'Local a confirmar'} - {item.get('status') or 'SEM_STATUS'}",
            "item": item,
        }

    if contexto_tipo == "oficio":
        if not contexto_id:
            business_rule("Contexto de oficio exige contexto_id.")
        office = repo.get("oficios", contexto_id)
        if not office:
            not_found("Oficio")
        item = enrich_office(repo, office)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "oficios",
            "origem": origem,
            "filtro": filtro,
            "rotulo": item.get("titulo") or item.get("numero") or "Oficio",
            "subtitulo": f"{item.get('orgao_destino') or 'Destino nao informado'} - {item.get('status') or 'SEM_STATUS'}",
            "item": item,
        }

    if contexto_tipo == "emenda":
        if not contexto_id:
            business_rule("Contexto de emenda exige contexto_id.")
        amendment = repo.get("emendas", contexto_id)
        if not amendment:
            not_found("Emenda")
        item = enrich_amendment(repo, amendment)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "emendas",
            "origem": origem,
            "filtro": filtro,
            "rotulo": item.get("titulo") or item.get("numero") or "Emenda",
            "subtitulo": f"{item.get('beneficiario') or 'Sem beneficiario'} - {item.get('status_execucao') or 'SEM_STATUS'}",
            "item": item,
        }

    if contexto_tipo == "territorio":
        territory = repo.get("territorios", contexto_id) if contexto_id else None
        territory_name_value = territory.get("nome") if territory else (filtro or "Sem territorio")
        demands = [enrich_demand(repo, item) for item in repo.all("demandas")]
        contacts = [enrich_contact(repo, item) for item in repo.all("contatos")]
        territory_demands = [
            item
            for item in demands
            if item.get("territorio_id") == contexto_id or territory_scope_matches(item.get("territorio_nome"), territory_name_value)
        ]
        territory_contacts = [
            item
            for item in contacts
            if item.get("territorio_id") == contexto_id
            or territory_scope_matches(item.get("territorio_nome"), territory_name_value)
            or territory_scope_matches(item.get("bairro"), territory_name_value)
        ]
        score = len(territory_demands) * 3 + len([item for item in territory_contacts if item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"]) * 2 + len(territory_contacts)
        return {
            "tipo": contexto_tipo,
            "id": contexto_id,
            "modulo": modulo or "executivo",
            "origem": origem,
            "filtro": territory_name_value,
            "rotulo": territory_name_value,
            "subtitulo": f"{len(territory_demands)} demanda(s) e {len(territory_contacts)} contato(s) no territorio",
            "item": {
                "territorio_id": contexto_id,
                "territorio_nome": territory_name_value,
                "tipo": territory.get("tipo") if territory else None,
                "demandas": len(territory_demands),
                "contatos": len(territory_contacts),
                "liderancas": len([item for item in territory_contacts if item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"]),
                "engajamento_forte": len([item for item in territory_contacts if item.get("engajamento") in {"FORTE", "ALTO"}]),
                "score": score,
                "nivel_pressao": pressure_level(score),
            },
        }

    if contexto_tipo == "sentimento":
        all_sentiments = repo.all("sentimento_social")
        selected_channel = payload.get("canal")
        selected_period = payload.get("periodo")
        selected_territory = payload.get("territorio")
        scoped_sentiments = select_sentiments(all_sentiments, selected_channel, selected_period, selected_territory)
        sentiment_snapshot = aggregate_sentiment(scoped_sentiments)
        sentiment_focus = filtro or "negative"
        selected_parts = [part for part in [selected_channel, selected_period, selected_territory] if part]
        return {
            "tipo": contexto_tipo,
            "id": sentiment_snapshot.get("coletado_em"),
            "modulo": modulo or "executivo",
            "origem": origem,
            "filtro": sentiment_focus,
            "rotulo": f"Sentimento {sentiment_focus}",
            "subtitulo": " | ".join(selected_parts) if selected_parts else (sentiment_snapshot.get("tema") or "Humor publico das ultimas 24h"),
            "item": {
                **sentiment_snapshot,
                "foco": sentiment_focus,
                "canal_selecionado": selected_channel,
                "periodo_selecionado": selected_period,
                "territorio_selecionado": selected_territory,
            },
        }

    if contexto_tipo == "dashboard_card":
        card_labels = {
            "open-demands": ("Demandas abertas", "Fila operacional do atendimento"),
            "contacts": ("Contatos", "Base politica ativa"),
            "leadership": ("Liderancas", "Rede de influencia do mandato"),
            "strong-engagement": ("Engajamento forte", "Base mobilizada para acao"),
            "pending-agenda": ("Agenda pendente", "Compromissos ainda em aberto"),
            "pending-offices": ("Oficios pendentes", "Pendencias institucionais"),
            "amendments": ("Emendas", "Execucao orcamentaria"),
            "legislative": ("Legislativo", "Fluxo legislativo atual"),
        }
        title, subtitle = card_labels.get(filtro, ("Painel estrategico", "Leitura assistida do dashboard"))
        return {
            "tipo": contexto_tipo,
            "id": None,
            "modulo": modulo or "executivo",
            "origem": origem,
            "filtro": filtro,
            "rotulo": title,
            "subtitulo": subtitle,
            "item": None,
        }

    return {
        "tipo": "modulo",
        "id": None,
        "modulo": modulo,
        "origem": origem,
        "filtro": filtro,
        "rotulo": module_label(modulo),
        "subtitulo": "Leitura assistida do modulo atual",
        "item": None,
    }


def ai_build_summary(repo: JsonStore, context: dict[str, Any]) -> str:
    context_type = context["tipo"]
    item = context.get("item") or {}

    if context_type == "demanda":
        age = days_since(item.get("data_abertura") or item.get("created_at"))
        age_text = f"{age} dia(s)" if age is not None else "tempo indefinido"
        decision_text = "Defina responsavel e proximo passo."
        if context.get("origem") == "alerta" and context.get("filtro") == "sla-overdue":
            decision_text = "Acao imediata: devolver e registrar andamento."
        elif context.get("origem") == "alerta" and context.get("filtro") == "sla-risk":
            decision_text = "Previna vencimento: avance hoje no fluxo."
        return (
            f"{item.get('titulo')}. {item.get('prioridade') or 'MEDIA'} | {item.get('status') or 'SEM_STATUS'} | {age_text}. "
            f"Territorio {item.get('territorio_nome') or 'nao definido'}; responsavel {item.get('responsavel_nome') or 'nao atribuido'}. {decision_text}"
        )

    if context_type == "contato":
        interactions = len([entry for entry in repo.all("interacoes") if entry.get("cidadao_id") == context.get("id")])
        demands = len([entry for entry in repo.all("demandas") if entry.get("cidadao_id") == context.get("id")])
        return (
            f"{item.get('nome')}. {item.get('nivel_relacionamento') or 'CONTATO'} com engajamento {item.get('engajamento') or 'FRIO'}. "
            f"Ha {interactions} interacao(oes) e {demands} demanda(s). Decida relacionamento ou atendimento."
        )

    if context_type == "agenda":
        return (
            f"{item.get('titulo')}. {item.get('status') or 'SEM_STATUS'} em {item.get('local_texto') or 'local a confirmar'}. "
            f"Responsavel {item.get('responsavel_nome') or 'nao definido'}. Confirme briefing e entrega."
        )

    if context_type == "oficio":
        late = item.get("dias_sem_resposta") or 0
        late_text = f"{late} dia(s) sem resposta" if late else "acompanhamento em dia"
        decision_text = "Cobre o orgao e atualize a demanda vinculada."
        if context.get("origem") != "alerta":
            decision_text = "Valide follow-up e proximo contato institucional."
        return (
            f"{item.get('numero') or 'Oficio'} | {item.get('status') or 'SEM_STATUS'} | {late_text}. "
            f"Destino {item.get('orgao_destino') or 'nao informado'}; demanda {item.get('demanda_titulo') or 'nao vinculada'}. {decision_text}"
        )

    if context_type == "emenda":
        return (
            f"{item.get('numero') or 'Emenda'} | {item.get('status_execucao') or 'SEM_STATUS'}. "
            f"Pleiteado {format_currency_brl(item.get('valor_indicado') or 0)}, aprovado {format_currency_brl(item.get('valor_aprovado') or 0)} e empenhado {format_currency_brl(item.get('valor_empenhado') or 0)}. "
            f"Beneficiario {item.get('beneficiario') or 'nao informado'}; empenho {format_date_br(item.get('data_empenho')) if item.get('data_empenho') else 'sem data'}."
        )

    if context_type == "territorio":
        heatmap_text = "Priorize resposta local."
        if context.get("origem") == "heatmap":
            heatmap_text = f"Pressao {str(item.get('nivel_pressao') or 'BAIXA').lower()}: priorize resposta local."
        return (
            f"{item.get('territorio_nome') or 'Sem territorio'}: {item.get('demandas') or 0} demandas, {item.get('contatos') or 0} contatos, "
            f"{item.get('liderancas') or 0} liderancas. {heatmap_text}"
        )

    if context_type == "sentimento":
        selected_scope = [part for part in [item.get("canal_selecionado"), item.get("periodo_selecionado"), item.get("territorio_selecionado")] if part]
        scope_text = f" Recorte: {' / '.join(selected_scope)}." if selected_scope else ""
        return (
            f"Tema {item.get('tema') or 'Sem tema'}: {item.get('negativo') or 0}% negativo, {item.get('neutro') or 0}% neutro, {item.get('positivo') or 0}% positivo. "
            f"Decida resposta publica e agenda de escuta. {item.get('alerta') or 'Sem alerta.'}{scope_text}"
        )

    if context_type == "dashboard_card":
        overview = ai_overview_snapshot(repo)
        filtro = context.get("filtro")
        if filtro == "open-demands":
            return f"{overview['open_demands']} demandas abertas; {overview['unassigned_demands']} sem responsavel; {overview['critical_demands']} prioritarias. Ataque fila e dono."
        if filtro == "contacts":
            return f"Base com {overview['contacts']} contatos, {overview['leaders']} liderancas e {overview['strong_engagement']} engajados. Priorize cobertura e mobilizacao."
        if filtro == "leadership":
            return f"{overview['leaders']} liderancas mapeadas. Reative lacunas e proteja influencia territorial."
        if filtro == "strong-engagement":
            return f"{overview['strong_engagement']} contatos com engajamento forte. Converta mobilizacao em agenda ou entrega."
        if filtro == "pending-agenda":
            return f"{overview['pending_agenda']} compromissos pendentes. Confirme briefing, local e resultado esperado."
        if filtro == "pending-offices":
            return f"{overview['pending_offices']} oficios pendentes; {overview['late_offices']} com atraso relevante. Priorize cobranca institucional."
        if filtro == "amendments":
            return f"Emendas: {overview['amendments_approved']} aprovadas e {overview['amendments_committed']} com empenho. Revise captação e destino."
        if filtro == "legislative":
            return f"{overview['propositions']} proposicoes ativas. Identifique etapa travada e proxima acao politica."
        return "Painel consolidado. Escolha a frente com maior risco ou maior retorno politico." 

    overview = ai_overview_snapshot(repo)
    modulo = context.get("modulo")
    if modulo == "executivo":
        return f"Comando central: {overview['open_demands']} demandas abertas, {overview['pending_offices']} oficios pendentes e {overview['pending_agenda']} compromissos abertos. Decida a frente do dia."
    if modulo == "atendimento":
        return f"Atendimento com {overview['open_demands']} demandas abertas e {overview['unassigned_demands']} sem responsavel. Distribua e avance fluxo."
    if modulo == "crm":
        return f"CRM com {overview['contacts']} contatos, {overview['leaders']} liderancas e {overview['strong_engagement']} engajados. Priorize relacionamento ativo."
    if modulo == "agenda":
        return f"Agenda com {overview['pending_agenda']} compromissos pendentes. Confirme execucao e devolutiva."
    if modulo == "oficios":
        return f"Oficios com {overview['pending_offices']} pendencias e {overview['late_offices']} atrasos criticos. Cobre resposta e registre retorno."
    if modulo == "emendas":
        return f"Emendas com {overview['amendments_approved']} aprovadas e {overview['amendments_committed']} empenhadas. Revise captação e beneficiarios."
    if modulo == "legislativo":
        return f"Legislativo com {overview['propositions']} proposicoes. Destrave a etapa mais carregada."
    if modulo == "compliance":
        return f"Compliance acompanha {overview['audit_entries']} registros recentes. Preserve rastreabilidade."
    if modulo == "cadastros":
        return f"Cadastros: {overview['contacts']} contatos, {overview['users']} usuarios e {overview['territories']} territorios. Existem campos nao preenchidos em cadastros." 
    if modulo == "mobile":
        return f"Mobile com {overview['sync_entries']} sincronizacoes e {overview['sync_errors']} erros. Trate falhas de campo."
    return "Contexto localizado para apoio operacional. Revise os dados antes de agir."


def ai_overview_snapshot(repo: JsonStore) -> dict[str, Any]:
    demands = [enrich_demand(repo, item) for item in repo.all("demandas")]
    contacts = [enrich_contact(repo, item) for item in repo.all("contatos")]
    agenda = [enrich_agenda(repo, item) for item in repo.all("agenda_eventos")]
    offices = [enrich_office(repo, item) for item in repo.all("oficios")]
    amendments = [enrich_amendment(repo, item) for item in repo.all("emendas")]
    propositions = repo.all("proposicoes")
    sync_entries = repo.all("sync_mobile")
    open_status = {"ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"}
    open_demands = [item for item in demands if item.get("status") in open_status]
    pending_agenda = [item for item in agenda if item.get("status") not in {"REALIZADO", "CANCELADO"}]
    pending_offices = [item for item in offices if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}]
    indicated = sum(float(item.get("valor_indicado") or 0) for item in amendments)
    approved = sum(float(item.get("valor_aprovado") or 0) for item in amendments)
    committed = sum(float(item.get("valor_empenhado") or 0) for item in amendments)
    return {
        "open_demands": len(open_demands),
        "unassigned_demands": len([item for item in open_demands if not item.get("responsavel_usuario_id")]),
        "critical_demands": len([item for item in open_demands if item.get("prioridade") in {"ALTA", "CRITICA"}]),
        "contacts": len(contacts),
        "leaders": len([item for item in contacts if item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"]),
        "strong_engagement": len([item for item in contacts if item.get("engajamento") in {"FORTE", "ALTO"}]),
        "pending_agenda": len(pending_agenda),
        "pending_offices": len(pending_offices),
        "late_offices": len([item for item in pending_offices if (item.get("dias_sem_resposta") or 0) >= 15]),
        "amendments_approved_percent": round((approved / indicated) * 100, 1) if indicated else 0,
        "amendments_committed_percent": round((committed / approved) * 100, 1) if approved else 0,
        "amendments_approved": len([item for item in amendments if item.get("status_execucao") in {"APROVADA", "EMPENHADA"}]),
        "amendments_committed": len([item for item in amendments if item.get("status_execucao") == "EMPENHADA"]),
        "propositions": len(propositions),
        "audit_entries": len(repo.all("auditoria")),
        "users": len(repo.all("usuarios")),
        "territories": len(repo.all("territorios")),
        "sync_entries": len(sync_entries),
        "sync_errors": len([item for item in sync_entries if item.get("status") == "ERRO"]),
    }


def ai_build_suggestions(repo: JsonStore, context: dict[str, Any]) -> list[dict[str, Any]]:
    context_type = context["tipo"]
    item = context.get("item") or {}

    if context_type == "demanda":
        suggestions: list[dict[str, Any]] = []
        if not item.get("cidadao_id"):
            suggestions.append(ai_action("Regularizar demandante", "A demanda precisa de um contato vinculado antes de ganhar tracao operacional.", "Editar demanda", "focus-demand-edit", "atendimento", context["id"]))
        if not item.get("responsavel_usuario_id"):
            suggestions.append(ai_action("Atribuir responsavel", "Sem dono interno, a fila tende a perder prazo e rastreabilidade.", "Definir responsavel", "focus-demand-assignee", "atendimento", context["id"]))
        if item.get("cidadao_id"):
            suggestions.append(ai_action("Abrir CRM do demandante", "Use o historico politico para qualificar abordagem e promessa de retorno.", "Abrir relacionamento", "open-contact", "crm", item.get("cidadao_id")))
            if not item.get("cidadao_foto_url"):
                suggestions.append(ai_action("Incluir foto do beneficiario", "Sem foto, a identificacao do perfil perde velocidade nas filas e no relacionamento politico.", "Editar cadastro", "focus-contact-edit", "cadastros", item.get("cidadao_id")))
        if item.get("status") in {"ABERTA", "EM_TRIAGEM", "REABERTA"}:
            suggestions.append(ai_action("Conduzir a proxima etapa", "A demanda ainda depende de definicao de andamento no fluxo de atendimento.", "Abrir fluxo", "open-demand", "atendimento", context["id"]))
        if not item.get("territorio_id") and not item.get("territorio_nome"):
            suggestions.append(ai_action("Associar territorio", "Sem territorio, o comando central perde leitura de base e cobertura territorial.", "Editar demanda", "focus-demand-edit", "atendimento", context["id"]))
        if item.get("responsavel_usuario_id") and not item.get("responsavel_foto_url"):
            suggestions.append(ai_action("Atualizar foto do responsavel", "A foto do colaborador melhora triagem visual, distribuicao e leitura das filas operacionais.", "Editar colaborador", "focus-user-edit", "cadastros", item.get("responsavel_usuario_id")))
        if item.get("tipo_demanda") == "INDICACAO_VAGA":
            if not item.get("cv_upload_id"):
                suggestions.append(ai_action("Anexar curriculo", "A indicacao para vaga precisa do CV antes do envio para triagem externa.", "Editar demanda", "focus-demand-edit", "atendimento", context["id"]))
            if not item.get("tipo_vaga_pretendida"):
                suggestions.append(ai_action("Definir tipo da vaga", "Sem tipo de vaga, a triagem perde velocidade e assertividade.", "Editar demanda", "focus-demand-edit", "atendimento", context["id"]))
            if item.get("status") == "CONCLUIDA":
                suggestions.append(ai_action("Arquivar com nota de conclusao", "Agora atualize a situacao para Arquivada e substitua a descricao por uma nota objetiva de alocacao ou encerramento.", "Editar", "focus-demand-edit", "atendimento", context["id"]))
        return suggestions[:4]

    if context_type == "contato":
        suggestions = [
            ai_action("Registrar nova interacao", "Movimente o relacionamento com um novo contato, retorno ou convite territorial.", "Abrir interacao", "focus-interaction-form", "crm", context["id"]),
            ai_action("Converter relacionamento em atendimento", "Quando ha demanda latente, o fluxo de atendimento deve sair do CRM e entrar na fila operacional.", "Abrir nova demanda", "focus-demand-create", "atendimento", context["id"]),
        ]
        if not item.get("foto_url_publica"):
            suggestions.append(ai_action("Incluir foto do perfil", "A foto e opcional, mas acelera a identificacao em bases grandes e melhora a leitura operacional.", "Editar cadastro", "focus-contact-edit", "cadastros", context["id"]))
        if not item.get("territorio_id") and not item.get("bairro"):
            suggestions.append(ai_action("Qualificar base territorial", "Sem territorio ou bairro, o contato perde valor estrategico para leitura de mapa.", "Editar cadastro", "focus-contact-edit", "cadastros", context["id"]))
        else:
            suggestions.append(ai_action("Revisar cadastro politico", "Ajuste influencia, engajamento e voto 2028 antes da proxima acao de campo.", "Editar cadastro", "focus-contact-edit", "cadastros", context["id"]))
        return suggestions[:4]

    if context_type == "agenda":
        suggestions = [
            ai_action("Preparar relatorio do compromisso", "Apos o evento, consolide publico, resultado e anexos para nao perder memoria politica.", "Abrir relatorio", "focus-agenda-report", "agenda", context["id"]),
            ai_action("Revisar agenda do modulo", "Use a visao completa para equilibrar agenda parlamentar, equipe e cobertura territorial.", "Abrir agenda", "open-agenda", "agenda", context["id"]),
        ]
        if not item.get("territorio_id") and not item.get("territorio_nome"):
            suggestions.append(ai_action("Associar territorio ao compromisso", "Sem territorio, o impacto do evento nao aparece na leitura territorial consolidada.", "Abrir agenda", "open-agenda", "agenda", context["id"]))
        return suggestions[:4]

    if context_type == "oficio":
        suggestions = [
            ai_action("Revisar follow-up institucional", "Oficios pendentes exigem ritual de cobranca e rastreio de resposta.", "Abrir oficio", "open-office", "oficios", context["id"]),
        ]
        if item.get("demanda_id"):
            suggestions.append(ai_action("Abrir demanda vinculada", "A resposta institucional deve retroalimentar o fluxo de atendimento correspondente.", "Abrir demanda", "open-demand", "atendimento", item.get("demanda_id")))
        else:
            suggestions.append(ai_action("Vincular demanda operacional", "Sem demanda associada, o oficio fica isolado da trilha principal de entrega politica.", "Abrir oficios", "open-office", "oficios", context["id"]))
        return suggestions[:4]

    if context_type == "emenda":
        return [
            ai_action("Revisar execucao da emenda", "Acompanhe gargalo entre indicado, empenhado e pago para antecipar bloqueios politicos.", "Abrir emendas", "open-emendas", "emendas", context["id"]),
            ai_action("Cruzar entrega com territorio", "Sem traducao territorial, a emenda perde capacidade de gerar narrativa de resultado.", "Abrir emendas", "open-emendas", "emendas", context["id"]),
        ]

    if context_type == "territorio":
        return [
            ai_action("Abrir demandas do territorio", "Veja a fila operacional concentrada nesse territorio antes de priorizar resposta politica.", "Abrir demandas", "open-territory-demand-list", "executivo", context.get("id")),
            ai_action("Cadastrar nova demanda territorial", "A leitura territorial vira operacao quando ja sai com territorio predefinido no formulario.", "Nova demanda territorial", "focus-demand-create-territory", "atendimento", context.get("id")),
            ai_action("Qualificar base do territorio", "Feche lacunas de cadastro e engajamento com novos contatos ou liderancas dessa area.", "Novo contato territorial", "focus-contact-create-territory", "cadastros", context.get("id")),
        ]

    if context_type == "sentimento":
        focus = item.get("foco")
        territory_name = item.get("territorio_selecionado") or (item.get("territorios") or [{}])[0].get("territorio")
        if focus == "positive":
            return [
                ai_action("Ativar base favoravel", "Transforme humor positivo em relacionamento documentado e mobilizacao concreta.", "Abrir base mobilizada", "strong-engagement", "executivo"),
                ai_action("Montar agenda de capitalizacao", "Converta o tema em agenda, visita ou entrega politica registrada.", "Nova agenda orientada", "focus-agenda-create-sentiment", "agenda", context.get("id")),
            ]
        suggestions = [
            ai_action("Abrir resposta territorial", "Cruze o alerta com demandas abertas e territórios mais pressionados.", "Ver demandas do territorio", territory_name and territory_name != "Geral" and "open-territory-demand-list" or "open-demands", "executivo", context.get("id")),
            ai_action("Montar agenda de escuta", "Crie um compromisso orientado pelo tema e pelo alerta do sentimento coletado.", "Nova agenda orientada", "focus-agenda-create-sentiment", "agenda", context.get("id")),
        ]
        if territory_name and territory_name != "Geral":
            suggestions.insert(0, ai_action("Focar territorio do alerta", "O recorte territorial do sentimento pode virar leitura operacional imediata.", "Abrir territorio", "open-territory-demand-list", "executivo", context.get("id")))
        unique_suggestions: list[dict[str, Any]] = []
        seen_keys: set[tuple[str | None, str | None, str | None]] = set()
        for suggestion in suggestions:
            key = (suggestion.get("action"), suggestion.get("section"), suggestion.get("entity_id"))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_suggestions.append(suggestion)
        return unique_suggestions[:4]

    if context_type == "dashboard_card":
        filtro = context.get("filtro")
        open_demands = [enrich_demand(repo, item) for item in repo.all("demandas") if item.get("status") in {"ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"}]
        unassigned = next((item for item in open_demands if not item.get("responsavel_usuario_id")), None)
        pending_agenda = next((enrich_agenda(repo, item) for item in repo.all("agenda_eventos") if item.get("status") not in {"REALIZADO", "CANCELADO"}), None)
        pending_office = next((enrich_office(repo, item) for item in sorted(repo.all("oficios"), key=lambda row: str(row.get("created_at") or "")) if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}), None)
        if filtro == "open-demands":
            suggestions = []
            if unassigned:
                suggestions.append(ai_action("Distribuir demanda sem dono", "A forma mais rapida de reduzir risco operacional e atribuir um responsavel agora.", "Atribuir responsavel", "focus-demand-assignee", "atendimento", unassigned.get("id")))
            critical = next((item for item in open_demands if item.get("prioridade") in {"ALTA", "CRITICA"}), None)
            if critical:
                suggestions.append(ai_action("Atacar prioridade critica", "Ha demanda com prioridade elevada aguardando decisao humana.", "Abrir demanda critica", "open-demand", "atendimento", critical.get("id")))
            return suggestions[:4]
        if filtro in {"contacts", "leadership", "strong-engagement"}:
            contact = next((item for item in repo.all("contatos") if item.get("status") != "EXCLUIDO"), None)
            if contact:
                return [
                    ai_action("Registrar movimento de relacionamento", "A base mobilizada se sustenta com interacao registrada, nao so com cadastro passivo.", "Abrir CRM", "open-contact", "crm", contact.get("id")),
                    ai_action("Qualificar cadastro politico", "Revise influencia, engajamento e territorio para leitura mais precisa da base.", "Editar cadastro", "focus-contact-edit", "cadastros", contact.get("id")),
                ]
        if filtro == "pending-agenda" and pending_agenda:
            return [
                ai_action("Preparar o proximo compromisso", "O ganho imediato esta em briefing, confirmacao e relatorio de execucao.", "Abrir relatorio", "focus-agenda-report", "agenda", pending_agenda.get("id")),
                ai_action("Revisar agenda completa", "Equilibre compromissos de equipe e vereador antes de travar a semana.", "Abrir agenda", "open-agenda", "agenda", pending_agenda.get("id")),
            ]
        if filtro == "pending-offices" and pending_office:
            return [
                ai_action("Tratar pendencia institucional critica", "O oficio mais antigo tende a concentrar risco politico e desgaste de retorno.", "Abrir oficio", "open-office", "oficios", pending_office.get("id")),
            ]
        if filtro == "amendments":
            return [ai_action("Abrir carteira de emendas", "Verifique o gargalo financeiro e a traducao da entrega para territorio e narrativa politica.", "Abrir emendas", "open-emendas", "emendas")]
        if filtro == "legislative":
            return [ai_action("Abrir pauta legislativa", "Concentre energia na etapa com maior volume ou maior criticidade politica.", "Abrir legislativo", "open-legislative", "legislativo")]
        if filtro == "territory-pressure":
            return [
                ai_action("Ler territorio mais pressionado", "Priorize o territorio com maior combinacao de demandas, contatos e liderancas.", "Ver territorio", "open-territory-demand-list", "executivo"),
                ai_action("Converter leitura territorial em cadastro", "Use o formulario com territorio predefinido para acelerar resposta politica.", "Novo contato territorial", "focus-contact-create-territory", "cadastros"),
            ]
        if filtro == "negative-sentiment":
            return [
                ai_action("Organizar agenda de resposta", "O humor negativo pede resposta documentada em agenda e escuta de base.", "Nova agenda orientada", "focus-agenda-create-sentiment", "agenda"),
            ]

    modulo = context.get("modulo")
    if modulo == "executivo":
        hottest_demand = next((enrich_demand(repo, item) for item in repo.all("demandas") if item.get("prioridade") in {"ALTA", "CRITICA"}), None)
        oldest_office = next((enrich_office(repo, item) for item in sorted(repo.all("oficios"), key=lambda row: str(row.get("created_at") or "")) if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}), None)
        suggestions = []
        if hottest_demand:
            suggestions.append(ai_action("Atacar demanda critica", "Leve a IA para o fluxo que tem mais chance de gerar desgaste se travar.", "Abrir demanda", "open-demand", "atendimento", hottest_demand.get("id")))
        if oldest_office:
            suggestions.append(ai_action("Cobrar oficio mais antigo", "Pendencia institucional envelhecida precisa de roteiro de follow-up e retorno.", "Abrir oficio", "open-office", "oficios", oldest_office.get("id")))
        return suggestions[:4]
    if modulo == "atendimento":
        demand = next((enrich_demand(repo, item) for item in repo.all("demandas") if item.get("status") in {"ABERTA", "EM_TRIAGEM", "REABERTA"}), None)
        return [ai_action("Revisar fila prioritaria", "Use o atendimento para tirar gargalos de triagem, responsavel e territorio.", "Abrir atendimento", "open-demand", "atendimento", demand.get("id") if demand else None)]
    if modulo == "crm":
        contact = next((item for item in repo.all("contatos") if item.get("status") != "EXCLUIDO"), None)
        if contact:
            return [ai_action("Movimentar base com nova interacao", "Relacionamento sem ritual de contato perde temperatura politica.", "Abrir interacao", "focus-interaction-form", "crm", contact.get("id"))]
    if modulo == "agenda":
        agenda = next((enrich_agenda(repo, item) for item in repo.all("agenda_eventos") if item.get("status") not in {"REALIZADO", "CANCELADO"}), None)
        if agenda:
            return [ai_action("Fechar proximo compromisso", "Confirme briefing, publico estimado e relatorio para nao perder capacidade de execucao.", "Abrir relatorio", "focus-agenda-report", "agenda", agenda.get("id"))]
    if modulo == "oficios":
        office = next((enrich_office(repo, item) for item in sorted(repo.all("oficios"), key=lambda row: str(row.get("created_at") or "")) if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}), None)
        if office:
            return [ai_action("Abrir pendencia institucional", "O foco inicial e o oficio ainda sem retorno formal do orgao destinatario.", "Abrir oficio", "open-office", "oficios", office.get("id"))]
    if modulo == "emendas":
        return [ai_action("Ler execucao da carteira", "Acompanhe percentual pago e empenhado antes de reportar entrega politica.", "Abrir emendas", "open-emendas", "emendas")]
    if modulo == "legislativo":
        return [ai_action("Revisar pauta legislativa", "Mapeie o gargalo por etapa e alinhamento politico necessario.", "Abrir legislativo", "open-legislative", "legislativo")]
    if modulo == "compliance":
        return [ai_action("Abrir rastreabilidade do modulo", "Use auditoria e consistencia cadastral para reduzir risco operacional silencioso.", "Abrir conformidade", "open-compliance", "compliance")]
    if modulo == "cadastros":
        contact = next((item for item in repo.all("contatos") if item.get("status") != "EXCLUIDO" and not item.get("territorio_id") and not item.get("bairro")), None)
        if contact:
            return [ai_action("Corrigir lacuna de cadastro", "Contato sem territorio ou bairro enfraquece mapa, CRM e atendimento.", "Editar cadastro", "focus-contact-edit", "cadastros", contact.get("id"))]
    if modulo == "mobile":
        return [ai_action("Conferir sincronizacao de campo", "Revise itens processados e erros antes de propagar dados incompletos ao gabinete.", "Abrir modulo mobile", "open-mobile", "mobile")]
    return []


def ai_build_operational_context(repo: JsonStore, payload: dict[str, Any]) -> dict[str, Any]:
    context = ai_resolve_context(repo, payload)
    suggestions = ai_build_suggestions(repo, context)
    item = context.get("item") or {}
    return {
        "titulo": f"IA: {module_label(context.get('modulo'))}",
        "subtitulo": context.get("subtitulo") or "Fluxo orientado por contexto",
        "resumo": ai_build_summary(repo, context),
        "contexto": {
            "tipo": context.get("tipo"),
            "id": context.get("id"),
            "modulo": context.get("modulo"),
            "origem": context.get("origem"),
            "rotulo": context.get("rotulo"),
            "filtro": context.get("filtro"),
            "canal": item.get("canal_selecionado"),
            "periodo": item.get("periodo_selecionado"),
            "territorio": item.get("territorio_selecionado") or item.get("territorio_nome") or payload.get("territorio"),
        },
        "sugestoes": suggestions,
    }


@router.post("/ai/contexto-operacional")
def ai_operational_context(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("contexto_tipo",))
    return success(request, ai_build_operational_context(repo, payload))


@router.post("/ai/resumir-contexto")
def ai_summarize_context(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("contexto_tipo",))
    if payload["contexto_tipo"] in {"documento", "parecer"}:
        contexto_id = payload.get("contexto_id")
        if not contexto_id:
            business_rule("Contexto de documento exige contexto_id.")
        doc = repo.get("documentos", contexto_id)
        if not doc:
            not_found("Documento")
        resumo = f"Documento {doc.get('tipo')} em status {doc.get('status')}, versao {doc.get('versao_atual')}: {doc.get('titulo')}."
    else:
        resumo = ai_build_summary(repo, ai_resolve_context(repo, payload))
    return success(request, {"resumo": resumo})


@router.post("/ai/sugerir-proxima-etapa")
def ai_suggest_next_step(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("contexto_tipo",))
    suggestion = "Revisar o historico, confirmar responsavel e registrar a proxima acao manualmente."
    justification = "A IA assistiva nao altera estado automaticamente; ela apenas organiza o proximo passo provavel."
    suggestions = ai_build_suggestions(repo, ai_resolve_context(repo, payload))
    if suggestions:
        suggestion = suggestions[0]["titulo"]
        justification = suggestions[0]["descricao"]
    return success(request, {"sugestao": suggestion, "justificativa": justification})
