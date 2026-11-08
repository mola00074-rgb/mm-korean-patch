import sys;sys.path.insert(0,'.')
import pickle,tags,re,os,json
msgs=pickle.load(open('msgs.pkl','rb'))
os.makedirs('en',exist_ok=True)
seen={}; todo=[]; dup={}; skip=[]
for m in msgs:
    s=tags.to_tagged(m)
    if not re.search('[A-Za-z]',re.sub(r'\{[^}]*\}|\[[^\]]*\]','',s)): skip.append(m['id']); continue
    if s in seen: dup[m['id']]=seen[s]; continue
    seen[s]=m['id']; todo.append((m['id'],s))
print(len(todo),'unique',len(dup),'dups',len(skip),'skip', sum(len(s) for _,s in todo))
json.dump({'dup':dup,'skip':skip},open('meta.json','w'))
batches=[];cur=[];n=0
for tid,s in todo:
    cur.append((tid,s)); n+=len(s)
    if n>9000: batches.append(cur); cur=[]; n=0
if cur: batches.append(cur)
for i,b in enumerate(batches):
    with open('en/b%02d.txt'%i,'w') as f:
        for tid,s in b: f.write('@%04X\n%s\n'%(tid,s))
print(len(batches),'batches')
