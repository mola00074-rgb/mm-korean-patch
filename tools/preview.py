import sys,re,pickle,struct
sys.path.insert(0,'.')
import build_data as b, mmtext, tags, krfont, widths
from PIL import Image, ImageDraw
nes=open(mmtext.DEC+'/extracted/n64-us/baserom/nes_font_static','rb').read()
final,errs=b.process(b.load_ko())
msgs={m['id']:m for m in pickle.load(open('msgs.pkl','rb'))}
COL={1:(255,60,60),2:(70,255,70),3:(80,80,255),4:(255,255,60),5:(120,200,255),6:(255,120,255),7:(200,200,200),8:(255,160,60),0:(255,255,255)}
gcache={}
def glyph(c):
    if c not in gcache: gcache[c]=krfont.render(c)
    return gcache[c]
def blit(img,g,x,y,col):
    for yy in range(16):
        for xx in range(16):
            bb=g[yy*8+xx//2]; v=(bb>>4) if xx%2==0 else bb&15
            if v:
                X,Y=x+xx,y+yy
                if 0<=X<img.width and 0<=Y<img.height:
                    a=v/15; p=img.getpixel((X,Y)); img.putpixel((X,Y),tuple(int(p[i]*(1-a)+col[i]*a) for i in range(3)))
def render_msg(tid):
    m=msgs[tid]; s=final[tid].replace('…','...')
    toks=tags.from_tagged(s,m['toks'][0][1])
    glyphs={}
    def kr(c):
        if c not in glyphs: glyphs[c]=len(glyphs)
        return glyphs[c]
    data,pos=mmtext.encode(dict(toks=toks),kr)
    inv={v:k for k,v in glyphs.items()}; pmap={p:inv[g] for p,g in pos}
    # simulate at 4x supersample: game px = texels*0.75 ; we draw at 1 texel per px then scale
    boxes=[];cur=[];
    i=11; col=0; x=0; line=0; img=None
    W,H=int(256/0.75)+20,4*16+10
    def newbox():
        im=Image.new('RGB',(W,H),(30,30,60)); return im
    img=newbox(); y=4
    BOXEND={0x10,0x12,0x1B,0x1C,0x1D,0x19,0xE0,0xBF,0x15,0x1A}
    while i<len(data):
        c=data[i]
        if c in BOXEND:
            boxes.append(img); 
            if c==0xBF: break
            img=newbox(); x=0; y=4
            i+= 3 if c in (0x1B,0x1C,0x1D) else 1; continue
        if c<=8: col=c; i+=1; continue
        if c in (0x11,0x13): x=0; y+=16; i+=1; continue  # 12px line spacing *(1/0.75)=16
        if c in (0x1E,0x1F,0x1B): i+=3; continue
        if c==0x14: i+=2; continue
        if c==0x20: x+=6/0.75; i+=1; continue
        if c in (0x17,0x18,0x0A,0x16,0xC2,0xC3) or (0xC1<=c<=0xFF and c!=0xBF): i+=1; continue
        if i in pmap:
            blit(img,glyph(pmap[i]),int(x),y,COL.get(col,(255,255,255))); x+=int(15*0.75)/0.75
        else:
            g=nes[(c-0x20)*128:(c-0x1F)*128]; blit(img,g,int(x),y,COL.get(col,(255,255,255))); x+=int(widths.W[c-0x20]*0.75)/0.75
        i+=1
    return boxes
ids=[int(a,16) for a in sys.argv[1:]]
allb=[]
for t in ids: allb+= render_msg(t)
W=allb[0].width; H=sum(b.height+4 for b in allb)
out=Image.new('RGB',(W,H),(0,0,0)); yy=0
for bx in allb: out.paste(bx,(0,yy)); yy+=bx.height+4
out=out.resize((W*2,H*2),Image.BILINEAR); out.save('preview.png'); print(len(allb),'boxes')
