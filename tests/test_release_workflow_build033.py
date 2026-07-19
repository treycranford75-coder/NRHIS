from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_stage_helper_uses_dynamic_manifest() -> None:
    text = read("scripts/release/Stage-NrhisBuildPayload.ps1")
    assert "Get-NrhisBuildPayloadFiles.ps1" in text
    assert "RequiredFiles" in text
    assert "Test-NrhisBuildChangeSet.ps1" in text


def test_stage_helper_includes_required_files() -> None:
    text = read("scripts/release/Stage-NrhisBuildPayload.ps1")
    assert "$normalized -notin $expectedFiles" in text
    assert "$expectedFiles += $normalized" in text


def test_payload_consistency_uses_sha256() -> None:
    text = read("scripts/release/Test-NrhisPayloadConsistency.ps1")
    assert "Get-FileHash" in text
    assert "SHA256" in text
    assert "Payload mismatch" in text


def test_build_validation_checks_payload_before_ci() -> None:
    text = read("scripts/release/Invoke-NrhisBuildValidation.ps1")
    consistency_index = text.index("Test-NrhisPayloadConsistency.ps1")
    ci_index = text.index("Invoke-NrhisCiParity.ps1")
    assert consistency_index < ci_index


def test_build033_documents_permanent_starter_staging() -> None:
    text = read("docs/Release/Sprint2_Build033_PR.md")
    assert "Start-NrhisBuild.ps1" in text
    assert "automatically staged" in text
