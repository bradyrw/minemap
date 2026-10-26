import cv2, numpy as np, glob, os, json, sys
A='/mnt/user-data/attachments/ba6c1b57-38dc-5687-ab7c-fd489399e74a/'
REFS={A+'934ff835-image.png':'Position: -2025, 102, -2014', A+'c18a42d0-image.png':'Position: -258, 89, -256', A+'ab40235f-image.png':'Position: -1739, 109, -524', A+'6c60bc77-image.png':'Position: -22, 51, -243', A+'43f6f8f5-image.png':'Position: -133, 62, -152'}
def line_img(path):
    im=cv2.imread(path); H,W=im.shape[:2]; s=W/2868
    crop=im[int(190*s):int(290*s), int(130*s):int(1000*s)]
    if s!=1: crop=cv2.resize(crop,None,fx=1/s,fy=1/s,interpolation=cv2.INTER_CUBIC)
    g=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
    return (g>215).astype(np.uint8)
def glyphs(b):
    rows=np.nonzero(b.sum(1))[0]
    if len(rows)==0: return []
    y0,y1=rows.min(),rows.max()+1; b=b[y0:y1]
    cols=b.sum(0)>0; out=[]; x=0
    while x<b.shape[1]:
        if cols[x]:
            x1=x
            while x1<b.shape[1] and cols[x1]: x1+=1
            out.append((x,x1,b[:,x:x1])); x=x1
        else: x+=1
    return out
def norm(g): 
    ys=np.nonzero(g.sum(1))[0]; g=g[ys.min():ys.max()+1]
    return cv2.resize(g.astype(np.float32),(12,16),interpolation=cv2.INTER_AREA)
T={}
for p,s in REFS.items():
    gs=glyphs(line_img(p)); chars=[c for c in s if c!=' ']
    if len(gs)!=len(chars): print('ref mismatch',os.path.basename(p),len(gs),len(chars)); continue
    for (x0,x1,g),c in zip(gs,chars): T.setdefault(c,[]).append(norm(g))
print('templates for', ''.join(sorted(T)))
def read(path):
    b=line_img(path); gs=glyphs(b)
    if len(gs)<10: return None
    out=''; lastx=None
    for x0,x1,g in gs:
        if lastx is not None and x0-lastx>7: out+=' '
        n=norm(g); best=max(T,key=lambda c:max(float((n*t).sum()/(np.sqrt((n*n).sum()*(t*t).sum())+1e-6)) for t in T[c])); out+=best; lastx=x1
    return out
if __name__=='__main__':
    import re
    res={}
    for p in sorted(glob.glob('/home/claude/shots/*'))+sorted(glob.glob(A+'*.png')):
        im=cv2.imread(p)
        if im.shape[1]<1900: continue
        r=read(p); m=re.search(r'(-?\d+), (-?\d+), (-?\d+)',r or '')
        res[os.path.basename(p)]=[int(v) for v in m.groups()] if m else None
        print(os.path.basename(p), r, '->', res[os.path.basename(p)])
    json.dump(res,open('/home/claude/poi/coords.json','w'),indent=1)
