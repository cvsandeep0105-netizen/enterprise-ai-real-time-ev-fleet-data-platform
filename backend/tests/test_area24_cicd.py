from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def workflow_text():
    assert WORKFLOW.is_file()
    return WORKFLOW.read_text(encoding="utf-8-sig")


def test_historical_ci_workflow_contract_exists():
    text = workflow_text()

    assert "EV Fleet Data Platform CI" in text
    assert "push:" in text
    assert "pull_request:" in text
    assert "main" in text
    assert "permissions:" in text
    assert "contents: read" in text


def test_historical_ci_preserves_application_compilation():
    text = workflow_text()
    assert "python -m compileall -q backend/app" in text


def test_historical_ci_preserves_application_contract():
    text = workflow_text()
    assert "from app.main import app" in text
    assert "MISSING ROUTES" in text


def test_historical_ci_preserves_regression_capability():
    text = workflow_text()

    assert "python -m pytest backend/tests -q" in text
    assert "backend/tests" in text


def test_historical_ci_uses_current_python_runtime():
    text = workflow_text()
    assert 'python-version: "3.12"' in text


def test_historical_ci_uses_backend_requirements():
    text = workflow_text()
    assert "pip install -r backend/requirements.txt" in text


def test_historical_ci_is_secret_safe():
    text = workflow_text()

    for value in (
        "CHANGE_ME",
        "SECRET_CHANGE_ME",
        "AREA21_DEVELOPMENT_SECRET",
    ):
        assert value not in text


def test_historical_ci_has_read_only_permissions():
    text = workflow_text()
    assert "permissions:" in text
    assert "contents: read" in text