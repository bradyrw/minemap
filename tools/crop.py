import sys, numpy as np, cv2
from PIL import Image
def beige_mask(a):
    r,g,b=[a[...,i].astype(int) for i in range(3)]
    return (r>130)&(r<235)&(g>110)&(g<210)&(b>70)&(b<160)&(r-b>45)&(r-g>5)&(r-g<40)&(abs((r-g)-(g-b))<25)
def crop(path):
    im=Image.open(path).convert('RGB'); a=np.array(im); H,W=a.shape[:2]
    m=beige_mask(a)
    cy,cx=H//2,W//2
    # scan outward along center row/col for first solid beige run (>=8px)
    def scan(line, start, step):
        i=start; run=0
        while 0<=i<len(line):
            run = run+1 if line[i] else 0
            if run>=8: return i-run+1
            i+=step
        return None
    row=m[cy]; col=m[:,cx]
    # use multiple rows/cols and take median
    L=[];R=[];T=[];B=[]
    for d in range(-int(H*0.3),int(H*0.3),12):
        if not (0<=cy+d<H and 0<=cx+d<W): continue
        rr=m[cy+d]; cc=m[:,cx+d]
        l=scan(rr,cx+d,-1); r=scan(rr,cx+d,1); t=scan(cc,cy+d,-1); b=scan(cc,cy+d,1)
        if l is not None: L.append(l)
        if r is not None: R.append(r)
        if t is not None: T.append(t)
        if b is not None: B.append(b)
    l,r,t,b=[int(np.median(x)) if x else -1 for x in (L,R,T,B)]
    return im, (l+1,t+1,r,b)
if __name__=='__main__':
    for p in sys.argv[1:]:
        im,box=crop(p); print(p.split('/')[-1], box, box[2]-box[0], box[3]-box[1])

def loose(a):
    r,g,b=[a[...,i].astype(int) for i in range(3)]
    beige=(r>120)&(g>100)&(b>60)&(r-b>35)&(r-b<110)&(r-g>5)&(r-g<45)
    dark=(r<60)&(g<60)&(b<60)
    gray=(abs(r-g)<12)&(abs(g-b)<12)&(r>60)&(r<200)
    return beige|dark|gray
def crop2(path):
    im,(l,t,r,b)=crop(path); a=np.array(im); H,W=a.shape[:2]
    if r<0: r=W-15
    w=r-l; b=min(H-1,t+w)
    m=loose(a)
    def trim(line_fn, i, step, limit):
        while 0<=i<limit and line_fn(i)>0.6: i+=step
        return i
    t2=trim(lambda y: m[y,l:r].mean(), t, 1, H)
    l2=trim(lambda x: m[t2:b,x].mean(), l, 1, W)
    r2=trim(lambda x: m[t2:b,x].mean(), r-1, -1, W)+1
    w=r2-l2; b2=t2+w
    return im,(l2,t2,r2,b2)
