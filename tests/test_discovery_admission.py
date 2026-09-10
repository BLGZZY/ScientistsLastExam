"""Discovery admission must not promote a public-score Δ to measures_iteration."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "report_discovery_admission.py"
    spec = importlib.util.spec_from_file_location("discovery_admission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DiscoveryAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_optimization_row_is_unchanged(self):
        row = {"task": "Chemistry/LennardJonesCluster", "verdict": "measures_iteration"}
        out = self.mod.classify_discovery_row(row, "optimization")
        self.assertEqual(out["verdict"], "measures_iteration")
        self.assertNotIn("iteration_claim", out)

    def test_discovery_measures_iteration_is_stripped(self):
        row = {"task": "Mathematics/SequenceLawRecovery", "verdict": "measures_iteration"}
        out = self.mod.classify_discovery_row(row, "discovery")
        self.assertEqual(out["public_score_verdict"], "measures_iteration")
        self.assertEqual(out["verdict"], "discovery_public_score_only")
        self.assertIn("not_from_combined_score", out["iteration_claim"])

    def test_discovery_ceiling_does_not_claim_mechanism_solved(self):
        row = {"task": "Mathematics/SequenceLawRecovery", "verdict": "solved_at_ceiling"}
        out = self.mod.classify_discovery_row(row, "discovery")
        self.assertEqual(out["verdict"], "public_score_at_ceiling")
        self.assertIn("mechanism", out["iteration_claim"])

    def test_absent_axis_input_is_explicitly_reported_missing(self):
        row = {"task": "X/Y", "verdict": "exhausted_unpaired"}
        out = self.mod.classify_discovery_row(row, "discovery")
        self.assertEqual(out["missing_axes"], ["mechanism", "fdr", "refusal"])
        self.assertEqual(out["count_without_denominator"], [])

    def test_count_without_denominator_is_surfaced_not_imputed(self):
        axes = {
            "mechanism": {"value": 0.5, "key": "mechanism_score"},
            "fdr": {"value": None, "key": "development_false_discoveries",
                    "status": "count_without_denominator"},
            "refusal": {"value": 1.0, "key": "correct_refusal_rate"},
        }
        row = {"task": "X/Y", "verdict": "exhausted_unpaired"}
        out = self.mod.classify_discovery_row(row, "discovery", axes)
        self.assertEqual(out["count_without_denominator"], ["fdr"])
        self.assertEqual(out["missing_axes"], [])

    def test_mechanism_on_another_split_is_not_reported_missing(self):
        axes = {
            "mechanism": {
                "value": None, "key": "mechanism_score", "split": "unsplit",
                "requested_split": "heldout", "status": "published_on_other_split",
            },
            "fdr": {"value": 0.1, "key": "development_false_discovery_rate"},
            "refusal": {"value": 1.0, "key": "correct_refusal_rate"},
        }
        row = {"task": "X/Y", "verdict": "exhausted_unpaired"}
        out = self.mod.classify_discovery_row(row, "discovery", axes)
        self.assertEqual(out["published_on_other_split"], ["mechanism"])
        self.assertEqual(out["missing_axes"], [])

    def test_triple_axes_join_only_to_the_same_full_run_identity(self):
        axes = {
            "mechanism": {"value": 0.5, "key": "mechanism_score"},
            "fdr": {"value": 0.1, "key": "false_discovery_rate"},
            "refusal": {"value": 0.8, "key": "correct_refusal_rate"},
        }
        triple = {"rows": [{
            "task": "Mathematics/SequenceLawRecovery",
            "model": "hy3-ioa",
            "llm_condition_sha256": "condition-a",
            "task_version": "task-v1",
            "runtime_source_sha256": "runtime-a",
            "status": "ok",
            "axes": axes,
        }]}
        admission = {"rows": [
            {
                "task": "Mathematics/SequenceLawRecovery",
                "model": "hy3-ioa",
                "llm_condition_sha256": "condition-a",
                "task_version": "task-v1",
                "runtime_source_sha256": "runtime-a",
                "verdict": "measures_iteration",
            },
            {
                "task": "Mathematics/SequenceLawRecovery",
                "model": "hy3-ioa",
                "llm_condition_sha256": "condition-b",
                "task_version": "task-v2",
                "runtime_source_sha256": "runtime-b",
                "verdict": "measures_iteration",
            },
        ]}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            admission_path = root / "admission.json"
            triple_path = root / "triple.json"
            output_path = root / "out.json"
            admission_path.write_text(json.dumps(admission), encoding="utf-8")
            triple_path.write_text(json.dumps(triple), encoding="utf-8")
            self.mod.main([
                "--admission", str(admission_path),
                "--triple", str(triple_path),
                "--output", str(output_path),
            ])
            rows = json.loads(output_path.read_text(encoding="utf-8"))["rows"]
        self.assertEqual(rows[0]["axes"], axes)
        self.assertEqual(rows[0]["missing_axes"], [])
        self.assertEqual(rows[0]["axes_join"], "exact")
        self.assertEqual(rows[1]["missing_axes"], ["mechanism", "fdr", "refusal"])
        self.assertEqual(rows[1]["axes_join"], "no_match")

    def _identity(self, **extra):
        row = {
            "task": "Mathematics/SequenceLawRecovery",
            "model": "hy3-ioa",
            "llm_condition_sha256": "condition-a",
            "task_version": "task-v1",
            "runtime_source_sha256": "runtime-a",
        }
        row.update(extra)
        return row

    def test_multi_seed_triple_joins_when_admission_names_seed_and_mode(self):
        axes0 = {
            "mechanism": {"value": 0.4, "key": "heldout_mechanism_score", "split": "heldout"},
            "fdr": {"value": 0.1, "key": "heldout_false_discovery_rate", "split": "heldout"},
            "refusal": {"value": 0.8, "key": "heldout_unsupported_refusal_rate", "split": "heldout"},
        }
        axes1 = {
            "mechanism": {"value": 0.6, "key": "heldout_mechanism_score", "split": "heldout"},
            "fdr": {"value": 0.2, "key": "heldout_false_discovery_rate", "split": "heldout"},
            "refusal": {"value": 0.7, "key": "heldout_unsupported_refusal_rate", "split": "heldout"},
        }
        triple = {"schema_version": 2, "rows": [
            {**self._identity(seed=0, feedback_mode="normal", status="ok", axes=axes0)},
            {**self._identity(seed=1, feedback_mode="normal", status="ok", axes=axes1)},
        ]}
        admission = {"rows": [
            {**self._identity(seed=0, feedback_mode="normal", verdict="measures_iteration")},
            {**self._identity(seed=1, feedback_mode="normal", verdict="measures_iteration")},
        ]}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            admission_path = root / "admission.json"
            triple_path = root / "triple.json"
            output_path = root / "out.json"
            admission_path.write_text(json.dumps(admission), encoding="utf-8")
            triple_path.write_text(json.dumps(triple), encoding="utf-8")
            self.mod.main([
                "--admission", str(admission_path),
                "--triple", str(triple_path),
                "--output", str(output_path),
            ])
            document = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 2)
        self.assertEqual(document["rows"][0]["axes"], axes0)
        self.assertEqual(document["rows"][1]["axes"], axes1)
        self.assertEqual(document["rows"][0]["missing_axes"], [])
        self.assertEqual(document["rows"][1]["missing_axes"], [])
        self.assertEqual(document["rows"][0]["axes_join"], "exact")

    def test_multi_seed_triple_does_not_claim_axes_unpublished(self):
        axes = {
            "mechanism": {"value": 0.5, "key": "heldout_mechanism_score"},
            "fdr": {"value": 0.1, "key": "heldout_false_discovery_rate"},
            "refusal": {"value": 0.8, "key": "heldout_unsupported_refusal_rate"},
        }
        triple = {"schema_version": 2, "rows": [
            {**self._identity(seed=0, feedback_mode="normal", status="ok", axes=axes)},
            {**self._identity(seed=1, feedback_mode="normal", status="ok", axes=axes)},
        ]}
        admission = {"rows": [
            {**self._identity(verdict="measures_iteration")},
        ]}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            admission_path = root / "admission.json"
            triple_path = root / "triple.json"
            output_path = root / "out.json"
            admission_path.write_text(json.dumps(admission), encoding="utf-8")
            triple_path.write_text(json.dumps(triple), encoding="utf-8")
            self.mod.main([
                "--admission", str(admission_path),
                "--triple", str(triple_path),
                "--output", str(output_path),
            ])
            row = json.loads(output_path.read_text(encoding="utf-8"))["rows"][0]
        self.assertEqual(row["axes_join"], "ambiguous_multi_run")
        self.assertEqual(row["missing_axes"], [])
        self.assertIn("seed and feedback_mode", row["axes_join_reason"])

    def test_admission_chains_a_written_two_seed_triple_report(self):
        import contextlib
        import io
        from unittest import mock

        triple_mod_path = Path(__file__).resolve().parents[1] / "scripts" / "report_discovery_triple.py"
        spec = importlib.util.spec_from_file_location("discovery_triple", triple_mod_path)
        triple_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(triple_mod)

        def write_run(directory: Path, seed: int) -> None:
            directory.mkdir(parents=True)
            (directory / "run_manifest.json").write_text(json.dumps({
                "task_id": "Mathematics/SequenceLawRecovery",
                "feedback_mode": "normal",
                "seed": seed,
                "llm_condition": {"model": "hy3-ioa"},
                "llm_condition_sha256": "condition-a",
                "task_package_sha256": "task-package",
                "runtime_source_sha256": "runtime-a",
            }), encoding="utf-8")
            (directory / "trajectory.jsonl").write_text(
                json.dumps({"step": 0, "valid": True, "score": 0.0}) + "\n"
                + json.dumps({
                    "step": 1,
                    "valid": True,
                    "score": 0.5,
                    "metrics": {
                        "combined_score": 0.5,
                        "heldout_mechanism_score": 0.4 + 0.1 * seed,
                        "heldout_false_discovery_rate": 0.1,
                        "heldout_unsupported_refusal_rate": 0.8,
                        "heldout_discovery_coverage": 0.7,
                    },
                }) + "\n",
                encoding="utf-8",
            )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for seed in (0, 1):
                write_run(root / "runs" / str(seed), seed)
            triple_path = root / "triple.json"
            with mock.patch.object(
                triple_mod, "discovery_task_names",
                return_value={"SequenceLawRecovery"},
            ), contextlib.redirect_stdout(io.StringIO()):
                triple_mod.main(["--runs", str(root / "runs"), "--output", str(triple_path)])
            triple_rows = [
                row for row in json.loads(triple_path.read_text(encoding="utf-8"))["rows"]
                if row.get("status") == "ok"
            ]
            self.assertEqual(len(triple_rows), 2)
            admission = {"rows": [
                {
                    "task": row["task"],
                    "model": row["model"],
                    "llm_condition_sha256": row["llm_condition_sha256"],
                    "task_version": row["task_version"],
                    "runtime_source_sha256": row["runtime_source_sha256"],
                    "seed": row["seed"],
                    "feedback_mode": row["feedback_mode"],
                    "verdict": "measures_iteration",
                }
                for row in triple_rows
            ]}
            admission_path = root / "admission.json"
            output_path = root / "out.json"
            admission_path.write_text(json.dumps(admission), encoding="utf-8")
            self.mod.main([
                "--admission", str(admission_path),
                "--triple", str(triple_path),
                "--output", str(output_path),
            ])
            joined = json.loads(output_path.read_text(encoding="utf-8"))["rows"]
        self.assertEqual(len(joined), 2)
        self.assertEqual({row["seed"] for row in joined}, {0, 1})
        for row in joined:
            self.assertEqual(row["axes_join"], "exact")
            self.assertEqual(row["missing_axes"], [])
            self.assertEqual(row["axes"]["mechanism"]["status"], "semantics_unrecorded")
            self.assertNotIn("mechanism", row["published_on_other_split"])


if __name__ == "__main__":
    unittest.main()
