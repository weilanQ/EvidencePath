"""Verify archived diagnostic evidence without raw KG, model training, or network access."""
import argparse,json,math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import numpy as np
import pandas as pd

PACKAGE=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--run',type=Path,default=PACKAGE/'data/processed/frozen_analysis')
p.add_argument('--generated',type=Path,default=PACKAGE/'code/results/generated/primary')
p.add_argument('--report',type=Path,default=PACKAGE/'code/results/generated/verification_report.json')
a=p.parse_args();run=a.run.resolve();gen=a.generated.resolve()
def read(rel):return pd.read_csv(run/rel)
checks={}
ci=read('e1/bootstrap_confidence_intervals.csv');boot=read('e1/bootstrap_replicates.csv')
metric_column={'rr':'delta_mrr','hit1':'delta_hit1','hit3':'delta_hit3','hit5':'delta_hit5'}
max_ci_error=0.
for r in ci.itertuples():
    values=boot[(boot.criterion==r.criterion)&(boot.comparison==r.comparison)][metric_column[r.metric]].to_numpy()
    assert len(values)==10000
    lo,hi=np.quantile(values,[.025,.975],method='linear')
    max_ci_error=max(max_ci_error,abs(lo-r.ci_lower_95),abs(hi-r.ci_upper_95))
assert max_ci_error<1e-12
checks['all_32_bootstrap_intervals_recomputed_from_10000_archived_replicates']=True

labels=read('e0/frozen_analysis_bundle/replay_labels.csv')
candidates=read('e0/frozen_analysis_bundle/replay_candidates.csv')
membership=read('e1/cluster_memberships.csv')
query_rows=read('e0/replay_query_metrics.csv')
shared=read('e2/replay_shared_first_rankings.csv')
qorder=sorted(labels.qid.unique())
query_rr=query_rows.pivot(index='qid',columns='method',values='rr').loc[qorder]
shared_rank=shared.set_index(['qid','drug_norm']).shared_first_rank.to_dict()
shared_rr={}
for q,g in labels.groupby('qid'):
    ranks=[shared_rank.get((q,d),np.inf) for d in g.positive_drug]
    rank=min(ranks);shared_rr[q]=1/rank if np.isfinite(rank) else 0.
query_rr['SharedFirstContext']=[shared_rr[q] for q in qorder]
# Reconstruct every saved mean from the saved component draws. This verifies
# query weighting; it does not generate new bootstrap randomness.
query_metrics={'rr':query_rr}
for metric,k in [('hit1',1),('hit3',3),('hit5',5)]:
    values=query_rows.pivot(index='qid',columns='method',values=metric).loc[qorder]
    values['SharedFirstContext']=[int(shared_rr[q]>=1/k) for q in qorder]
    query_metrics[metric]=values
max_draw_error=0.
for criterion in ['drug','source']:
    grouped=membership[membership.criterion==criterion].groupby('component_id').qid.apply(list).to_dict()
    draws=np.load(run/f'e1/{criterion}_bootstrap_draws.npz',allow_pickle=False)['draws']
    assert draws.shape[0]==10000
    component_count=max(int(cid) for cid in grouped)+1
    counts=np.zeros(component_count,dtype=int)
    for cid,queries in grouped.items():counts[int(cid)]=len(queries)
    denominators=counts[draws].sum(axis=1)
    for A,B in [('RRF','Context'),('RRF','CIViC'),('SharedFirstContext','Context'),('RRF','SharedFirstContext')]:
        saved=boot[(boot.criterion==criterion)&(boot.comparison==A+' - '+B)].sort_values('round')
        assert np.array_equal(saved.query_denominator.to_numpy(),denominators)
        for metric,values in query_metrics.items():
            totals=np.zeros(component_count)
            for cid,queries in grouped.items():totals[int(cid)]=(values.loc[queries,A]-values.loc[queries,B]).sum()
            expected=totals[draws].sum(axis=1)/denominators
            error=float(np.max(np.abs(expected-saved[metric_column[metric]].to_numpy())))
            max_draw_error=max(max_draw_error,error)
            assert error<1e-12
checks['all_80000_saved_cluster_means_verify_query_weighting_for_four_metrics']=True

permutation=read('e3/permutation_tail_tests.csv');clinical=read('archived_inputs/diagnostics/civic_shuffle_round_metrics.csv')
recomputed=[];max_permutation_error=0.
for r in permutation.itertuples():
    n=45 if r.cohort=='Replay' else 41
    if r.shuffled_branch=='Graph':
        rounds=read(f'e3/{r.cohort.lower()}_graph_shuffle_round_metrics.csv')
    else:
        rounds=clinical[clinical.evaluation_group.str.contains('Quarterly' if r.cohort=='Replay' else 'January')]
    col={'MRR':'query_mrr','HR@3':'hr3_hits','HR@5':'hr5_hits'}[r.metric]
    divisor=1 if r.metric=='MRR' else n
    raw=rounds[col].to_numpy();values=raw/divisor
    observed=r.original*divisor
    count=int((raw>=observed-(1e-12 if r.metric=='MRR' else 1e-10)).sum())
    pvalue=(count+1)/5001
    lo,hi=np.quantile(values,[.025,.975],method='linear')
    for value,stored in [(values.mean(),r.permuted_mean),(lo,r.central95_lower),(hi,r.central95_upper),(pvalue,r.p_raw)]:max_permutation_error=max(max_permutation_error,abs(value-stored))
    assert len(values)==5000 and count==r.upper_tail_count
    recomputed.append(pvalue)
order=np.argsort(recomputed,kind='stable');adjusted=np.minimum(1,np.maximum.accumulate(np.array(recomputed)[order]*(12-np.arange(12))))
for index,value in zip(order,adjusted):assert abs(value-permutation.iloc[index].p_holm_12)<1e-12
assert max_permutation_error<1e-12
checks['all_12_permutation_tails_and_holm_corrections_recomputed']=True

sources=read('e4/label_support_sources.csv').fillna('');used=read('e4/query_start_evidence_used.csv').fillna('');overlap=read('e4/positive_source_overlap.csv').fillna('')
start=used.groupby('qid').canonical_source.apply(lambda s:set(s)-{''}).to_dict();label=defaultdict(set)
for r in sources[sources.cohort=='Replay'].itertuples():label[r.qid,r.positive_drug].add(r.canonical_source)
for r in overlap.itertuples():
    matches=(start.get(r.qid,set())&label[r.qid,r.positive_drug])-{''}
    assert bool(matches)==(str(r.same_source).lower()=='true')
    assert matches==set(filter(None,str(r.overlap_sources).split(';')))
assert len(overlap)==46 and overlap.same_source.astype(bool).sum()==7
retained=read('e4/retained_labels.csv');assert len(retained)==39 and retained.qid.nunique()==39
checks['all_46_actual_input_source_overlap_classifications_recomputed']=True

positive=labels.groupby('qid').positive_drug.apply(set).to_dict();decomposition=read('e5/query_displacement_decomposition.csv').set_index('qid')
def reciprocal(r):return Fraction(1,int(r)) if pd.notna(r) and r>0 else Fraction(0)
for q,g in candidates.groupby('qid'):
    positives=g[g.drug_norm.isin(positive[q])];old=positives[positives.b0_rank.notna()]
    graph=max((reciprocal(r) for r in old.b0_rank),default=Fraction(0));mix=max((reciprocal(r) for r in positives.b1_rank),default=Fraction(0));mix_old=max((reciprocal(r) for r in old.b1_rank),default=Fraction(0))
    for expected,col in [(mix_old-graph,'displacement'),(mix-mix_old,'coverage_gain'),(mix-graph,'net_change')]:assert abs(float(expected)-decomposition.loc[q,col])<1e-12
checks['all_45_displacement_identities_recomputed_with_exact_fractions']=True
generated=pd.read_csv(gen/'audited_main_results.csv')
assert len(generated)==20 and set(generated.method)=={'Graph','Mix','Append-SF','AltGraph','AltAppend','RRF','Context','CIViC','SharedFirstContext','Borda'}
checks['portable_table_builder_recomputed_10_main_policies_per_cohort']=True
settings=read('e6/reproduction_settings.csv');limit=settings[settings.setting=='Candidate limit'].iloc[0].value
assert '30' in limit and ('Top-30' in limit or '前30' in limit)
checks['corrected_candidate_limit_description_present']=True
report={'status':'passed','checks':checks,'max_confidence_interval_error':max_ci_error,'max_permutation_summary_error':max_permutation_error,'scope':'Verification from frozen ranks, archived query evidence, resampling indices and saved diagnostic replicates. No raw-KG feature extraction or model training.'}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
