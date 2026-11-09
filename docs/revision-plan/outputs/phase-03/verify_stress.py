"""Call original read-only verifier with an explicit historical path adapter."""
from pathlib import Path
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('historical_verifier',ROOT/'thucnghiem/results/verify_camera_ready_evidence.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# The original script's historical src/ path maps exactly to thucnghiem/.
# cwd remains inside the same repository for git show. No source edit or copy.
m.ROOT=OUT/'path-adapter';m.ROOT.mkdir(exist_ok=True)
link=m.ROOT/'src'
if not link.exists():link.symlink_to(ROOT/'thucnghiem',target_is_directory=True)
assert link.resolve()==(ROOT/'thucnghiem').resolve()
m.RESULTS=m.ROOT/'src/results'
# Original base check fails on missing final LF in one current CSV. Preserve that
# failure and prove exact record equality before replay, without repairing input.
import subprocess,csv,io,hashlib
p=m.RESULTS/'cij_baseline_benchmark_results/benchmark_test_40runs.csv'
current=p.read_bytes();historical=subprocess.check_output(['git','show',m.RQ1_SOURCE_COMMIT+':src/results/cij_baseline_benchmark_results/benchmark_test_40runs.csv'],cwd=ROOT)
assert current+b'\n'==historical
assert list(csv.DictReader(io.StringIO(current.decode())))==list(csv.DictReader(io.StringIO(historical.decode())))
m.verify_hash_manifest('rq2_results/rq2_artifact_sha256.json');m.verify_hash_manifest('rq3_results/rq3_artifact_sha256.json')
base={'rq1_test_rows':m.read_rows(p)}
assert len(base['rq1_test_rows'])==400 and len({r['run_id'] for r in base['rq1_test_rows']})==40
print('Original base byte equality FAILED: final LF absent; current CSV records equal historical records exactly. Independent stress replay follows, not full verifier PASS.',flush=True)
records=[]
for rel,executed in [('rq1_results',True),('rq1_results_v2/full',False)]:
 d=m.verify_rq1_stress_artifact(base,m.RESULTS/rel,require_executed_notebook=executed);d={k:v for k,v in d.items() if k not in {'per_run_rows'}};records.append(d);print('verified',rel,{k:d[k] for k in ['manifest_files','checkpoints','paired_effect_rows','audit_numpy']},flush=True)
(OUT/'stress-verification.json').write_text(json.dumps({'adapter':'path-adapter/src -> repository/thucnghiem; historical git src paths unchanged','checks':records,'scope':'original verifier base and primary/replication stress, including checkpoints/mapping/bootstrap; no manuscript/full-run claim'},indent=2)+'\n')
