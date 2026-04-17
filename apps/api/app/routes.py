from __future__ import annotations

import hashlib
from datetime import datetime, timezone
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


def enrich_contact(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    return enriched


def enrich_demand(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    contact = repo.get("contatos", enriched.get("cidadao_id")) if enriched.get("cidadao_id") else None
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    if not enriched["territorio_nome"] and contact:
        enriched["territorio_nome"] = territory_name(repo, contact.get("territorio_id")) or contact.get("bairro")
        enriched["territorio_id"] = enriched.get("territorio_id") or contact.get("territorio_id")
    enriched["cidadao_nome"] = contact.get("nome") if contact else contact_name(repo, enriched.get("cidadao_id"))
    enriched["categoria_nome"] = category_name(repo, enriched.get("categoria_id"))
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    if enriched.get("status") in {"CONCLUIDA", "CANCELADA"}:
        enriched["criticidade_derivada"] = "BAIXA"
    elif enriched.get("prioridade") == "CRITICA":
        enriched["criticidade_derivada"] = "CRITICA"
    elif enriched.get("prioridade") == "ALTA":
        enriched["criticidade_derivada"] = "ALTA"
    else:
        enriched["criticidade_derivada"] = "NORMAL"
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


def enrich_agenda(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    return enriched


def enrich_proposition(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["responsavel_nome"] = user_name(repo, enriched.get("responsavel_usuario_id"))
    return enriched


def enrich_amendment(repo: JsonStore, item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["territorio_nome"] = territory_name(repo, enriched.get("territorio_id"))
    indicated = float(enriched.get("valor_indicado") or 0)
    paid = float(enriched.get("valor_pago") or 0)
    committed = float(enriched.get("valor_empenhado") or 0)
    enriched["percentual_pago"] = round((paid / indicated) * 100, 1) if indicated else 0
    enriched["percentual_empenhado"] = round((committed / indicated) * 100, 1) if indicated else 0
    return enriched


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
        enrich=public_user,
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
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", created["id"], "CREATE", payload_novo=public_user(created))
    return success(request, public_user(created))


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
    return success(request, public_user(user))


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
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", usuario_id, "UPDATE", public_user(previous), public_user(updated))
    return success(request, public_user(updated))


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
    repo.update("usuarios", usuario_id, {"senha_hash": hash_password("Senha@123")})
    repo.audit(current_user["gabinete_id"], current_user["id"], "usuario", usuario_id, "RESET_SENHA", payload_novo=payload)
    return success(request, {"status": "RESET_ENFILEIRADO"})


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
        list_response(request, "equipes", repo, locals().copy(), ("nome", "descricao"))["data"],
    )


@router.post("/equipes", status_code=201)
def create_team(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("nome",))
    item = {**payload, "gabinete_id": current_user["gabinete_id"], "ativo": payload.get("ativo", True)}
    created = repo.create("equipes", item)
    repo.audit(current_user["gabinete_id"], current_user["id"], "equipe", created["id"], "CREATE", payload_novo=created)
    return success(request, created)


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
    return success(request, team)


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
    updated = repo.update("equipes", equipe_id, payload)
    repo.audit(current_user["gabinete_id"], current_user["id"], "equipe", equipe_id, "UPDATE", previous, updated)
    return success(request, updated)


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
    if payload.get("responsavel_usuario_id") and not repo.get("usuarios", payload["responsavel_usuario_id"]):
        business_rule("responsavel_usuario_id invalido para demanda.")
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "territorio_id": payload.get("territorio_id") or contact.get("territorio_id"),
        "status": payload.get("status", "ABERTA"),
        "prioridade": payload.get("prioridade", "MEDIA"),
        "origem_cadastro": payload.get("origem_cadastro", "WEB_INTERNO"),
        "responsavel_usuario_id": payload.get("responsavel_usuario_id") or current_user["id"],
        "data_abertura": iso_now(),
        "data_conclusao": None,
        "tags": payload.get("tags", []),
        "anexos": payload.get("anexos", []),
    }
    created = repo.create("demandas", item)
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
    if patch.get("responsavel_usuario_id") and not repo.get("usuarios", patch["responsavel_usuario_id"]):
        business_rule("responsavel_usuario_id invalido para demanda.")
    if patch.get("status") == "CONCLUIDA" and not patch.get("data_conclusao"):
        patch["data_conclusao"] = iso_now()
    if patch.get("status") == "ARQUIVADA" and not patch.get("data_arquivamento"):
        patch["data_arquivamento"] = iso_now()
    updated = repo.update("demandas", demanda_id, patch)
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
    require_fields(payload, ("titulo", "numero", "valor_indicado", "status_execucao"))
    item = {
        **payload,
        "gabinete_id": current_user["gabinete_id"],
        "valor_empenhado": float(payload.get("valor_empenhado") or 0),
        "valor_liquidado": float(payload.get("valor_liquidado") or 0),
        "valor_pago": float(payload.get("valor_pago") or 0),
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


@router.get("/political-os/overview")
def political_os_overview(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    contacts = repo.all("contatos")
    demands = [enrich_demand(repo, item) for item in repo.all("demandas")]
    agenda = [enrich_agenda(repo, item) for item in repo.all("agenda_eventos")]
    propositions = repo.all("proposicoes")
    amendments = [enrich_amendment(repo, item) for item in repo.all("emendas")]
    offices = [enrich_office(repo, item) for item in repo.all("oficios")]
    sentiments = repo.all("sentimento_social")
    convenios = repo.all("editais_convenios")

    open_status = {"ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"}
    open_demands = [item for item in demands if item.get("status") in open_status]
    leaders = [
        item
        for item in contacts
        if item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"
    ]
    strong_engagement = [item for item in contacts if item.get("engajamento") in {"FORTE", "ALTO"}]

    territories = repo.all("territorios")
    heatmap = []
    for territory in territories:
        territory_demands = [item for item in demands if item.get("territorio_id") == territory["id"]]
        territory_contacts = [item for item in contacts if item.get("territorio_id") == territory["id"]]
        if not territory_demands and not territory_contacts:
            continue
        score = len(territory_demands) * 3 + len([item for item in territory_contacts if item.get("influencia") == "ALTA"]) * 2 + len(territory_contacts)
        heatmap.append(
            {
                "territorio_id": territory["id"],
                "territorio_nome": territory["nome"],
                "tipo": territory.get("tipo"),
                "demandas": len(territory_demands),
                "contatos": len(territory_contacts),
                "liderancas": len([item for item in territory_contacts if item.get("nivel_relacionamento") == "LIDERANCA" or item.get("influencia") == "ALTA"]),
                "score": score,
            }
        )
    by_bairro: dict[str, dict[str, Any]] = {}
    for contact in contacts:
        if contact.get("territorio_id"):
            continue
        bairro = contact.get("bairro") or "Sem bairro"
        by_bairro.setdefault(bairro, {"territorio_nome": bairro, "demandas": 0, "contatos": 0, "liderancas": 0, "score": 0})
        by_bairro[bairro]["contatos"] += 1
        by_bairro[bairro]["liderancas"] += 1 if contact.get("influencia") == "ALTA" else 0
        by_bairro[bairro]["score"] += 2 if contact.get("influencia") == "ALTA" else 1
    for demand in demands:
        if demand.get("territorio_id"):
            continue
        contact = repo.get("contatos", demand.get("cidadao_id")) if demand.get("cidadao_id") else None
        bairro = demand.get("bairro") or (contact or {}).get("bairro") or "Sem territorio"
        by_bairro.setdefault(bairro, {"territorio_nome": bairro, "demandas": 0, "contatos": 0, "liderancas": 0, "score": 0})
        by_bairro[bairro]["demandas"] += 1
        by_bairro[bairro]["score"] += 3
    heatmap.extend(by_bairro.values())
    if not heatmap:
        for contact in contacts:
            bairro = contact.get("bairro") or "Sem bairro"
            by_bairro.setdefault(bairro, {"territorio_nome": bairro, "demandas": 0, "contatos": 0, "liderancas": 0, "score": 0})
            by_bairro[bairro]["contatos"] += 1
            by_bairro[bairro]["liderancas"] += 1 if contact.get("influencia") == "ALTA" else 0
            by_bairro[bairro]["score"] += 2 if contact.get("influencia") == "ALTA" else 1
        heatmap = list(by_bairro.values())
    heatmap.sort(key=lambda item: item.get("score", 0), reverse=True)

    amendment_totals = {
        "valor_indicado": sum(float(item.get("valor_indicado") or 0) for item in amendments),
        "valor_empenhado": sum(float(item.get("valor_empenhado") or 0) for item in amendments),
        "valor_liquidado": sum(float(item.get("valor_liquidado") or 0) for item in amendments),
        "valor_pago": sum(float(item.get("valor_pago") or 0) for item in amendments),
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
        alerts.append(
            {
                "tipo": "OFICIO",
                "titulo": office.get("titulo"),
                "descricao": f"{office.get('orgao_destino')} sem resposta ha {office.get('dias_sem_resposta')} dias.",
            }
        )
    for demand in [item for item in open_demands if item.get("prioridade") in {"ALTA", "CRITICA"}][:4]:
        alerts.append(
            {
                "tipo": "DEMANDA",
                "titulo": demand.get("titulo"),
                "descricao": f"{demand.get('cidadao_nome') or 'Demandante'} em {demand.get('status')}.",
            }
        )
    for convenio in convenios[:2]:
        alerts.append(
            {
                "tipo": "CONVENIO",
                "titulo": convenio.get("titulo"),
                "descricao": f"{convenio.get('orgao')} - {convenio.get('status')}.",
            }
        )

    latest_sentiment = sentiments[-1] if sentiments else {"positivo": 0, "neutro": 0, "negativo": 0, "alerta": "Sem dados coletados."}
    data = {
        "cards": {
            "demandas_abertas": len(open_demands),
            "contatos": len(contacts),
            "liderancas": len(leaders),
            "engajamento_forte": len(strong_engagement),
            "agenda_pendente": len([item for item in agenda if item.get("status") not in {"REALIZADO", "CANCELADO"}]),
            "oficios_pendentes": len([item for item in offices if item.get("status") not in {"RESPONDIDO", "CONCLUIDO"}]),
        },
        "heatmap": heatmap[:8],
        "sentimento": latest_sentiment,
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
    item = {
        "gabinete_id": current_user["gabinete_id"],
        "nome_original": file.filename,
        "nome_storage": storage_name,
        "mime_type": file.content_type or "application/octet-stream",
        "tamanho_bytes": len(contents),
        "hash_sha256": digest,
        "url_storage": str(storage_path.relative_to(settings.root_dir)).replace("\\", "/"),
        "contexto": contexto,
        "uploaded_by": current_user["id"],
        "uploaded_at": iso_now(),
        "ativo": True,
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
                        "origem_cadastro": body.get("origem_cadastro", "MOBILE_CAMPO"),
                        "status": body.get("status", "ATIVO"),
                        "duplicidade_suspeita": False,
                    },
                )
            elif entity == "demanda":
                if not body.get("cidadao_id") or not repo.get("contatos", body["cidadao_id"]):
                    raise ValueError("Toda demanda mobile deve estar vinculada a um demandante cadastrado.")
                created = repo.create(
                    "demandas",
                    {
                        **body,
                        "gabinete_id": current_user["gabinete_id"],
                        "origem_cadastro": body.get("origem_cadastro", "MOBILE_CAMPO"),
                        "status": body.get("status", "ABERTA"),
                        "prioridade": body.get("prioridade", "MEDIA"),
                        "data_abertura": iso_now(),
                    },
                )
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


@router.post("/ai/resumir-contexto")
def ai_summarize_context(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("contexto_tipo", "contexto_id"))
    contexto_tipo = payload["contexto_tipo"]
    contexto_id = payload["contexto_id"]
    if contexto_tipo == "demanda":
        demand = repo.get("demandas", contexto_id)
        if not demand:
            not_found("Demanda")
        resumo = f"Demanda {demand.get('status')} com prioridade {demand.get('prioridade')}: {demand.get('titulo')}."
    elif contexto_tipo in {"documento", "parecer"}:
        doc = repo.get("documentos", contexto_id)
        if not doc:
            not_found("Documento")
        resumo = f"Documento {doc.get('tipo')} em status {doc.get('status')}, versao {doc.get('versao_atual')}: {doc.get('titulo')}."
    else:
        resumo = "Contexto localizado para apoio operacional. Revise os dados antes de agir."
    return success(request, {"resumo": resumo})


@router.post("/ai/sugerir-proxima-etapa")
def ai_suggest_next_step(
    request: Request,
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: JsonStore = Depends(get_store),
):
    require_fields(payload, ("contexto_tipo", "contexto_id"))
    suggestion = "Revisar o historico, confirmar responsavel e registrar a proxima acao manualmente."
    justification = "A IA assistiva nao altera estado automaticamente; ela apenas organiza o proximo passo provavel."
    if payload["contexto_tipo"] == "demanda":
        demand = repo.get("demandas", payload["contexto_id"])
        if not demand:
            not_found("Demanda")
        if not demand.get("cidadao_id"):
            suggestion = "Regularizar o demandante antes de qualquer andamento."
            justification = "O fluxo do atendimento depende de um contato/cidadao cadastrado."
        elif not demand.get("responsavel_usuario_id"):
            suggestion = "Iniciar atendimento ou atribuir um colaborador responsavel."
            justification = "A demanda ja possui demandante, mas ainda nao tem responsavel interno."
        elif demand.get("status") in {"EM_TRIAGEM", "REABERTA"}:
            suggestion = "Mover para atendimento e registrar uma tarefa operacional."
            justification = "O status indica que a demanda precisa de andamento humano."
    return success(request, {"sugestao": suggestion, "justificativa": justification})
