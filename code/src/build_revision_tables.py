"""Generate audited manuscript tables and Figure 2 from frozen experiment artifacts.

Writes only inside this script's generated/ directory. No model fitting or input mutation.
"""
import argparse, csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

sys.stdout.reconfigure(encoding='utf-8')
PACKAGE=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description='Rebuild paper tables and figure from frozen analysis artifacts.')
parser.add_argument('--run',type=Path,default=PACKAGE/'data/processed/frozen_analysis',help='Input frozen analysis directory (default: data/processed/frozen_analysis).')
parser.add_argument('--out',type=Path,default=PACKAGE/'code/results/generated/primary',help='Output directory (default: code/results/generated/primary).')
args=parser.parse_args()
RUN=args.run.resolve()
OUT=args.out.resolve()
OUT.mkdir(parents=True,exist_ok=True)
SOURCE_RUN='20261123T004441Z'
INPUTS={}
def read(rel):
    p=RUN/rel
    INPUTS[p.relative_to(RUN).as_posix()]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    return pd.read_csv(p)
def write(name,s): (OUT/name).write_text(s+'\n',encoding='utf-8')
def fmt(v,n=4):return f'{float(v):.{n}f}'
def sig(v,n=4):return f'{float(v):+.{n}f}'
def interval(lo,hi,n=4,signed=True):
    number=sig if signed else fmt
    return r'$[\,'+number(lo,n)+r',\,'+number(hi,n)+r'\,]$'
# Captions contain names only; interpretation and units belong in manuscript prose.
def latex_table(name,caption,label,spec,head,rows,fontsize='small',pad='3.5pt'):
    lines=['% Generated from frozen artifacts; edit build_revision_tables.py, not numeric cells.',r'\begin{table}[t]',r'\centering',r'\caption{'+caption+'}',r'\label{'+label+'}','\\'+fontsize,r'\setlength{\tabcolsep}{'+pad+'}',r'\begin{tabular}{'+spec+'}',r'\toprule',' & '.join(head)+r' \\',r'\midrule']
    lines.extend(rows);lines.extend([r'\bottomrule',r'\end{tabular}'])
    lines.append(r'\end{table}');write(name,'\n'.join(lines))
def metric(c,l,col):
    lookup=c.set_index(['qid','drug_norm'])[col].to_dict();qrr=[];p_rr=[];hits={k:0 for k in [1,3,5,10]};cov=0
    for q,g in l.groupby('qid',sort=True):
        ranks=[lookup.get((q,d),np.nan) for d in g.positive_drug]
        valid=[float(x) for x in ranks if pd.notna(x) and x>0]
        for r in ranks:
            if pd.notna(r) and r>0:p_rr.append(1/float(r));cov+=1
            else:p_rr.append(0.)
        best=min(valid) if valid else np.inf;qrr.append(1/best if np.isfinite(best) else 0.)
        for k in hits:hits[k]+=int(best<=k)
    return {'queries':len(qrr),'positive_pairs':len(p_rr),'query_mrr':np.mean(qrr),'pair_mrr':np.mean(p_rr),'covered_pairs':cov,**{f'hr{k}_hits':v for k,v in hits.items()}}

summary=read('e2/membership_diagnostic_summary.csv')
cohorts={}
for cohort,prefix in [('Development','development'),('Replay','replay')]:
    c=read(f'e0/frozen_analysis_bundle/{prefix}_candidates.csv')
    l=read(f'e0/frozen_analysis_bundle/{prefix}_labels.csv')
    shared=read(f'e2/{prefix}_shared_first_rankings.csv')
    assert set(zip(c.qid,c.drug_norm))==set(zip(shared.qid,shared.drug_norm))
    sfmap=shared.set_index(['qid','drug_norm']).shared_first_rank.to_dict()
    c['shared_first_rank']=[sfmap[q,d] for q,d in zip(c.qid,c.drug_norm)]
    # Original Borda uses the same complete two lists with length normalization.
    c['borda_rank']=np.nan
    for q,g in c.groupby('qid',sort=True):
        lg=int(g.rg.notna().sum());le=int(g.re.notna().sum())
        sg=(lg-g.rg+1)/lg if lg else pd.Series(0.,index=g.index)
        se=(le-g.re+1)/le if le else pd.Series(0.,index=g.index)
        order=g.assign(score=sg.fillna(0.)+se.fillna(0.)).sort_values(['score','drug_norm'],ascending=[False,True],kind='stable')
        c.loc[order.index,'borda_rank']=np.arange(1,len(g)+1)
    m=metric(c,l,'borda_rank')
    expected=.4620596205962059 if cohort=='Development' else .30402107107421117
    assert abs(m['query_mrr']-expected)<1e-14
    summary=pd.concat([summary,pd.DataFrame([{'method':'Borda','cohort':cohort,**m}])],ignore_index=True)
    methods={'Graph':'b0_rank','Mix':'b1_rank','Append-SF':'b2_rank','AltGraph':'b3_rank','AltAppend':'b4_rank','RRF':'b5_rank','Context':'b6_rank','CIViC':'re','SharedFirstContext':'shared_first_rank','Borda':'borda_rank'}
    for method,col in methods.items():
        actual=metric(c,l,col);expected_row=summary[(summary.cohort==cohort)&(summary.method==method)].iloc[0]
        for field in ['queries','positive_pairs','query_mrr','pair_mrr','covered_pairs','hr1_hits','hr3_hits','hr5_hits','hr10_hits']:
            assert abs(actual[field]-expected_row[field])<1e-13,(cohort,method,field,actual[field],expected_row[field])
    cohorts[cohort]=(c,l)
summary.to_csv(OUT/'audited_main_results.csv',index=False,encoding='utf-8-sig',float_format='%.17g')
display={'CIViC':'CIViC branch','SharedFirstContext':'Shared-first'}
order=['Graph','Mix','CIViC','Append-SF','AltGraph','AltAppend','Borda','Context','SharedFirstContext','RRF']
rows=[]
for cohort,title in [('Development','January development: 41 queries, 43 pairs'),('Replay','Retrospective new-context replay: 45 queries, 46 pairs')]:
    rows.append(r'\multicolumn{7}{l}{\textit{'+title+r'}} \\')
    for method in order:
        r=summary[(summary.cohort==cohort)&(summary.method==method)].iloc[0]
        rows.append(' & '.join([display.get(method,method),f'{int(r.covered_pairs)}/{int(r.positive_pairs)}',fmt(r.query_mrr),fmt(r.pair_mrr),*[f'{int(r[f"hr{k}_hits"])}/{int(r.queries)}' for k in [1,3,5]]])+r' \\')
    if cohort=='Development':rows.append(r'\midrule')
latex_table('table_main_results.tex','Main results','tab:main','lrrrrrr',['Method','Pair cov.','MRR$_q$','MRR$_p$','HR@1','HR@3','HR@5'],rows,pad='3pt')

coverage=[]
for cohort,(c,l) in cohorts.items():
    positives=set(zip(l.qid,l.positive_drug))
    masks={'Graph $R_0$':c.rg.notna(),'Evidence $E$':c.re.notna(),'Union $R_1$':pd.Series(True,index=c.index),r'Shared $R_0\cap E$':c.origin.eq('R0_and_CIViC_retrieved'),'Graph only':c.origin.eq('R0_primekg'),'Evidence only':c.origin.eq('CIViC_retrieved_new')}
    for support,mask in masks.items():
        g=c[mask];n=sum((q,d) in positives for q,d in zip(g.qid,g.drug_norm))
        coverage.append({'cohort':cohort,'support':support,'candidate_rows':len(g),'covered_positive_pairs':n,'total_positive_pairs':len(l)})
cov=pd.DataFrame(coverage);cov.to_csv(OUT/'audited_candidate_coverage.csv',index=False,encoding='utf-8-sig')
replay_cov=cov[cov.cohort=='Replay']
assert replay_cov.candidate_rows.tolist()==[1262,438,1580,120,1142,318]
assert replay_cov.covered_positive_pairs.tolist()==[20,32,33,19,1,13]
rows=[]
for support in cov.support.drop_duplicates():
    cells=[support]
    for cohort in ['Development','Replay']:
        r=cov[(cov.cohort==cohort)&(cov.support==support)].iloc[0]
        cells.extend([f'{int(r.candidate_rows):,}',f'{int(r.covered_positive_pairs)}/{int(r.total_positive_pairs)}'])
    rows.append(' & '.join(cells)+r' \\')
latex_table('table_candidate_coverage.tex','Candidate coverage','tab:coverage','lrrrr',['Support','Dev. records','Dev. pairs','Replay records','Replay pairs'],rows,pad='4pt')

paired=read('e1/strong_baseline_summary.csv');ci=read('e1/bootstrap_confidence_intervals.csv');ci=ci[ci.metric=='rr']
comp_names={'RRF - Context':'RRF--Context','RRF - CIViC':'RRF--CIViC','SharedFirstContext - Context':'Shared--Context','RRF - SharedFirstContext':'RRF--Shared'}
rows=[]
for r in paired.itertuples():
    drug=ci[(ci.comparison==r.comparison)&(ci.criterion=='drug')].iloc[0];source=ci[(ci.comparison==r.comparison)&(ci.criterion=='source')].iloc[0]
    rows.append(' & '.join([comp_names[r.comparison],sig(r.delta_mrr),interval(drug.ci_lower_95,drug.ci_upper_95),interval(source.ci_lower_95,source.ci_upper_95),f'{int(r.wins)}/{int(r.ties)}/{int(r.losses)}'])+r' \\')
latex_table('table_paired_replay.tex','Paired replay comparisons','tab:paired','lrrrr',['Comparison',r'$\Delta$MRR',r'Drug 95\% interval',r'Source 95\% interval','W/T/L'],rows,fontsize='small',pad='2.5pt')

trade=read('e1/new_old_top5_tradeoff.csv')
rows=[' & '.join([display.get(r.method,r.method),f'{int(r.evidence_exclusive_top5)}/{int(r.evidence_exclusive_positive_pairs)}',f'{int(r.original_top5_retained)}/{int(r.append_sf_original_top5_pairs)}'])+r' \\' for r in trade.itertuples()]
latex_table('table_new_old_tradeoff.tex','Positive retention','tab:tradeoff','lrr',['Policy','Evidence-only top five','Old top-five retained'],rows)

lens=read('e2/branch_length_summary.csv')
rows=[' & '.join([r.cohort,r.branch,fmt(r.median,0),f'{int(r.min)}--{int(r.max)}',str(int(r.empty_lists))])+r' \\' for r in lens.itertuples()]
latex_table('table_branch_lengths.tex','Branch lengths','tab:lengths','llrrr',['Cohort','Branch','Median','Range','Empty'],rows)

perm=read('e3/permutation_tail_tests.csv')
def perm_rows(sub):
    rows=[]
    for r in sub.itertuples():
        scale=1 if r.metric=='MRR' else 100;n=4 if scale==1 else 2
        metric='MRR' if scale==1 else r.metric+r' (\%)'
        cells=[r.shuffled_branch,metric,fmt(r.original*scale,n),fmt(r.permuted_mean*scale,n),interval(r.central95_lower*scale,r.central95_upper*scale,n,signed=False),fmt(r.p_raw),fmt(r.p_holm_12)]
        rows.append(' & '.join(cells)+r' \\')
    return rows
latex_table('table_shuffle_replay.tex','Order shuffles','tab:order-ablation','llrrrrr',['Shuffled','Metric','Observed','Mean',r'Central 95\%','Upper $p$','Holm $p$'],perm_rows(perm[perm.cohort=='Replay']),fontsize='small',pad='2.2pt')
rows=[]
for cohort in ['Development','Replay']:
    rows.append(r'\multicolumn{7}{l}{\textit{'+cohort+r'}} \\');rows.extend(perm_rows(perm[perm.cohort==cohort]))
    if cohort=='Development':rows.append(r'\midrule')
latex_table('table_shuffle_all_supp.tex','Order shuffles across cohorts','tab:supp-shuffle','llrrrrr',['Shuffled','Metric','Observed','Mean',r'Central 95\%','Upper $p$','Holm $p$'],rows,pad='2.2pt')

source=read('e4/source_excluded_metrics.csv');sub=source[source.subset=='confirmed_overlap_removed']
rows=[' & '.join([r.method,fmt(r.query_mrr),f'{int(r.covered_pairs)}/{int(r.positive_pairs)}',*[f'{int(getattr(r,f"hr{k}_hits"))}/{int(r.queries)}' for k in [1,3,5]]])+r' \\' for r in sub.itertuples()]
latex_table('table_source_excluded.tex','Source exclusion','tab:source-exclusion','lrrrrr',['Policy','MRR$_q$','Pair cov.','HR@1','HR@3','HR@5'],rows)

cases=read('e6/case_rankings_with_context.csv')
specs=[('Jul25_Jan26','Breast Cancer|MP:263','dovitinib','Jan. Breast MP:263'),('Jul25_Jan26','Breast Cancer|MP:263','erdafitinib','Jan. Breast MP:263'),('W1','Colorectal Cancer|MP:5117','pembrolizumab','W1 Colorectal MP:5117'),('W1','Diffuse Midline Glioma, H3 K27M-mutant|MP:3807','dordaviprone','W1 Midline glioma MP:3807'),('W3','Melanoma|MP:281','belvarafenib','W3 Melanoma MP:281$^*$')]
rank_lookup=pd.concat([cohorts[n][0] for n in cohorts]).set_index(['window_id','query_id','drug_norm'])
case_records=[];rows=[]
for w,q,d,label in specs:
    sel=cases[(cases.window_id==w)&(cases.query_id==q)&(cases.positive_drug==d)];assert len(sel)==1;r=sel.iloc[0]
    alt=rank_lookup.loc[(w,q,d),'b4_rank'] if (w,q,d) in rank_lookup.index else np.nan
    vals=[r.Append_SF_rank,alt,r.Context_rank,r.SharedFirstContext_rank,r.RRF_rank]
    def rk(v):return '--' if pd.isna(v) else str(int(v))
    rows.append(' & '.join([label,d,*[rk(v) for v in vals]])+r' \\')
    case_records.append({'window_id':w,'query_id':q,'positive_drug':d,'Append-SF':r.Append_SF_rank,'AltAppend':alt,'Context':r.Context_rank,'Shared-first':r.SharedFirstContext_rank,'RRF':r.RRF_rank})
latex_table('table_cases_with_context.tex','Case study','tab:cases','llrrrrr',['Query context','Drug','App.','Alt.','Ctx.','Shared','RRF'],rows,fontsize='small',pad='2pt')
pd.DataFrame(case_records).to_csv(OUT/'audited_case_comparison.csv',index=False,encoding='utf-8-sig')

# Plot all five original policies plus Context and the new shared-first control.
replay=summary[summary.cohort=='Replay'].set_index('method')
styles={
 'Graph':{'label':'Graph','color':'#7d8794','marker':'s','linestyle':':'},
 'Append-SF':{'label':'Append-SF','color':'#917754','marker':'D','linestyle':'--'},
 'CIViC':{'label':'CIViC branch','color':'#d28b30','marker':'o','linestyle':'--'},
 'Context':{'label':'Context','color':'#8b5f9e','marker':'x','linestyle':'-'},
 'Borda':{'label':'Borda','color':'#3e858c','marker':'v','linestyle':'-.'},
 'RRF':{'label':'RRF','color':'#245b97','marker':'o','linestyle':'-'},
 'SharedFirstContext':{'label':'Shared-first Context','color':'#287b57','marker':'^','linestyle':'-'}
}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
fig,ax=plt.subplots(figsize=(4.8,3.6))
data=[]
for method,style in styles.items():
    counts=[int(replay.loc[method,f'hr{k}_hits']) for k in [1,3,5,10]]
    if method=='CIViC':ax.plot([1,3,5,10],np.array(counts)/45,markersize=7,markerfacecolor='none',linewidth=1.5,**style)
    else:ax.plot([1,3,5,10],np.array(counts)/45,markersize=5,linewidth=1.5,**style)
    data.append({'method':method,'display_label':style['label'],'hits':dict(zip([1,3,5,10],counts)),'denominator_queries':45,'positive_pairs':46,**style})
ax.set_title('Retrospective new-context replay\n45 queries, 46 positives',fontsize=9.2)
ax.set_xlabel('Retrieval depth K');ax.set_ylabel('Query hit rate');ax.set_xticks([1,3,5,10]);ax.set_ylim(0,.75);ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0));ax.grid(axis='y',alpha=.2)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.27),ncol=3,frameon=False,fontsize=7.8,handlelength=1.9,columnspacing=.95)
fig.subplots_adjust(left=.14,right=.98,top=.85,bottom=.32)
fig.savefig(OUT/'replay_hr_at_k_with_context.pdf');fig.savefig(OUT/'replay_hr_at_k_with_context.png',dpi=240);plt.close(fig)
write('figure_hrk.tex',r'''\begin{figure}[t]
\centering
\includegraphics[width=.96\textwidth]{generated/replay_hr_at_k_with_context.pdf}
\caption{Hit rates}
\label{fig:hrk}
\end{figure}''')
legend={'source_run':SOURCE_RUN,'figure':'replay_hr_at_k_with_context.pdf','cohort':'Retrospective new-context replay','queries':45,'positive_pairs':46,'points':data,'note':'Context and CIViC have the same HR values at all four plotted cutoffs; both are retained with distinct line/marker styles.'}
write('figure_legend_mapping.json',json.dumps(legend,ensure_ascii=False,indent=2))

status={'status':'passed','source_run':SOURCE_RUN,'main_methods_per_cohort':10,'borda_independently_reconstructed':True,'all_summary_methods_recomputed_from_frozen_ranks':True,'replay_support_records':dict(zip(replay_cov.support,replay_cov.candidate_rows.astype(int))),'replay_support_positive_pairs':dict(zip(replay_cov.support,replay_cov.covered_positive_pairs.astype(int))),'case_rows':len(case_records),'figure_queries':45,'figure_positive_pairs':46,'dependencies':['booktabs','graphicx'],'input_manifest':INPUTS,'outputs':sorted(p.name for p in OUT.iterdir() if p.is_file())}
write('tables_validation.json',json.dumps(status,ensure_ascii=False,indent=2))
write('INTEGRATION_NOTES.txt','''Use title-only figure and table captions. Place sample definitions, units, abbreviations and interpretation in manuscript prose; do not add below-table note blocks.\nFragments use booktabs and graphicx, already loaded in the baseline. Inputs are relative to manuscript root; include using \\input{generated/table_main_results.tex}, etc.
Main recommendations: table_candidate_coverage.tex, table_main_results.tex, table_paired_replay.tex, table_shuffle_replay.tex, table_cases_with_context.tex, table_source_excluded.tex, and figure_hrk.tex. Do not duplicate table_new_old_tradeoff.tex and table_branch_lengths.tex in main if space is tight; move to supplement. table_shuffle_all_supp.tex is full two-cohort supplementary reporting.
Main CI table's Shared--Context and RRF--Shared rows already show the two membership steps; no duplicate step table is generated.
RRF--Context delta +0.0435293817, drug/source CIs both cross zero. Shared-first replay MRR 0.4264844209 vs RRF 0.3895376121; all four Context/RRF/Shared-first/CIViC HR@5 = 27/45. Source exclusion leaves 39 queries/39 positives; RRF HR@5 22/39 vs Context/CIViC 23/39. Do not claim stable superiority or causal membership attribution.
Table labels preserve baseline main/coverage/cases/order-ablation/hrk identifiers; paired, source-exclusion, tradeoff and lengths labels are new. Use table_shuffle_all_supp only in Supplement_S1 if repeated labels avoided.
''')
print(json.dumps({k:v for k,v in status.items() if k not in ['input_manifest','outputs']},ensure_ascii=False,indent=2))
