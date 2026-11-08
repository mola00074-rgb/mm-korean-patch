import sys; sys.path.insert(0,'.')
import mmtext,struct,pickle
msgs=mmtext.parse()
seg=open(mmtext.DEC+'/extracted/n64-us/baserom/message_data_static','rb').read()
code=open(mmtext.DEC+'/extracted/n64-us/baserom/code','rb').read()
idx=-1
for i in range(0,len(code)-16,4):
    if code[i:i+2]==b'\0\0' and code[i+4:i+8]==b'\x08\0\0\0' and code[i+8:i+10]==b'\0\x02':
        idx=i;break
print('table at',hex(idx))
tab=[];i=idx
while True:
    tid,tp,_,ptr=struct.unpack('>HBBI',code[i:i+8]); tab.append((tid,tp,ptr)); i+=8
    if tid==0xFFFF: break
print(len(tab),len(msgs))
bad=0
for k,m in enumerate(msgs):
    tid,tp,ptr=tab[k]; nxt=tab[k+1][2]
    assert tid==m['id']
    b,_=mmtext.encode(m)
    o=ptr-0x08000000; m['off']=o; m['origlen']=nxt-ptr
    if seg[o:o+len(b)]!=b:
        bad+=1
        if bad<4: print('mismatch',hex(tid),seg[o:o+len(b)].hex(),b.hex())
print('bad',bad, 'maxlen',max(m['origlen'] for m in msgs))
pickle.dump(msgs,open('msgs.pkl','wb'))
