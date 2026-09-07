"""Published 1989 code replication plus a free-suffix product, without search.

The n=6,7,8 packed data were extracted from Andreas Florath's BSD-3-Clause
Lean transcription. See ../references/reference_sources.json and license file.
The original codes are due to van Laarhoven, Aarts, van Lint and Wille (1989).
For n=9,10 the n=8 code is extended by all suffixes; these are not record claims.
This is a contamination/replication probe, NOT a truth-blind search reference.
Run: python verification/reference_reconstruction.py 8
"""
from pathlib import Path
import argparse
import itertools
import json


def build_covering(n: int):
    if n not in range(6, 11):
        raise ValueError("unsupported covering length")
    data = json.loads((Path(__file__).parent / "data" / "van_laarhoven_packed.json").read_text())
    k = min(n, 8)
    code = [[(value // (3 ** i)) % 3 for i in range(k)] for value in data[str(k)]]
    return [word + list(suffix) for word in code
            for suffix in itertools.product(range(3), repeat=n - k)]


def export_source():
    """Single-file public-data candidate suitable for the isolated RPC worker."""
    data = json.loads((Path(__file__).parent / "data/van_laarhoven_packed.json").read_text())
    license_text = (Path(__file__).resolve().parents[1] / "references/CoveringCodes-LICENSE.txt").read_text()
    notice = "# van Laarhoven et al. (1989), Florath Lean transcription. Public-data reconstruction.\n"
    notice += "".join("# " + line + "\n" for line in license_text.splitlines())
    return (notice + "import itertools\nDATA = " + repr(data)
            + "\n\ndef build_covering(n):\n"
              "    if n not in range(6, 11):\n        raise ValueError('unsupported covering length')\n"
              "    k = min(n, 8)\n"
              "    code = [[(v // 3**i) % 3 for i in range(k)] for v in DATA[str(k)]]\n"
              "    return [w + list(s) for w in code for s in itertools.product(range(3), repeat=n-k)]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", nargs="?", type=int)
    parser.add_argument("--export", type=Path, help="write a self-contained reference candidate")
    args = parser.parse_args()
    if (args.n is None) == (args.export is None):
        parser.error("give n or --export PATH, exclusively")
    if args.export is not None:
        args.export.write_text(export_source(), encoding="utf-8")
    else:
        print(json.dumps(build_covering(args.n)))
