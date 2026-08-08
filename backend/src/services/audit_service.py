"""后台审计日志服务."""

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def log_audit(
    db: Session,
    actor_id: int,
    action: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    ip: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=ip,
        )
    )
    db.commit()
