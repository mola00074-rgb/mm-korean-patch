import sys,os,re,json,pickle,glob
sys.path.insert(0,os.path.dirname(__file__))
import mmtext,tags,widths,krfont
msgs=pickle.load(open('msgs.pkl','rb'))
meta=json.load(open('meta.json'))
byid={m['id']:m for m in msgs}
KR_ADV=15.0
SCALE=0.75
def px_char(c):
    if c==' ': return 6
    if '가'<=c<='힣': return int(KR_ADV*SCALE)
    if c in KOR_PUNCT: c=KOR_PUNCT[c]
    o=ord(c)
    if o<0x20 or o>0xBF: raise ValueError('char %r'%c)
    return widths.charpx(o)
KOR_PUNCT={'…':'...'}
TAGPX={'name':48,'BOMBER_CODE':40,'RUPEES_TOTAL':24,'RUPEES_SELECTED':24,'STRAY_FAIRIES':24,'TOKENS':24,'HOURS_UNTIL_MOON_CRASH':24,'TIME_UNTIL_MOON_CRASH':50,'TIME_UNTIL_NEW_DAY':50}
BTN={'[A]','[B]','[C]','[L]','[R]','[Z]','[C-Up]','[C-Down]','[C-Left]','[C-Right]','▼','[Control-Pad]'}
TOKRE=re.compile(r'\{[^}]*\}|\[(?:A|B|C|L|R|Z|C-Up|C-Down|C-Left|C-Right|Control-Pad)\]|\n|.',re.S)
BOXRE=re.compile(r'\{(?:BOX|BOX2|EV|EV2|CONT|PERS)\}|\{(?:BOXD|FADE|FADES):[0-9A-Fa-f]+\}')
def tok_px(t):
    if t.startswith('{'):
        n=t[1:-1].split(':')[0]
        return TAGPX.get(n, 24 if n.isupper() and n not in tags.BOXEND else 0)
    if t in BTN or t=='▼': return 10
    return px_char(t)
def limit_for(m):
    h=m['toks'][0][1]; typ=(h[0]>>8)&0xF
    if typ==0xC: return 137
    return 188
def split_boxes(s):
    parts=[];pos=0
    for mm in BOXRE.finditer(s):
        parts.append((s[pos:mm.start()],mm.group(0))); pos=mm.end()
    parts.append((s[pos:],''))
    return parts
def norm(s):
    s=s.replace('…','...')
    s=re.sub(r'(\{(?:BOX|BOX2|EV|EV2|CONT|PERS)\}|\{(?:BOXD|FADE|FADES):[0-9A-Fa-f]+\})\n',r'\1',s)
    return s
def wrap_box(text,limit,errs,tid,allow_wrap=True):
    lines=re.split(r'(\n|\{cr\})',text)
    out=[]
    for i in range(0,len(lines),2):
        line=lines[i]; sep=lines[i+1] if i+1<len(lines) else ''
        toks=TOKRE.findall(line)
        cur=[];w=0;res=[]
        for t in toks:
            tw=tok_px(t)
            if w+tw>limit and allow_wrap and t!=' ':
                # break at last space in cur
                sp=max((k for k,x in enumerate(cur) if x==' '),default=-1)
                if sp>0:
                    res.append(''.join(cur[:sp])); cur=cur[sp+1:]
                else:
                    res.append(''.join(cur)); cur=[]
                w=sum(tok_px(x) for x in cur)
            cur.append(t); w+=tw
        res.append(''.join(cur))
        res=[r.rstrip(' ') if k<len(res)-1 else r for k,r in enumerate(res)]
        out.append('\n'.join(res)+sep)
    return ''.join(out)
def count_lines(text):
    # count visible lines: newlines + 1 ignoring a trailing empty line created by tags only
    segs=re.split(r'\n|\{cr\}',text)
    while len(segs)>1 and re.sub(r'\{[^}]*\}','',segs[-1]).strip()=='' and not re.search(r'\{(2c|3c)\}',segs[-1]): segs.pop()
    return len(segs)
def struct_seq(s):
    seq=[]
    for t in re.findall(r'\{[^}]*\}|\[(?:A|B|C|L|R|Z|C-Up|C-Down|C-Left|C-Right|Control-Pad)\]',s):
        n=t[1:-1].split(':')[0] if t.startswith('{') else t
        if n in ('w','r','g','b','y','lb','p','s','o','cr','d'): continue
        if t.startswith('['): continue
        seq.append(t)
    return seq
def load_ko():
    ko={}
    for f in sorted(glob.glob('ko/*.txt')):
        cur=None;buf=[]
        for line in open(f,encoding='utf-8').read().split('\n'):
            if re.match(r'^@[0-9A-F]{4}$',line):
                if cur is not None: ko[cur]='\n'.join(buf).rstrip('\n')
                cur=int(line[1:],16); buf=[]
            elif cur is not None: buf.append(line)
        if cur is not None: ko[cur]='\n'.join(buf).rstrip('\n')
    return ko
def process(ko, report=True):
    errs=[]; final={}
    for tid,s in ko.items():
        m=byid.get(tid)
        if m is None: errs.append((tid,'unknown id')); continue
        en=tags.to_tagged(m)
        s=norm(s)
        if struct_seq(en)!=struct_seq(s):
            errs.append((tid,'struct mismatch: en=%s ko=%s'%(struct_seq(en),struct_seq(s)))); continue
        lim=limit_for(m)
        enb=split_boxes(norm(en)); kob=split_boxes(s)
        outs=[]
        for (et,eend),(kt,kend) in zip(enb,kob):
            choice=bool(re.search(r'\{(2c|3c)\}',kt))
            if choice:
                w=kt
                for line in re.split(r'\n|\{cr\}',kt):
                    if sum(tok_px(t) for t in TOKRE.findall(line))>lim+4: errs.append((tid,'choice line too long: '+line))
                if count_lines(kt)!=count_lines(et): errs.append((tid,'choice box line count %d!=%d'%(count_lines(kt),count_lines(et))))
            else:
                w=wrap_box(kt,lim,errs,tid)
            n=count_lines(w)
            if n>4: errs.append((tid,'box has %d lines: %r'%(n,w)))
            outs.append(w+kend)
        final[tid]=''.join(outs)
    return final,errs
def bad_chars(s):
    out=set()
    for c in re.sub(r'\{[^}]*\}|\[(?:A|B|C|L|R|Z|C-Up|C-Down|C-Left|C-Right|Control-Pad)\]','',s):
        if c=='\n' or '가'<=c<='힣' or c in KOR_PUNCT: continue
        if not (0x20<=ord(c)<=0x7E): out.add(c)
    return out
if __name__=='__main__':
    ko=load_ko()
    for d,src in meta['dup'].items():
        if src in ko and int(d) not in ko: ko[int(d)]=ko[src]
    final,errs=process(ko)
    for tid,s in final.items():
        b=bad_chars(s)
        if b: errs.append((tid,'bad chars %r'%b))
    for e in errs: print('%04X'%e[0],e[1])
    print('translated',len(final),'/',len(msgs),'errors',len(errs))
    if '--gen' in sys.argv and not errs:
        import gen_c; gen_c.generate(final)
