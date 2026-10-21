"""Career-table wikitext parser, copied verbatim from DraftDB-Data/traj_features.py (project code) so this collector is self-contained."""
import json,re,glob,csv,unicodedata,collections
def norm(s): return re.sub(r"[^a-z0-9 %.]","",unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()).strip()
def clean_cell(c):
    c=c.strip(); c=re.sub(r'^(?:[a-zA-Z]+\s*=\s*"[^"]*"\s*)+\|','',c); c=re.sub(r'^(?:[a-zA-Z]+\s*=\s*[^\s|]+\s*)+\|','',c)
    c=re.sub(r"\{\{[Tt]ooltip\|([^|}]*)\|[^}]*\}\}",r"\1",c); c=re.sub(r"\{\{[Aa]bbr\|([^|}]*)\|[^}]*\}\}",r"\1",c)
    c=re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]",r"\1",c); c=re.sub(r"\{\{[^{}]*\}\}","",c); c=re.sub(r"<ref.*?(/>|</ref>)","",c,flags=re.S); c=re.sub(r"<[^>]+>","",c)
    return c.replace("'''","").replace("''","").strip()
HMAP={"year":"year","season":"year","team":"team","club":"team","league":"league","gp":"gp","g":"gp","gs":"gs","mpg":"mpg","min":"mpg","fg%":"fg%","fg":"fg%","3p%":"3p%","3pt%":"3p%","ft%":"ft%","rpg":"rpg","reb":"rpg","apg":"apg","ast":"apg","spg":"spg","stl":"spg","bpg":"bpg","blk":"bpg","ppg":"ppg","pts":"ppg"}
NUM=("gp","gs","mpg","fg%","3p%","ft%","rpg","apg","spg","bpg","ppg")
def fnum(v):
    v=re.sub(r"[†‡*%]","",v or "").replace(",",".").strip(); m=re.search(r"-?\d*\.?\d+",v); return float(m.group(0)) if m else None
def parse_year(y):
    y=re.sub(r"\[.*?\]|[†‡*]","",y or "").strip(); m=re.search(r"(\d{4})\s*[–\-−/]\s*(\d{2,4})",y)
    if m:
        a=int(m.group(1)); b=m.group(2); e=int(b) if len(b)==4 else a//100*100+int(b)
        if e<a: e+=100
        return e if e-a<=1 else a+1
    m=re.search(r"^(\d{4})$",y); return int(m.group(1)) if m else None
STD=["year","team","gp","gs","mpg","fg%","3p%","ft%","rpg","apg","spg","bpg","ppg"]
def year_of(cell):
    m=re.search(r"\{\{nbay\|(\d{4})",cell)
    if m: return int(m.group(1))+1
    return parse_year(clean_cell(cell))
def rows_from(wt):
    out=[]; head=""; intable=False; hdr=None; block=[]
    def flush():
        nonlocal block
        if not block: return
        cells=[]
        for l in block:
            l=l.strip()
            if l.startswith("!"): cells+=[("h",c) for c in re.split(r"!!",l[1:])]
            elif l.startswith("|") and not l.startswith("|}"): cells+=[("d",c) for c in re.split(r"\|\|",l[1:])]
        block=[]
        if not cells: return
        if all(t=="h" for t,_ in cells):
            keys=[HMAP.get(norm(clean_cell(c)).replace(" ",""),None) for _,c in cells]
            if "gp" in keys and "ppg" in keys: hdr[:]=[keys]
            return
        raw=[c for _,c in cells]
        if re.search(r"career|total",norm(clean_cell(raw[0]))) or any("sortbottom" in c for c in raw[:1]): return
        yr=year_of(raw[0])
        if yr is None: return
        r=dict(section=head,end=yr,team="",league="")
        keys=hdr[0] if hdr and hdr[0] else STD
        if keys is STD:
            nums=[fnum(clean_cell(c)) for c in raw[1:]]
            texts=[clean_cell(c) for c in raw[1:] if fnum(clean_cell(c)) is None or re.search(r"[A-Za-z]{3}",clean_cell(c))]
            r["team"]=texts[0] if texts else ""; vals=[v for c,v in zip(raw[1:],nums) if not re.search(r"[A-Za-z]{3}",clean_cell(c))]
            names=["gp","gs","mpg","fg%","3p%","ft%","rpg","apg","spg","bpg","ppg"] if len(vals)>=11 else ["gp","mpg","fg%","3p%","ft%","rpg","apg","spg","bpg","ppg"]
            for k,v in zip(names,vals): r[k]=v
        else:
            vals=[clean_cell(c) for c in raw]
            for k,i in {k:i for i,k in enumerate(keys) if k}.items():
                if i<len(vals):
                    if k in("team","league"): r[k]=vals[i]
                    elif k!="year": r[k]=fnum(vals[i])
        if r.get("gp"): out.append(r)
    for line in wt.split("\n"):
        s=line.strip()
        m=re.match(r"^(==+)\s*(.*?)\s*==+\s*$",s)
        if m: flush(); head=m.group(2); intable=False; hdr=None; continue
        if re.search(r"\{\{[^{}]*statistics start",s,re.I) or s.startswith("{|"):
            flush(); intable=True; hdr=[None]; continue
        if not intable: continue
        if s.startswith("{{S-end}}") or s.startswith("{{end}}") or s.startswith("|}"): flush(); intable=False; hdr=None; continue
        if s.startswith("|-"): flush(); continue
        block.append(line)
    flush(); return out
