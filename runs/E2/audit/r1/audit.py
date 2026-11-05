import json,re,random,itertools,collections,statistics as S,colorsys
import numpy as np
from PIL import Image
from html.parser import HTMLParser
E0='runs/E2/eval/r0_cons_lr5e-5/';E1='runs/E2/eval/r1/';OUT='runs/E2/audit/r1/'
briefs={json.loads(l)['id']:json.loads(l) for l in open('briefs/e2_eval.jsonl')}
sc={}
for l in open(E1+'judge/scores_imajev-9b.jsonl'):
    d=json.loads(l)
    if not d['errors']: sc[d['pair_id']]=1-d['p_a_avg']   # a=base
ids=sorted(sc)
PATH={'base':E1+'pages_base/{b}/s0','r0':E0+'pages_r0_cons/{b}/s0','r1':E1+'pages_r1/{b}/s0'}
class P(HTMLParser):
    def __init__(s):
        super().__init__();s.t=[];s.skip=0;s.imgs=[];s.tags=collections.Counter();s.seq=[];s.cls=set()
    def handle_starttag(s,tag,a):
        s.tags[tag]+=1;s.seq.append(tag);a=dict(a)
        for c in (a.get('class') or '').split():s.cls.add(c.lower())
        if tag in('script','style'):s.skip+=1
        if tag=='img':s.imgs.append(a.get('src',''))
    def handle_endtag(s,tag):
        if tag in('script','style'):s.skip=max(0,s.skip-1)
    def handle_data(s,d):
        if not s.skip:s.t.append(d)
KW={'hero':['hero'],'comparison table':['compar','<table'],'app download':['app store','google play','download'],'features':['feature'],'CTA':['get started','sign up','cta','try ','join','start '],'integrations':['integrat'],'footer':['footer','©','&copy;'],'stats':['stat','%','+ '],'testimonials':['testimonial','"'],'team':['team','meet '],'newsletter signup':['newsletter','subscribe'],'gallery':['gallery'],'FAQ':['faq','frequently'],'how it works':['how it works','step'],'pricing':['pricing','/mo','$'],'logos':['logo','trusted','partner']}
def info(path,br):
    h=open(path+'.html').read();p=P();p.feed(h)
    txt=' '.join(' '.join(p.t).split());low=txt.lower()+' '+' '.join(re.findall(r'(?:id|class)="([^"]*)"',h)).lower();full=low+h.lower()
    secs=br['sections'];hit=sum(any(k in full for k in KW.get(s,[s.lower()])) for s in secs)
    ext=[u for u in p.imgs if u.startswith('http') or u.startswith('//')]
    hexes=set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{6}\b',h))
    return dict(len=len(h),words=len(txt.split()),secs_frac=hit/len(secs),imgs=len(p.imgs),ext_imgs=len(ext),
      hero100vh=bool(re.search(r'(min-)?height:\s*(100|9\d)vh',h)),
      trust=len(re.findall(r'award|rated|★|5\.0|4\.\d/5|trusted by|as seen|#1|best-in',txt,re.I)),
      praise=len(re.findall(r'beautiful|stunning|modern design|sleek|elegant design|visually',txt,re.I)),
      grad=h.lower().count('gradient'),svg=p.tags['svg'],welcome=bool(re.search(r'<h1[^>]*>\s*welcome to',h,re.I)),
      p6a11cb=('6a11cb' in h.lower()),nhex=len(hexes),hexes=hexes,txt=txt,seq=p.seq,cls=p.cls,
      boxshadow=h.lower().count('box-shadow'),verbatim=br['description'].lower() in txt.lower())
def toks(t):return set(re.findall(r'[a-z]{3,}',t.lower()))
def jac(a,b):return len(a&b)/max(1,len(a|b))
def img(path,size=(64,40)):
    return Image.open(path+'.png').convert('RGB').resize(size,Image.BILINEAR)
def feats(path):
    im=img(path);a=np.asarray(im,dtype=np.float32)/255
    g=np.asarray(im.convert('L'),dtype=np.float32)/255
    full=Image.open(path+'.png').convert('RGB');w,hh=full.size
    hero=np.asarray(full.crop((0,0,w,int(hh*.3))).resize((32,12)),dtype=np.float32).reshape(-1,3)
    q=(hero//64).astype(int);binid=q[:,0]*16+q[:,1]*4+q[:,2]
    pc=collections.Counter(binid.tolist()).most_common(1)[0][0]
    # hue bucket of mean hero color (saturation-aware)
    m=hero.mean(0)/255;hh_,s,v=colorsys.rgb_to_hsv(*m)
    hb='gray/white' if s<.12 else ('dark' if v<.2 else f'hue{int(hh_*12)%12}')
    # histogram 4 bins/channel over whole page
    hist=np.histogramdd(a.reshape(-1,3),bins=(4,4,4),range=((0,1),)*3)[0].ravel();hist/=hist.sum()
    return dict(gray=g.ravel(),col=a.ravel(),hist=hist,pbin=pc,hue=hb,hero_mean=m)
def mpd(vs,pairs):return float(np.mean([np.linalg.norm(vs[i]-vs[j])/np.sqrt(len(vs[i])) for i,j in pairs]))
rng=random.Random(0);smp=rng.sample(ids,30);pairs=list(itertools.combinations(range(30),2))
I={};F={}
for pol in PATH:
    I[pol]={b:info(PATH[pol].format(b=b),briefs[b]) for b in ids}
    F[pol]={b:feats(PATH[pol].format(b=b)) for b in ids}
stats={'n':len(ids)}
def rowagg(f):return {pol:round(float(np.mean([f(I[pol][b]) for b in ids])),3) for pol in I}
for k in['len','words','secs_frac','imgs','ext_imgs','hero100vh','trust','praise','grad','svg','welcome','p6a11cb','nhex','boxshadow','verbatim']:
    stats[k]=rowagg(lambda x,k=k:x[k])
# collapse across briefs
cross={}
for pol in PATH:
    c={}
    c['gray64x40_dist']=mpd([F[pol][b]['gray'] for b in smp],pairs)
    c['color64x40_dist']=mpd([F[pol][b]['col'] for b in smp],pairs)
    c['hist_L1']=float(np.mean([np.abs(F[pol][smp[i]]['hist']-F[pol][smp[j]]['hist']).sum() for i,j in pairs]))
    c['text_jaccard']=float(np.mean([jac(toks(I[pol][smp[i]]['txt']),toks(I[pol][smp[j]]['txt'])) for i,j in pairs]))
    c['tagbigram_jaccard']=float(np.mean([jac(set(zip(I[pol][smp[i]]['seq'],I[pol][smp[i]]['seq'][1:])),set(zip(I[pol][smp[j]]['seq'],I[pol][smp[j]]['seq'][1:]))) for i,j in pairs]))
    c['class_jaccard']=float(np.mean([jac(I[pol][smp[i]]['cls'],I[pol][smp[j]]['cls']) for i,j in pairs]))
    c['hexcolor_jaccard']=float(np.mean([jac(I[pol][smp[i]]['hexes'],I[pol][smp[j]]['hexes']) for i,j in pairs]))
    hc=collections.Counter(F[pol][b]['hue'] for b in ids);c['hero_hue_buckets']=dict(hc.most_common())
    c['top_hero_hue_share']=hc.most_common(1)[0][1]/len(ids)
    pb=collections.Counter(F[pol][b]['pbin'] for b in ids);c['distinct_primary_bins']=len(pb);c['top_primary_bin_share']=pb.most_common(1)[0][1]/len(ids)
    hm=np.array([F[pol][b]['hero_mean'] for b in ids]);c['hero_mean_color_std']=float(hm.std(0).mean())
    allhex=collections.Counter(h for b in ids for h in I[pol][b]['hexes']);c['distinct_hex_total']=len(allhex);c['top5_hex']=allhex.most_common(5)
    c['hex_per_page']=float(np.mean([I[pol][b]['nhex'] for b in ids]))
    sc_=collections.Counter()
    for b in ids:
        for s in set(re.split(r'(?<=[.!?])\s+',I[pol][b]['txt'])):
            if len(s)>25:sc_[s.lower()]+=1
    c['sentences_in_>=5_briefs']=sum(v>=5 for v in sc_.values())
    h1=collections.Counter()
    for b in ids:
        m=re.search(r'<h1[^>]*>(.*?)</h1>',open(PATH[pol].format(b=b)+'.html').read(),re.S|re.I)
        if m:h1[re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',m.group(1))).strip().lower()]+=1
    c['distinct_h1_frac']=len(h1)/max(1,sum(h1.values()))
    cross[pol]={k:(round(v,4) if isinstance(v,float) else v) for k,v in c.items()}
stats['across_briefs_30']=cross
# within-brief (training samples)
within={}
for r,d in(('round0','runs/E2/round0/pages/'),('round1','runs/E2/round1/pages/')):
    import os
    bs=sorted(x for x in os.listdir(d) if x.startswith('e2_'));tj=[];gd=[];cd=[];nv=[];hx=[]
    nuniq=[]
    for b in bs:
        ps=[d+b+f'/s{k}' for k in range(4) if os.path.exists(d+b+f'/s{k}.png') and os.path.exists(d+b+f'/s{k}.html')]
        if len(ps)<4:continue
        hs=[open(p+'.html').read() for p in ps];pp=[]
        for h in hs:
            q=P();q.feed(h);pp.append(q)
        tx=[toks(' '.join(' '.join(q.t).split())) for q in pp]
        fs=[feats(p) for p in ps]
        for i,j in itertools.combinations(range(4),2):
            tj.append(jac(tx[i],tx[j]))
            gd.append(np.linalg.norm(fs[i]['gray']-fs[j]['gray'])/np.sqrt(2560))
            cd.append(np.linalg.norm(fs[i]['col']-fs[j]['col'])/np.sqrt(7680))
            hx.append(jac(set(re.findall(r'#[0-9a-f]{6}\b',hs[i].lower())),set(re.findall(r'#[0-9a-f]{6}\b',hs[j].lower()))))
        nuniq.append(len(set(hs)))
    within[r]=dict(briefs=len(nuniq),text_jaccard=round(float(np.mean(tj)),4),gray_dist=round(float(np.mean(gd)),4),color_dist=round(float(np.mean(cd)),4),hex_jaccard=round(float(np.mean(hx)),4),mean_distinct_html_of_4=round(float(np.mean(nuniq)),3),frac_briefs_all4_identical_html=round(float(np.mean([n==1 for n in nuniq])),3))
stats['within_brief']=within
# win analysis
ranked=sorted(ids,key=lambda b:(-sc[b],b));top=ranked[:15]
stats['win_rate_r1_imajev']=round(float(np.mean([sc[b]>.5 for b in ids])),3)
def dd(pa,pb,f):return round(float(np.mean([I[pa][b][f]-I[pb][b][f] for b in ids])),3)
dw=[I['r1'][b]['words']-I['base'][b]['words'] for b in ids];m=[sc[b] for b in ids]
stats['corr_margin_vs_words_delta']=round(float(np.corrcoef(dw,m)[0,1]),3)
stats['corr_margin_vs_len_delta']=round(float(np.corrcoef([I['r1'][b]['len']-I['base'][b]['len'] for b in ids],m)[0,1]),3)
stats['top15']={'ids':top,'margin':{b:round(sc[b]-.5,3) for b in top},'agg':{pol:{k:round(float(np.mean([I[pol][b][k] for b in top])),3) for k in['len','words','secs_frac','imgs','ext_imgs','hero100vh','grad','svg','welcome','trust','praise']} for pol in I}}
# r1 wins by whether hero hue is purple-blue p6a11cb
stats['win_by_p6a11cb']={str(v):[round(float(np.mean([sc[b]>.5 for b in ids if I['r1'][b]['p6a11cb']==v])),3),sum(I['r1'][b]['p6a11cb']==v for b in ids)] for v in(True,False)}
# contact sheet
cs=random.Random(1).sample(ids,12)
W,H=320,200;sheet=Image.new('RGB',(W*2+30,(H+4)*12//1//1),'white')
sheet=Image.new('RGB',(2*W*2+30,(H+6)*6),'white')
for n,b in enumerate(cs):
    col=n%2;row=n//2
    for k,pol in enumerate(('base','r1')):
        im=Image.open(PATH[pol].format(b=b)+'.png').convert('RGB').resize((W,H));sheet.paste(im,(col*(2*W+30)+k*W,row*(H+6)))
sheet.save(OUT+'contact_sheet.png')
stats['contact_ids']=cs
json.dump(stats,open(OUT+'audit_stats.json','w'),indent=1,default=str)
print(json.dumps({k:v for k,v in stats.items() if k!='top15'},indent=0,default=str))
print(json.dumps(stats['top15'],default=str))
