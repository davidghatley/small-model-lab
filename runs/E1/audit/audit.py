import json, random, sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path('runs/E1'); J=['omnijev-0.8b','omnijev-4b','rsi-jev-4b','imajev-9b']
L=lambda p:[json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
ref={r['pair_id']:r for r in L(R/'labels/reference.jsonl')}
meta={d.name:json.loads((d/'meta.json').read_text()) for d in (R/'pairs').iterdir() if (d/'meta.json').exists()}
S={j:{r['pair_id']:r for r in L(R/f'scores/{j}.jsonl')} for j in J}
out=[]
def P(*a): s=' '.join(str(x) for x in a); print(s); out.append(s)
def boot(v,seed=0,n=2000):
    rng=random.Random(seed); v=list(v)
    if not v: return (None,None)
    m=sorted(sum(rng.choice(v) for _ in v)/len(v) for _ in range(n)); return m[int(.025*n)],m[int(.975*n)-1]
# recompute p_a_avg
bad=0
for j in J:
    for r in S[j].values():
        if r['p_a_ab'] is None or r['p_a_ba'] is None or r['p_first_ab'] is None: bad+=1; continue
        if abs(r['p_a_avg']-(r['p_a_ab']+r['p_a_ba'])/2)>1e-9 or abs(r['p_a_ba']-(1-r['p_first_ba']))>1e-9 or abs(r['p_a_ab']-r['p_first_ab'])>1e-9: bad+=1
P('rows with missing/inconsistent fields:',bad, {j:len(S[j]) for j in J}, {j:sum(bool(r['errors']) for r in S[j].values()) for j in J})
def pred(r): return 'a' if r['p_a_avg']>=.5 else 'b'
def conf(r): return max(r['p_a_avg'],1-r['p_a_avg'])
sm=[k for k in ref if k.startswith('sm')]
P('ref counts',{p:sum(k.startswith(p) for k in ref) for p in('sm','fh','fg')}, 'ref label dist sm', {x:sum(ref[k]['better']==x for k in sm) for x in 'ab'})
P('\n## Claim 1: sm vs reference')
for j in J:
    ids=[k for k in sm if k in S[j] and S[j][k]['p_a_avg'] is not None]
    ok={k:pred(S[j][k])==ref[k]['better'] for k in ids}
    P(f'{j}: overall {np.mean(list(ok.values())):.3f} n={len(ids)}')
    for t in(.6,.7,.8):
        h=[k for k in ids if conf(S[j][k])>=t]; v=[ok[k] for k in h]
        lo,hi=boot(v); P(f'  conf>={t}: n={len(h)} cov={len(h)/len(ids):.2f} agree={np.mean(v):.3f} CI[{lo:.3f},{hi:.3f}]')
    h=[k for k in ids if abs(S[j][k]['p_a_avg']-.5)>=.2]; P(f'  |p-.5|>=.2 (conf>=.7) n={len(h)} agree={np.mean([ok[k] for k in h]):.3f}')
    h=[k for k in ids if ref[k]['confidence']>=.75]; P(f'  ref conf>=.75: n={len(h)} agree={np.mean([ok[k] for k in h]):.3f}')
    lo,hi=boot([ok[k] for k in ids]); P(f'  overall CI [{lo:.3f},{hi:.3f}]')
P('\n## Gate as coded: all reference pairs (sm+fh+fg), conf>=0.8')
for j in J:
    ids=[k for k in ref if k in S[j]]; h=[k for k in ids if conf(S[j][k])>=.8]
    v=[pred(S[j][k])==ref[k]['better'] for k in h]; lo,hi=boot(v)
    vs=[pred(S[j][k])==ref[k]['better'] for k in h if k.startswith('sm')]; los,his=boot(vs)
    P(f'{j}: all n={len(h)} {np.mean(v):.3f} CI[{lo:.3f},{hi:.3f}] | sm-only n={len(vs)} {np.mean(vs) if vs else float("nan"):.3f} CI[{los},{his}]')
P('\n## Claim 2: position bias (all scored pairs)')
for j in J:
    rs=[r for r in S[j].values() if r['p_first_ab'] is not None and r['p_first_ba'] is not None]
    pf=[x for r in rs for x in(r['p_first_ab'],r['p_first_ba'])]
    fl=np.mean([r['choice_ab']!=r['choice_ba'] for r in rs])
    # by source
    d={}
    for p in('sm','fh','fg'):
        q=[r for r in rs if r['pair_id'].startswith(p)]
        d[p]=(round(float(np.mean([r['choice_ab']!=r['choice_ba'] for r in q])),2),round(float(np.mean([x for r in q for x in(r['p_first_ab'],r['p_first_ba'])])),2))
    P(f'{j}: n={len(rs)} meanP(first)={np.mean(pf):.3f} flip={fl:.3f} by-source(flip,P1)={d}')
P('\n## Claim 3: by construction (fg)')
for j in J:
    fg=[k for k in meta if k.startswith('fg') and k in S[j] and S[j][k]['p_a_avg'] is not None]
    ok=[pred(S[j][k])==meta[k]['intended_better'] for k in fg]; lo,hi=boot(ok)
    sev={}
    for k,o in zip(fg,ok): sev.setdefault(meta[k]['flaw_severity'],[]).append(o)
    P(f'{j}: n={len(fg)} {np.mean(ok):.3f} CI[{lo:.3f},{hi:.3f}] '+str({s:(len(v),round(float(np.mean(v)),2)) for s,v in sorted(sev.items())}))
P('\n## Reference vs by-construction on the 20 fg in reference')
fgr=[k for k in ref if k.startswith('fg')]
P('agree:',sum(ref[k]['better']==meta[k]['intended_better'] for k in fgr),'/',len(fgr))
P('\n## Baselines on sm vs reference')
def feats(k):
    f={}
    for s in 'ab':
        im=Image.open(R/'pairs'/k/f'{s}.png').convert('RGB'); a=np.asarray(im).astype(float)
        bg=np.median(a.reshape(-1,3),axis=0)  # dominant-ish bg
        f[s]=dict(nonbg=float((np.abs(a-bg).sum(2)>30).mean()), dark=float(a.mean()), size=im.size[0]*im.size[1], edges=float((np.abs(np.diff(a.mean(2),axis=1))>20).mean()),
                  std=float(a.std()))
    return f
F={k:feats(k) for k in sm}
for nm in('nonbg','dark','size','edges','std'):
    for sg,name in((1,'higher'),(-1,'lower')):
        v=[]
        for k in sm:
            x,y=F[k]['a'][nm],F[k]['b'][nm]
            if x==y: v.append(0.5); continue
            v.append(float(('a' if sg*(x-y)>0 else 'b')==ref[k]['better']))
        lo,hi=boot(v)
        P(f'{nm} {name}: {np.mean(v):.3f} CI[{lo:.2f},{hi:.2f}]')
P('ref side balance: pick always a =',np.mean([ref[k]['better']=='a' for k in sm]))
# correlation of judge with baseline
for j in J:
    for nm in('nonbg','dark'):
        ids=[k for k in sm if k in S[j]]
        P(f'{j} agrees with "{nm} higher" on sm:',round(float(np.mean([pred(S[j][k])==('a' if F[k]['a'][nm]>F[k]['b'][nm] else 'b') for k in ids])),3))
# hi-conf disagreements for 0.8b
j='omnijev-0.8b'
dis=[k for k in sm if k in S[j] and conf(S[j][k])>=.7 and pred(S[j][k])!=ref[k]['better']]
dis.sort(key=lambda k:-conf(S[j][k]))
P('\n## 0.8b hi-conf (>=.7) disagreements on sm:',len(dis))
for k in dis: P(k,'p_a_avg=%.2f'%S[j][k]['p_a_avg'],'ref',ref[k]['better'],ref[k]['confidence'],'|',ref[k]['rationale'])
ECE=[]
Path('runs/E1/audit/audit_script_output.txt').write_text('\n'.join(out))
