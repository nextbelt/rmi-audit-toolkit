"""Convenience wrappers for writing AuditLog rows."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models_extra import AuditLog

logger = logging.getLogger(__name__)


def record(
    db: Session,
    *,
    action: str,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[Any] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert an audit row. Failures are logged but never raised — the audit
    path must not break the business action it's logging."""
    try:
        entry = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            target_type=target_type,
            target_id=None if target_id is None else str(target_id),
            ip_address=ip_address,
            details=json.dumps(details) if details else None,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:  # pragma: no cover - belt-and-braces
        db.rollback()
        logger.warning("Failed to write audit entry %s: %s", action, exc)
