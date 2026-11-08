import re, struct
import os
DEC=os.environ.get('MM_DECOMP',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','mm-decomp'))
CODES={}
for line in open(DEC+'/include/message_data_fmt_nes.h'):
    m=re.match(r'#define MESSAGE_(\w+) (0x[0-9A-F]+)',line)
    if m: CODES[m.group(1)]=int(m.group(2),16)
ARGS={'SHIFT':1,'BOX_BREAK_DELAYED':2,'FADE':2,'FADE_SKIPPABLE':2,'SFX':2,'DELAY':2}
SPECIAL={'[A]':0xB0,'[B]':0xB1,'[C]':0xB2,'[L]':0xB3,'[R]':0xB4,'[Z]':0xB5,'[C-Up]':0xB6,'[C-Down]':0xB7,'[C-Left]':0xB8,'[C-Right]':0xB9,'▼':0xBA,'[Control-Pad]':0xBB}
SPECIAL_RE=re.compile('|'.join(re.escape(k) for k in sorted(SPECIAL,key=len,reverse=True)))

SFX={}
import glob
for f in glob.glob(DEC+'/include/tables/sfx/*.h'):
    for line in open(f):
        m=re.match(r'/\* (0x[0-9A-F]+) \*/ DEFINE_SFX\(\w+, (\w+)',line)
        if m: SFX[m.group(2)]=int(m.group(1),16)
SFX['SFX_FLAG']=0x800
ARGNAMES={}
def evalarg(a):
    v=eval(a,{},SFX); ARGNAMES[v]=a.strip(); return v
def unescape(s):
    out=[];i=0
    while i<len(s):
        c=s[i]
        if c=='\\':
            n=s[i+1]
            if n=='n': out.append('\n'); i+=2
            elif n=='"': out.append('"'); i+=2
            elif n=='\\': out.append('\\'); i+=2
            elif n=='x':
                m=re.match(r'[0-9A-Fa-f]{1,2}',s[i+2:]); out.append(chr(int(m.group(0),16))); i+=2+len(m.group(0))
            else: raise ValueError(s)
        else: out.append(c); i+=1
    return ''.join(out)

def parse(path=DEC+'/extracted/n64-us/text/message_data.h'):
    src=open(path,encoding='utf-8').read()
    msgs=[]
    for m in re.finditer(r'DEFINE_MESSAGE\((0x[0-9A-F]+), (0x[0-9A-F]+), (0x[0-9A-F]+),\s*MSG\((.*?)\n\)\n\)',src,re.S):
        tid=int(m.group(1),16); body=m.group(4)
        toks=[]  # ('H',tuple) ('T',str) ('C',name,arg)
        for t in re.finditer(r'"((?:[^"\\]|\\.)*)"|([A-Z_][A-Z0-9_]*)(?:\(([^)]*)\))?',body):
            if t.group(1) is not None: toks.append(('T',unescape(t.group(1))))
            elif t.group(2)=='HEADER': toks.append(('H',tuple(int(x,0) for x in t.group(3).split(','))))
            else: toks.append(('C',t.group(2),evalarg(t.group(3)) if t.group(3) else None))
        msgs.append(dict(id=tid,type=int(m.group(2),16),pos=int(m.group(3),16),toks=toks))
    return msgs

def enc_text(s, kr=None):
    b=bytearray(); krpos=[]
    i=0
    while i<len(s):
        m=SPECIAL_RE.match(s,i)
        if m: b.append(SPECIAL[m.group(0)]); i=m.end(); continue
        c=s[i]
        if c=='\n': b.append(0x11)
        elif 0xAC00<=ord(c)<=0xD7A3:
            if kr is None: raise ValueError('hangul without kr map')
            krpos.append((len(b),kr(c))); b.append(KR_PLACEHOLDER)
        else:
            o=ord(c)
            if o in CHARX: o=CHARX[o]
            if o>0xFF: raise ValueError('bad char %r in %r'%(c,s))
            b.append(o)
        i+=1
    return b,krpos
KR_PLACEHOLDER=0x80
CHARX={}
def encode(msg, kr=None):
    b=bytearray(); pos=[]
    for t in msg['toks']:
        if t[0]=='H':
            h=t[1]; b+=struct.pack('>HBHHHH',*h)
        elif t[0]=='T':
            eb,kp=enc_text(t[1],kr); pos+=[(p+len(b),g) for p,g in kp]; b+=eb
        else:
            name,arg=t[1],t[2]; b.append(CODES[name])
            n=ARGS.get(name,0)
            if n==1: b.append(arg&0xFF)
            elif n==2: b+=struct.pack('>H',arg&0xFFFF)
            else: assert arg is None,(name,arg)
    b.append(CODES['END'])
    return b,pos
