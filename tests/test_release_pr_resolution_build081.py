from pathlib import Path


def test_resolver_exists_and_targets_build_branch() -> None:
    text = Path('scripts/release/Resolve-NrhisPullRequest.ps1').read_text(encoding='utf-8')
    assert 'gh pr list' in text
    assert 'feature/sprint2-build$BuildNumber' in text
    assert '--state all' in text
    assert 'No pull request found for branch' in text


def test_finish_lifecycle_rejects_placeholder_urls() -> None:
    text = Path('scripts/release/Finish-NrhisBuildLifecycle.ps1').read_text(encoding='utf-8')
    assert 'PASTE_ACTUAL_PR_URL_HERE' in text
    assert 'Resolve-NrhisPullRequest.ps1' in text
    assert 'Invalid pull-request URL' in text
