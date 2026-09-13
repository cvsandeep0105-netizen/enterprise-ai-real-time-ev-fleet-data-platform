from pathlib import Path
import yaml

p = Path(".github/workflows/cd.yml")
data = yaml.safe_load(p.read_text(encoding="utf-8"))
jobs = data["jobs"]
deploy = jobs["deploy"]

assert deploy["if"] == "${{ github.event.workflow_run.conclusion == 'success' && vars.PRODUCTION_DEPLOY_ENABLED == 'true' }}"
assert deploy["environment"]["name"] == "production"

text = p.read_text(encoding="utf-8")
for required in [
    "workflow_run",
    "KUBE_CONFIG_B64",
    "set image deployment/evfleet-backend",
    "set image deployment/evfleet-frontend",
    "rollout status deployment/evfleet-backend",
    "rollout status deployment/evfleet-frontend",
    "Production smoke test",
    "Automatic rollback",
    "rollout undo deployment/evfleet-backend",
    "rollout undo deployment/evfleet-frontend",
    "head_sha",
]:
    assert required in text, f"Missing CD requirement: {required}"

print("CD WORKFLOW STRUCTURE: PASS")
