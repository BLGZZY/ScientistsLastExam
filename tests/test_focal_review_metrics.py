"""PR74 review: claim-denominator FDR and fail-closed separation evidence."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    spec = importlib.util.spec_from_file_location("focal_review", ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode", ["claims", "abstain", "invalid", "mixed"])
def test_fdr_counts_valid_claims_across_both_world_kinds(mode):
    oracle = load("benchmarks/EarthScience/FocalMechanismStressInversion/verification/evaluator.py")
    baseline = load("benchmarks/EarthScience/FocalMechanismStressInversion/solution.py")
    calls = 0

    def candidate(problem, callback, budget):
        nonlocal calls
        calls += 1
        action = mode if mode != "mixed" else ("claims", "invalid", "abstain")[calls % 3]
        if action == "invalid":
            return {}
        if action == "abstain":
            return dict(sigma1=None, sigma3=None, R=None, plane_assignments=None,
                        abstain=True, confidence=0.)
        return baseline.infer_stress_orientation(problem, callback, budget)

    result = oracle.evaluate(candidate)
    for split, prefix, specs in [("development", "", oracle._BASE_DEVELOPMENT_SPECS),
                                  ("heldout", "heldout_", oracle.HELDOUT_SPECS)]:
        rows = [r for r in result["per_world"] if r["split"] == split]
        claims = sum(r["valid"] and not r["abstained"] for r in rows)
        false = sum(r["valid"] and not r["abstained"] and spec[1] != "supported"
                    for r, spec in zip(rows, specs))
        unsupported = sum(spec[1] != "supported" for spec in specs)
        assert result[prefix + "positive_claim_count"] == claims
        assert result[split + "_false_discovery_rate"] == (false / claims if claims else 0.)
        assert result[split + "_false_positive_rate"] == false / unsupported
        if mode == "claims":
            assert claims == len(specs)
            assert 0 < result[split + "_false_discovery_rate"] < 1
            assert result[split + "_false_positive_rate"] == 1
        if mode in ("invalid", "abstain"):
            assert claims == 0
            assert result["combined_score"] == 0
            assert all(r["valid"] == (mode == "abstain") for r in rows)


def report(reference=.9, probe=.5):
    return {"split": "development", "results": {
        "reference": {"configured_summary": {"normalized": reference}},
        "paired62208_refined": {"configured_summary": {"normalized": probe},
                                "threshold_sweep": {"25.0": {"normalized": probe}}}}}


def test_separation_preserves_strict_gates_and_score_ceiling():
    audit = load(".research/pr74_check_admission.py").audit
    assert audit([report()])["status"] == "separation_passed_not_certification"
    for ref, probe in [(1., .7751364580), (1., .75), (.5, .35), (.8, .6)]:
        assert audit([report(ref, probe)])["status"] == "BLOCKED"
    failure = audit([report(.7854573533, .7751364580)])["failures"][0]
    assert failure["impossible_at_score_ceiling"]
    assert failure["reference_required_above"] > 1


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 1.01, True])
def test_invalid_scores_cannot_pass(bad):
    audit = load(".research/pr74_check_admission.py").audit
    assert audit([report(reference=bad)])["status"] == "BLOCKED"
    assert audit([report(probe=bad)])["status"] == "BLOCKED"


def test_missing_strong_probe_and_sweeps_cannot_pass():
    audit = load(".research/pr74_check_admission.py").audit
    assert audit([])["status"] == "BLOCKED"
    missing = report()
    del missing["results"]["paired62208_refined"]
    assert audit([missing])["status"] == "BLOCKED"
    missing = report()
    missing["results"]["paired62208_refined"]["threshold_sweep"] = {}
    assert audit([missing])["status"] == "BLOCKED"
    fixed = report(probe=.8)
    fixed["results"]["paired62208_refined"]["threshold_sweep"]["25.0"]["normalized"] = .1
    assert audit([fixed])["status"] == "BLOCKED"
