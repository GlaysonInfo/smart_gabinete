from __future__ import annotations

import os
from pathlib import Path


class Settings:
    app_name = "GABINETE IA"
    api_prefix = "/api/v1"
    root_dir = Path(__file__).resolve().parents[3]
    data_dir = Path(os.getenv("GABINETE_IA_DATA_DIR", root_dir / "data"))
    db_file = Path(os.getenv("GABINETE_IA_DB_FILE", data_dir / "gabinete_ia.json"))
    upload_dir = Path(os.getenv("GABINETE_IA_UPLOAD_DIR", data_dir / "uploads"))
    jwt_secret = os.getenv("GABINETE_IA_JWT_SECRET", "dev-change-me")
    jwt_algorithm = "HS256"
    access_token_minutes = int(os.getenv("GABINETE_IA_ACCESS_MINUTES", "60"))
    refresh_token_days = int(os.getenv("GABINETE_IA_REFRESH_DAYS", "7"))
    password_pepper = os.getenv("GABINETE_IA_PASSWORD_PEPPER", "gabinete-ia-dev")
    sla_critical_hours = int(os.getenv("GABINETE_IA_SLA_CRITICA_HOURS", "4"))
    sla_high_hours = int(os.getenv("GABINETE_IA_SLA_ALTA_HOURS", "24"))
    sla_medium_hours = int(os.getenv("GABINETE_IA_SLA_MEDIA_HOURS", "72"))
    sla_low_hours = int(os.getenv("GABINETE_IA_SLA_BAIXA_HOURS", "120"))
    sla_warning_ratio = float(os.getenv("GABINETE_IA_SLA_WARNING_RATIO", "0.75"))


settings = Settings()

