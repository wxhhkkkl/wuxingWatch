"""T008 — SQLAlchemy model creation and relationships."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from models.bazi_chart import BaziChart
from models.user import User


def test_create_user(db_session):
    u = User(phone="13800138000")
    db_session.add(u)
    db_session.commit()
    assert u.id is not None
    assert u.phone == "13800138000"
    assert u.created_at is not None


def test_phone_is_unique(db_session):
    db_session.add(User(phone="13800138000"))
    db_session.commit()
    db_session.add(User(phone="13800138000"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_chart_with_user(db_session):
    u = User(phone="13800138000")
    db_session.add(u)
    db_session.flush()
    chart = BaziChart(
        user_id=u.id,
        relationship_type="CHILD",
        birth_solar=datetime(1990, 5, 20, 10, 30, tzinfo=UTC),
        chart_result="{}",
    )
    db_session.add(chart)
    db_session.commit()
    assert chart.id is not None
    assert chart.relationship_type == "CHILD"
    # cascade: deleting user removes their charts
    db_session.delete(u)
    db_session.commit()
    assert db_session.get(BaziChart, chart.id) is None


def test_chart_default_relationship_self(db_session):
    u = User(phone="13800138000")
    db_session.add(u)
    db_session.flush()
    chart = BaziChart(
        user_id=u.id,
        birth_solar=datetime(1990, 5, 20, 10, 30, tzinfo=UTC),
        chart_result="{}",
    )
    db_session.add(chart)
    db_session.commit()
    assert chart.relationship_type == "SELF"
