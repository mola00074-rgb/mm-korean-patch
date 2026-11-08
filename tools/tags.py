import re, mmtext
COL={'COLOR_DEFAULT':'w','COLOR_RED':'r','COLOR_GREEN':'g','COLOR_BLUE':'b','COLOR_YELLOW':'y','COLOR_LIGHTBLUE':'lb','COLOR_PINK':'p','COLOR_SILVER':'s','COLOR_ORANGE':'o'}
SIMPLE={'QUICKTEXT_ENABLE':'qt','QUICKTEXT_DISABLE':'/qt','CARRIAGE_RETURN':'cr','NAME':'name','TWO_CHOICE':'2c','THREE_CHOICE':'3c',
        'BOX_BREAK':'BOX','BOX_BREAK2':'BOX2','EVENT':'EV','EVENT2':'EV2','CONTINUE':'CONT','PERSISTENT':'PERS'}
ARGT={'DELAY':'d','SFX':'sfx','SHIFT':'sh','BOX_BREAK_DELAYED':'BOXD','FADE':'FADE','FADE_SKIPPABLE':'FADES'}
BOXEND={'BOX','BOX2','EV','EV2','CONT','PERS','BOXD','FADE','FADES'}
R={}
for k,v in COL.items(): R[v]=k
for k,v in SIMPLE.items(): R[v]=k
RA={v:k for k,v in ARGT.items()}
def to_tagged(msg):
    out=[]
    for t in msg['toks']:
        if t[0]=='H': continue
        if t[0]=='T': out.append(t[1].replace('{','(').replace('}',')'))
        else:
            n,a=t[1],t[2]
            if n in COL: out.append('{'+COL[n]+'}')
            elif n in SIMPLE: out.append('{'+SIMPLE[n]+'}')
            elif n in ARGT: out.append('{%s:%X}'%(ARGT[n],a))
            else: out.append('{%s}'%n)
    s=''.join(out)
    # box ends followed by newline for readability
    s=re.sub(r'(\{(?:BOX|BOX2|EV|EV2|CONT|PERS)\}|\{(?:BOXD|FADE|FADES):[0-9A-F]+\})',r'\1\n',s)
    return s.rstrip('\n')
TAG_RE=re.compile(r'\{([A-Za-z0-9_/]+)(?::([0-9A-Fa-f]+))?\}')
def from_tagged(s, header):
    # newline right after box end tags is cosmetic
    s=re.sub(r'(\{(?:BOX|BOX2|EV|EV2|CONT|PERS)\}|\{(?:BOXD|FADE|FADES):[0-9A-Fa-f]+\})\n',r'\1',s)
    toks=[('H',header)]
    pos=0
    for m in TAG_RE.finditer(s):
        if m.start()>pos: toks.append(('T',s[pos:m.start()]))
        name,arg=m.group(1),m.group(2)
        if name in R: toks.append(('C',R[name],None))
        elif name in RA: toks.append(('C',RA[name],int(arg,16)))
        elif name in mmtext.CODES: toks.append(('C',name,None))
        else: raise ValueError('unknown tag '+m.group(0))
        pos=m.end()
    if pos<len(s): toks.append(('T',s[pos:]))
    return toks
