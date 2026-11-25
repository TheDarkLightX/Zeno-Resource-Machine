"""Rebuild the Zeno-ADP quotient cross-check vectors.

    python3 reference_models/zeno_adp_vectors/regenerate.py [--check]

Runs this directory's Rust program twice: once for its 120 seeded random tables,
and once on the transition tables of the two correct RFC-0001 commit-path
instances, which are sent on stdin and recorded only by SHA-256.  The program
depends on ``zeno-adp = "=0.8.0"`` from crates.io and needs network access to
fetch it.  If the repository's pinned toolchain is unavailable, set
``RUSTUP_TOOLCHAIN`` to an installed one; the outputs are integer tables.
``--check`` compares with the committed file instead of writing it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGET = HERE / "vectors_0_8_0.json"
sys.path.insert(0, str(ROOT))

from reference_models.bounded_explorer import table_line  # noqa: E402
from reference_models.rfc0001_commit_path_explorer import explore_instance, instance_name, instances  # noqa: E402


def model_lines() -> list[tuple[str, str, int]]:
    """Instance label, table line and state count for each correct instance."""

    out = []
    for second in instances():
        exploration = explore_instance(second)
        out.append((instance_name(second), table_line(exploration.next, exploration.codes),
                    len(exploration.states)))
    return out


def cargo(args: list[str], stdin: str | None = None) -> str:
    """Run the generator and return its standard output."""

    command = ["cargo", "run", "--quiet", "--release", "--locked", "--manifest-path", str(HERE / "Cargo.toml")]
    command += ["--", *args] if args else []
    return subprocess.run(command, input=stdin, capture_output=True, text=True, check=True).stdout


def build() -> str:
    """The vectors file text."""

    random_cases = json.loads(cargo([]))
    lines = model_lines()
    answers = json.loads(cargo(["--stdin"], "".join(line + "\n" for _, line, _ in lines)))
    models = [
        {"instance": name, "states": states, "table_sha256": hashlib.sha256(line.encode("ascii")).hexdigest(),
         "quotient": answer}
        for (name, line, states), answer in zip(lines, answers, strict=True)
    ]
    vectors = {"schema": random_cases["schema"], "zeno_adp": random_cases["zeno_adp"],
               "random": random_cases["random"], "models": models,
               "generator": "reference_models/zeno_adp_vectors (zeno-adp =0.8.0 from crates.io)"}
    return json.dumps(vectors, separators=(",", ":")) + "\n"


def main() -> int:
    """Write the vectors, or compare them with the committed file."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = build()
    if args.check:
        same = TARGET.read_text(encoding="utf-8") == text
        print("vectors match" if same else "vectors differ")
        return 0 if same else 1
    TARGET.write_text(text, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
