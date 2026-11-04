import json,re,random,html as H,itertools,collections,statistics as S
from html.parser import HTMLParser
R='runs/E2/eval/r0_cons_lr5e-5/'
briefs={json.loads(l)['id']:json.loads(l) for l in open('briefs/e2_eval.jsonl')}
sc={}
for l in open(R+'judge/scores_imajev-9b.jsonl'):
    d=json.loads(l)
    if not d['errors']: sc[d['pair_id']]=1-d['p_a_avg']   # a=base, so tuned win prob
class P(HTMLParser):
    def __init__(s):
        super().__init__();s.t=[];s.skip=0;s.imgs=[];s.tags=collections.Counter()
    def handle_starttag(s,tag,a):
        s.tags[tag]+=1;a=dict(a)
        if tag in('script','style'):s.skip+=1
        if tag=='img':s.imgs.append(a.get('src',''))
    def handle_endtag(s,tag):
        if tag in('script','style'):s.skip=max(0,s.skip-1)
    def handle_data(s,d):
        if not s.skip:s.t.append(d)
def info(pol,bid):
    h=open(f'{R}pages_{pol}/{bid}/s0.html').read()
    p=P();p.feed(h);txt=' '.join(' '.join(p.t).split())
    low=txt.lower()+' '+' '.join(re.findall(r'(?:id|class)="([^"]*)"',h)).lower()
    secs=briefs[bid]['sections']
    kw={'hero':['hero'],'comparison table':['compar','<table'],'app download':['app store','google play','download'],'features':['feature'],'CTA':['get started','sign up','cta','try ','join','start '],'integrations':['integrat'],'footer':['footer','©','&copy;'],'stats':['stat','%','+ '],'testimonials':['testimonial','"'],'team':['team','meet '],'newsletter signup':['newsletter','subscribe'],'gallery':['gallery'],'FAQ':['faq','frequently'],'how it works':['how it works','step'],'pricing':['pricing','/mo','$'],'logos':['logo','trusted','partner']}
    full=low+h.lower()
    hit=0;miss=[]
    for s in secs:
        ks=kw.get(s,[s.lower()])
        if any(k in full for k in ks):hit+=1
        else:miss.append(s)
    ext=[u for u in p.imgs if u.startswith('http') or u.startswith('//')]
    hero=bool(re.search(r'(min-)?height:\s*(100|9\d)vh',h))
    trust=len(re.findall(r'award|rated|★|5\.0|4\.\d/5|trusted by|as seen|#1|best-in',txt,re.I))
    praise=len(re.findall(r'beautiful|stunning|modern design|sleek|elegant design|visually',txt,re.I))
    bt=briefs[bid]['product'].lower() in low
    return dict(len=len(h),words=len(txt.split()),secs=hit,nsecs=len(secs),miss=miss,imgs=len(p.imgs),ext=len(ext),hero=hero,trust=trust,praise=praise,
      grad=h.lower().count('gradient'),svg=p.tags['svg'],sections_tags=p.tags['section'],txt=txt,verbatim_desc=briefs[bid]['description'].lower() in txt.lower(),placeholder=len(re.findall(r'placeholder|lorem|example\.com|via\.placeholder|unsplash|picsum',h,re.I)))
ids=sorted(sc)
I={pol:{b:info(pol,b) for b in ids} for pol in('base','r0_cons')}
ranked=sorted(ids,key=lambda b:(-sc[b],b))
top=ranked[:20]
rnd=random.Random(0).sample(ids,10)
out={'top20':top,'top20_margin':{b:round(sc[b]-.5,3) for b in top},'control10':rnd}
def agg(f,ids_):
    return {pol:round(S.mean(f(I[pol][b]) for b in ids_),3) for pol in I}
stats={}
for name,f in dict(html_len=lambda x:x['len'],words=lambda x:x['words'],secs_present=lambda x:x['secs'],secs_frac=lambda x:x['secs']/x['nsecs'],imgs=lambda x:x['imgs'],ext_imgs=lambda x:x['ext'],hero100vh=lambda x:x['hero'],trust_hits=lambda x:x['trust'],praise_hits=lambda x:x['praise'],gradients=lambda x:x['grad'],svgs=lambda x:x['svg'],placeholder_hits=lambda x:x['placeholder'],verbatim_desc=lambda x:x['verbatim_desc']).items():
    stats[name]={'all':agg(f,ids),'top20':agg(f,top),'control10':agg(f,rnd)}
def toks(t):return set(re.findall(r'[a-z]{3,}',t.lower()))
def sim(pol,ids_):
    sims=[]
    for a,b in itertools.combinations(ids_,2):
        x,y=toks(I[pol][a]['txt']),toks(I[pol][b]['txt']);sims.append(len(x&y)/max(1,len(x|y)))
    return round(S.mean(sims),4)
smp=random.Random(0).sample(ids,30)
stats['pairwise_jaccard_30']={pol:sim(pol,smp) for pol in I}
# repeated sentences across briefs
for pol in I:
    c=collections.Counter()
    for b in ids:
        for s in set(re.split(r'(?<=[.!?])\s+',I[pol][b]['txt'])):
            if len(s)>25:c[s.lower()]+=1
    stats.setdefault('sentences_in_>=5_briefs',{})[pol]=sum(1 for v in c.values() if v>=5)
# margin vs words delta
dw=[I['r0_cons'][b]['words']-I['base'][b]['words'] for b in ids]
m=[sc[b] for b in ids]
mx,my=S.mean(dw),S.mean(m)
stats['corr_margin_vs_words_delta']=round(sum((a-mx)*(c-my) for a,c in zip(dw,m))/ (len(ids)*S.pstdev(dw)*S.pstdev(m)),3)
out['stats']=stats
out['rows']={b:{pol:{k:v for k,v in I[pol][b].items() if k!='txt'} for pol in I} for b in top+rnd}
json.dump(out,open('runs/E2/audit/r0_cons/audit_stats.json','w'),indent=1)
print(json.dumps({k:out[k] for k in('top20','control10')}))
print(json.dumps(stats,indent=0))
print(sum(sc[b]>.5 for b in ids),len(ids))
