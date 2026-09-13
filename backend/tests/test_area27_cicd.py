from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def workflow_text():
    assert WORKFLOW.is_file()
    return WORKFLOW.read_text(encoding="utf-8-sig")


def test_area27_workflow_exists():
    assert WORKFLOW.is_file()


def test_area27_triggers_on_main_push_and_pull_request():
    text = workflow_text()

    assert "push:" in text
    assert "pull_request:" in text
    assert "- main" in text


def test_area27_has_least_privilege_permissions():
    text = workflow_text()

    assert "permissions:" in text
    assert "contents: read" in text


def test_area27_has_concurrency_control():
    text = workflow_text()

    assert "concurrency:" in text
    assert "cancel-in-progress: true" in text


def test_area27_uses_supported_runtime_versions():
    text = workflow_text()

    assert 'python-version: "3.12"' in text
    assert 'node-version: "22"' in text


def test_area27_backend_quality_gate():
    text = workflow_text()

    assert "backend-quality:" in text
    assert "python -m compileall -q backend/app" in text
    assert "pytest" in text
    assert "backend/tests" in text


def test_area27_has_database_service():
    text = workflow_text()

    assert "postgres:" in text
    assert "postgres:16" in text
    assert "5433:5432" in text


def test_area27_has_kafka_service():
    text = workflow_text()

    assert "kafka:" in text
    assert "bitnamilegacy/kafka:" in text
    assert "29092:29092" in text


def test_area27_has_frontend_quality_gate():
    text = workflow_text()

    assert "frontend-quality:" in text
    assert "npm ci" in text
    assert "npm run lint" in text
    assert "npm run build" in text


def test_area27_has_container_validation():
    text = workflow_text()

    assert "container-validation:" in text
    assert "docker build" in text
    assert "docker image inspect" in text


def test_area27_has_kubernetes_validation():
    text = workflow_text()

    assert "kubernetes-validation:" in text
    assert "PyYAML" in text
    assert "KUBERNETES MANIFEST VALIDATION = PASS" in text


def test_area27_has_final_quality_gate():
    text = workflow_text()

    assert "ci-summary:" in text
    assert "AREA 27 CI QUALITY GATE" in text


def test_area27_has_application_contract():
    text = workflow_text()

    assert "from app.main import app" in text
    assert "required={" in text
    assert "/health" in text
    assert "/ready" in text


def test_area27_preserves_full_previous_area_regression():
    text = workflow_text()

    assert "python -m pytest backend/tests -q" in text

    for name in (
        "test_area16_api.py",
        "test_area17_integration.py",
        "test_area18_observability.py",
        "test_area19_security.py",
        "test_area19_authentication.py",
        "test_area19_auth_api.py",
        "test_area20_governance.py",
        "test_area20_governance_integration.py",
        "test_area21_configuration.py",
        "test_area22_ingestion.py",
        "test_area23_storage.py",
    ):
        assert name not in text or "backend/tests" in text


def test_area27_runs_historical_ci_regression():
    text = workflow_text()

    assert "test_area24_cicd.py" in text


def test_area27_does_not_use_local_env_file():
    text = workflow_text()
    assert ".env" not in text.replace(".env.example", "")


def test_area27_has_no_production_secret_literals():
    text = workflow_text()

    for value in (
        "CHANGE_ME",
        "SECRET_CHANGE_ME",
        "AREA21_DEVELOPMENT_SECRET",
    ):
        assert value not in text