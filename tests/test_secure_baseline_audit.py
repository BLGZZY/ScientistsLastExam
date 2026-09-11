from scripts.run_secure_baseline import INVALID_SCORE, _infrastructure_failure


def test_explicit_infrastructure_error_cannot_pass_as_candidate_rejection():
    assert _infrastructure_failure({
        "combined_score": INVALID_SCORE, "valid": 0.0,
        "infrastructure_failure": 1.0, "error_message": "sandbox unavailable",
    })
    assert _infrastructure_failure({"combined_score": INVALID_SCORE})
    assert not _infrastructure_failure({
        "combined_score": INVALID_SCORE, "valid": 0.0,
        "error_message": "candidate timeout", "candidate_failure_kind": "candidate_timeout",
    })
    assert not _infrastructure_failure({"combined_score": 0.0, "valid": 1.0})
