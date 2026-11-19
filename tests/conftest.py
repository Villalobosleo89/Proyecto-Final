import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import Especialidad, Medico, DispositivoWearable, Usuario
from app.core.security import get_password_hash

# SQLite en memoria compartida para toda la sesión de pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    
    # 1. Catálogo de especialidades
    for esp in ["Cardiologia", "Neurologia", "Neumologia", "Cirugia general", "Medicina interna", "Gastroenterologia", "Pediatria", "Medicina general"]:
        session.add(Especialidad(nombre=esp, activa=True))
    session.commit()

    # 2. Médico y Dispositivo
    cardio = session.query(Especialidad).filter(Especialidad.nombre == "Cardiologia").first()
    medico = Medico(
        nombre_completo="Dr. Prueba",
        correo="dr.prueba@umb.edu.co",
        id_especialidad=cardio.id_especialidad,
        activo=True
    )
    session.add(medico)
    session.commit()

    session.add(DispositivoWearable(
        id_medico=medico.id_medico,
        sistema_operativo="WearOS",
        fcm_token="token_test_wearos"
    ))
    session.commit()

    # 3. Usuarios de prueba
    admin_user = Usuario(
        nombre_usuario="admin_test",
        contrasena_hash=get_password_hash("pass123"),
        rol="admin",
        activo=True
    )
    medico_user = Usuario(
        nombre_usuario="medico_test",
        contrasena_hash=get_password_hash("pass123"),
        rol="medico",
        id_medico=medico.id_medico,
        activo=True
    )
    session.add_all([admin_user, medico_user])
    session.commit()
    session.close()

    yield

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={"usuario": "admin_test", "contrasena": "pass123"})
    assert res.status_code == 200
    return res.json()["access_token"]

@pytest.fixture
def medico_token(client):
    res = client.post("/api/v1/auth/login", json={"usuario": "medico_test", "contrasena": "pass123"})
    assert res.status_code == 200
    return res.json()["access_token"]
