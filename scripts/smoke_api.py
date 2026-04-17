from __future__ import annotations

import sys
import os
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["GABINETE_IA_DB_FILE"] = str(ROOT / "data" / "smoke_gabinete_ia.json")

from apps.api.app.main import app


client = TestClient(app)


def main() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email_login": "chefe@gabineteia.local", "senha": "Senha@123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text

    contacts = client.get("/api/v1/contatos", headers=headers)
    assert contacts.status_code == 200, contacts.text
    contact_id = contacts.json()["data"][0]["id"]

    created = client.post(
        "/api/v1/demandas",
        headers=headers,
        json={
            "cidadao_id": contact_id,
            "titulo": "Smoke test demanda",
            "descricao": "Registro criado pelo smoke test.",
            "prioridade": "MEDIA",
            "origem_cadastro": "WEB_INTERNO",
        },
    )
    assert created.status_code == 201, created.text
    demand_id = created.json()["data"]["id"]

    history = client.get(f"/api/v1/demandas/{demand_id}/historico", headers=headers)
    assert history.status_code == 200, history.text

    dashboard = client.get("/api/v1/territorial/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text

    overview = client.get("/api/v1/political-os/overview", headers=headers)
    assert overview.status_code == 200, overview.text

    for path in ("/api/v1/interacoes", "/api/v1/proposicoes", "/api/v1/emendas", "/api/v1/oficios"):
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text

    print("smoke ok")


if __name__ == "__main__":
    main()
