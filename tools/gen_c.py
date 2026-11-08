import re,os,pickle
import mmtext,tags,krfont
import os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src')
def generate(final):
    msgs=pickle.load(open('msgs.pkl','rb'))
    byid={m['id']:m for m in msgs}
    glyphs={}
    def kr(c):
        if c not in glyphs: glyphs[c]=len(glyphs)
        return glyphs[c]
    entries=[]; blob=bytearray(); pos=[]
    for m in sorted(msgs,key=lambda m:m['off']):
        if m['id'] not in final: continue
        h=m['toks'][0][1]
        s=final[m['id']].replace('…','...')
        toks=tags.from_tagged(s,h)
        b,p=mmtext.encode(dict(toks=toks),kr)
        assert len(b)<=1280,(hex(m['id']),len(b))
        entries.append((m['off'],len(blob),len(b),len(p),len(pos)))
        blob+=b; pos+=p
        while len(blob)%4: blob.append(0)
    chars=sorted(glyphs,key=lambda c:glyphs[c])
    with open(OUT+'/kr_data.h','w') as f:
        f.write('''#ifndef KR_DATA_H
#define KR_DATA_H
#include "PR/ultratypes.h"
#define KR_PLACEHOLDER 0x%02X
#define KR_ADVANCE 15.0f
#define KR_MSG_COUNT %d
#define KR_GLYPH_COUNT %d
typedef struct { u32 orig_off; u32 data_off; u16 len; u16 npos; u32 pos_off; } KrMsgEntry;
typedef struct { u16 pos; u16 glyph; } KrGlyphPos;
extern const KrMsgEntry kr_msg_table[KR_MSG_COUNT];
extern const u8 kr_msg_blob[];
extern const KrGlyphPos kr_glyph_pos[];
extern const u8 kr_glyphs[KR_GLYPH_COUNT][128];
#endif
'''%(mmtext.KR_PLACEHOLDER,len(entries),len(chars)))
    with open(OUT+'/kr_data.c','w') as f:
        f.write('#include "kr_data.h"\n\n')
        f.write('const KrMsgEntry kr_msg_table[KR_MSG_COUNT] = {\n')
        for e in entries: f.write('    { 0x%X, 0x%X, %d, %d, %d },\n'%e)
        f.write('};\n\n__attribute__((aligned(16))) const u8 kr_msg_blob[%d] = {\n'%len(blob))
        for i in range(0,len(blob),32): f.write('    '+','.join('0x%02X'%x for x in blob[i:i+32])+',\n')
        f.write('};\n\nconst KrGlyphPos kr_glyph_pos[%d] = {\n'%max(1,len(pos)))
        for i in range(0,len(pos),8): f.write('    '+' '.join('{%d,%d},'%x for x in pos[i:i+8])+'\n')
        if not pos: f.write('{0,0}\n')
        f.write('};\n\n__attribute__((aligned(16))) const u8 kr_glyphs[KR_GLYPH_COUNT][128] = {\n')
        for c in chars:
            g=krfont.render(c)
            f.write('    /* %s */ {'%c+','.join('0x%02X'%x for x in g)+'},\n')
        f.write('};\n')
    open(OUT+'/../glyphs.txt','w').write(''.join(chars))
    print('generated: %d msgs, %d glyphs, blob %d bytes'%(len(entries),len(chars),len(blob)))
