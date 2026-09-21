"""Shared fixtures: an isolated in-memory DB per test, plus a seed parent/child.

None of this touches app.db -- every test gets its own fresh SQLite database,
and the app's startup event (which would create_all against the real
DATABASE_URL) is never triggered because we don't use TestClient as a context
manager.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from main import app, get_current_parent, get_session
from models import Child, Parent


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="anon_client")
def anon_client_fixture(session):
    """Real auth: no login bypass. Use this to test signup/login/401s."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(session, anon_client):
    """Acts as the logged-in parent (the first Parent row), so feature tests
    don't each have to sign up and log in first."""

    def current_parent_override():
        return session.exec(select(Parent)).first()

    app.dependency_overrides[get_current_parent] = current_parent_override
    yield anon_client


@pytest.fixture
def parent_and_child(session):
    """One parent + one child, mirroring seed.py's dev seed data."""
    parent = Parent(name="Sam Parent", email="parent@example.com")
    session.add(parent)
    session.commit()
    session.refresh(parent)

    child = Child(name="Alex", parent_id=parent.id)
    session.add(child)
    session.commit()
    session.refresh(child)

    return parent, child
