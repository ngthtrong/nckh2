#!/usr/bin/env bash
set -euo pipefail

repro_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repro_profile="full"
repro_report=""

usage() {
  cat <<'EOF'
Usage: ./reproduce.sh [--profile full|smoke] [--report PATH]

full  creates a fresh CPython 3.12 environment, installs requirements.lock,
      runs the complete test suite, verifies the locked artifact package, and
      rebuilds and audits the manuscript. This is the submission profile.

smoke reuses .venv when available and runs the focused Gate-4 tests before the
      same artifact/manuscript verification. It is for quick local diagnosis.

--report writes the verifier's final machine-readable JSON report. Existing
         files are not overwritten.
EOF
}

while (($#)); do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      repro_profile="$2"
      shift 2
      ;;
    --report)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      repro_report="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$repro_profile" != "full" && "$repro_profile" != "smoke" ]]; then
  printf 'Unsupported profile: %s\n' "$repro_profile" >&2
  exit 2
fi
if [[ -n "$repro_report" && -e "$repro_report" ]]; then
  printf 'Refusing to replace existing report: %s\n' "$repro_report" >&2
  exit 2
fi

for repro_command in python3.12 xelatex bibtex; do
  command -v "$repro_command" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$repro_command" >&2
    exit 2
  }
done

repro_temp_root="$(mktemp -d "${TMPDIR:-/tmp}/nckh2-reproduce.XXXXXX")"
cleanup() {
  local candidate="${repro_temp_root:-}"
  if [[ -n "$candidate" && -d "$candidate" ]]; then
    case "$candidate" in
      "${TMPDIR:-/tmp}"/nckh2-reproduce.*)
        rm -rf -- "$candidate"
        ;;
      *)
        printf 'Refusing to remove unexpected temporary path: %s\n' \
          "$candidate" >&2
        ;;
    esac
  fi
}
trap cleanup EXIT

cd "$repro_root"
export PYTHONDONTWRITEBYTECODE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export SOURCE_DATE_EPOCH=1785275159
export TZ=UTC

if [[ "$repro_profile" == "full" ]]; then
  python3.12 -m venv "$repro_temp_root/venv"
  repro_python="$repro_temp_root/venv/bin/python"
  "$repro_python" -m pip install --no-input -r requirements.lock
else
  if [[ -x "$repro_root/.venv/bin/python" ]]; then
    repro_python="$repro_root/.venv/bin/python"
  else
    repro_python="$(command -v python3.12)"
  fi
fi

"$repro_python" -m demo.experiments.package_locked_artifacts \
  --verify \
  --materialize-root "$repro_root"

if [[ "$repro_profile" == "full" ]]; then
  "$repro_python" -m pytest -q
else
  "$repro_python" -m pytest -q \
    demo/tests/test_artifact_package.py \
    demo/tests/test_locked_submission.py \
    demo/tests/test_result_promotion.py \
    demo/tests/test_verify_figures.py
fi

"$repro_python" -m demo.verify_figures
"$repro_python" -m demo.experiments.verify_locked_submission \
  --repository-root "$repro_root" \
  --policy revision/submission-policy.json \
  --phase pre \
  --artifact-package revision/locked-artifacts.tar.gz \
  --artifact-manifest revision/artifact-package-manifest.json

(
  cd "$repro_root/paper"
  xelatex -interaction=nonstopmode -halt-on-error main.tex
  bibtex main
  xelatex -interaction=nonstopmode -halt-on-error main.tex
  xelatex -interaction=nonstopmode -halt-on-error main.tex
)

repro_post_args=(
  --repository-root "$repro_root"
  --policy revision/submission-policy.json
  --phase post
  --artifact-package revision/locked-artifacts.tar.gz
  --artifact-manifest revision/artifact-package-manifest.json
)
if [[ -n "$repro_report" ]]; then
  repro_post_args+=(--report "$repro_report")
fi
"$repro_python" -m demo.experiments.verify_locked_submission \
  "${repro_post_args[@]}"

printf 'PASS: %s reproduction completed without re-executing X0.\n' \
  "$repro_profile"
