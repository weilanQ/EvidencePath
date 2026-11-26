#!/usr/bin/env python3
"""Regenerate current paper artifacts and verify the declared frozen-input scope.

Inputs are immutable. Outputs go only to a generated-results directory. Historical
workflows use separate output names and do not replace the current seven-policy figure.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def input_state(manifest):
    state={}
    for record in manifest["files"]:
        path=ROOT/record["path"]
        actual=sha256(path)
        if actual!=record["sha256"]:
            raise RuntimeError("Frozen input checksum mismatch: "+record["path"])
        state[record["path"]]=actual
    return state
def sanitize(text):
    return text.replace(str(ROOT),"<REPO_ROOT>").replace(ROOT.as_posix(),"<REPO_ROOT>")
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"code/results/generated")
    parser.add_argument("--with-live-baseline-shuffles",action="store_true",
                        help="Additionally rerun the historical 5,000-round CIViC shuffle and old baseline plots.")
    args=parser.parse_args()
    out=args.output.resolve()
    protected=[ROOT/"data",ROOT/"docs",ROOT/"code/src",ROOT/"code/results/reference"]
    if any(out==p or p in out.parents for p in protected):
        raise SystemExit("Output must not overwrite data, source, documentation or reference artifacts.")
    out.mkdir(parents=True,exist_ok=True)
    logs=out/"logs";logs.mkdir(exist_ok=True)
    config=json.loads((ROOT/"code/configs/frozen_analysis_v1.0.json").read_text())
    manifest=json.loads((ROOT/"code/configs/immutable_inputs_v1.0.json").read_text())
    before=input_state(manifest)
    env=dict(os.environ,PYTHONIOENCODING="utf-8",EVIDENCEPATH_RESULTS_DIR=str(out))
    stages=[]
    def run(name,command):
        started=time.monotonic()
        result=subprocess.run([sys.executable,*map(str,command)],cwd=ROOT,env=env,
                              capture_output=True,text=True,encoding="utf-8")
        (logs/(name+".log")).write_text(sanitize(result.stdout+result.stderr),encoding="utf-8")
        stages.append({"stage":name,"returncode":result.returncode,
                       "elapsed_seconds":round(time.monotonic()-started,3),
                       "log":(logs/(name+".log")).relative_to(out).as_posix()})
        if result.returncode:
            raise RuntimeError("Stage failed: "+name+"; see "+stages[-1]["log"])
    primary=out/"primary"
    run("current_tables_and_figure",[ROOT/"code/src/build_revision_tables.py",
        "--run",ROOT/config["paths"]["frozen_inputs"],"--out",primary])
    run("frozen_evidence_verification",[ROOT/"code/src/verify_evidence.py",
        "--run",ROOT/config["paths"]["frozen_inputs"],"--generated",primary,
        "--report",out/"verification_report.json"])
    for name in ["run_main_results.py","run_cluster_sensitivity.py",
                 "run_descriptor_sensitivity.py","run_parameter_grid.py"]:
        run("baseline_"+name.removesuffix(".py"),[ROOT/"code/src/baseline"/name])
    # Verify the rerun grid against the strong-baseline diagnostic archive.
    import pandas as pd
    grid=pd.read_csv(out/"baseline/tables/rrf_grid_scan_54_summary.csv")
    stored=pd.read_csv(ROOT/config["paths"]["frozen_inputs"]/"e6/parameter_grid_vs_strong_baselines.csv")
    max_grid_error=0.
    for row in stored.itertuples():
        match=grid[(grid.k==row.k)&((grid.alpha-row.alpha).abs()<1e-12)]
        assert len(match)==1
        prefix="new" if row.cohort=="Replay" else "jan"
        actual=float(match.iloc[0][prefix+"_query_mrr"])
        max_grid_error=max(max_grid_error,abs(actual-row.query_mrr))
        assert abs(actual-row.query_mrr)<1e-12
        assert int(match.iloc[0][prefix+"_hr5_hits"])==row.hr5_hits
    if args.with_live_baseline_shuffles:
        for name in ["run_civic_order_shuffle.py","plot_figures.py"]:
            run("optional_"+name.removesuffix(".py"),[ROOT/"code/src/baseline"/name])
    generated=pd.read_csv(primary/"audited_main_results.csv")
    for cohort,key in [("Replay","expected_replay_mrr"),("Development","expected_development_mrr")]:
        for method,value in config[key].items():
            actual=generated[(generated.cohort==cohort)&(generated.method==method)].iloc[0]
            assert abs(actual.query_mrr-value)<1e-12,(cohort,method)
    after=input_state(manifest)
    assert before==after
    report={"status":"passed","release_version":config["release_version"],
            "scope":config["scope"],
            "recomputed":["10 ranking policies per development/replay cohort",
                          "candidate coverage and normalized Borda",
                          "current seven-policy HR-at-K figure",
                          "historical interleaving ceilings and temporal/omission summaries",
                          "54-setting grid, checked against archived strong-baseline results"],
            "verified_from_saved_evidence":["32 bootstrap confidence intervals",
                "all saved component draws and query-weighted paired means",
                "12 permutation tail tests and Holm correction",
                "46 actual-input source-overlap classifications",
                "45 displacement identities",
                "historical development cluster and descriptor summaries"],
            "not_performed":["raw PrimeKG/CIViC feature extraction","model training",
                "new bootstrap or graph-shuffle random draws"],
            "optional_historical_civic_shuffles_rerun":args.with_live_baseline_shuffles,
            "immutable_inputs_checked":len(before),"immutable_inputs_unchanged":True,
            "max_rerun_grid_mrr_error":max_grid_error,"stages":stages,
            "outputs":{"primary":"primary/","baseline":"baseline/","verification":"verification_report.json"},
            "runtime_note":"Measured runtime is reported per stage, not guaranteed across hardware."}
    (out/"reproduction_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"passed","immutable_inputs":len(before),
                      "primary_outputs":len(list(primary.glob("*"))),
                      "report":sanitize(str(out/"reproduction_report.json"))},indent=2))
if __name__=="__main__":
    main()
