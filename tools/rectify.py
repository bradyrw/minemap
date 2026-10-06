import numpy as np, cv2, glob, json, sys
from PIL import Image
from crop import crop2, loose
def fit_line(pts):
    pts=np.array(pts,float)
    if len(pts)<10: return None
    best=None
    for _ in range(200):
        i,j=np.random.choice(len(pts),2,replace=False); p,q=pts[i],pts[j]
        d=q-p; n=np.linalg.norm(d)
        if n<1: continue
        nrm=np.array([-d[1],d[0]])/n; dist=np.abs((pts-p)@nrm)
        inl=dist<2.0
        if best is None or inl.sum()>best[0]: best=(inl.sum(),inl)
    inl=pts[best[1]]
    # total least squares
    c=inl.mean(0); u,s,vt=np.linalg.svd(inl-c); d=vt[0]
    return c,d
def inter(l1,l2):
    c1,d1=l1;c2,d2=l2; A=np.array([d1,-d2]).T; t=np.linalg.solve(A,c2-c1); return c1+t[0]*d1
def edge_points(m,side,l,t,r,b,H,W):
    pts=[]
    if side in('left','right'):
        for y in range(int(t+(b-t)*0.08),int(b-(b-t)*0.12),6):
            if side=='left':
                xs=range(max(0,l-50),min(W,l+60))
            else:
                xs=range(min(W-1,r+50),max(0,r-60),-1)
            run=0
            for x in xs:
                run=0 if m[y,x] else run+1
                if run>=3: pts.append((x-2,y)); break
    else:
        for x in range(int(l+(r-l)*0.05),int(r-(r-l)*0.05),6):
            if side=='top' and (r-l)*0.28+l < x < (r-l)*0.72+l: continue   # HUD icons
            if side=='bottom' and (r-l)*0.45+l < x < (r-l)*0.6+l: continue # XP number
            ys=range(max(0,t-50),min(H,t+60)) if side=='top' else range(min(H-1,b+40),max(0,b-60),-1)
            run=0
            for y in ys:
                run=0 if m[y,x] else run+1
                if run>=3: pts.append((x,y-2 if side=='top' else y+2)); break
    return pts
def beige(a):
    r,g,b=[a[...,i].astype(int) for i in range(3)]
    return (r>150)&(g>130)&(b>80)&(r-b>40)&(r-b<110)&(r-g>5)&(r-g<45)
def bottom_points(a,l,t,r,b):
    m=beige(a); H=a.shape[0]
    cols=np.r_[int(l+(r-l)*0.1):int(l+(r-l)*0.42), int(l+(r-l)*0.62):int(r-(r-l)*0.1)]
    fr=m[:,cols].mean(1); band=[y for y in range(max(0,b-40),min(H,b+60)) if fr[y]>0.6]
    if not band: return []
    y0=band[0]+2; pts=[]
    for x in range(int(l+(r-l)*0.05),int(r-(r-l)*0.05),6):
        if (r-l)*0.45+l < x < (r-l)*0.6+l: continue
        y=y0
        while y>0 and m[y,x]: y-=1
        if y0-y<40: pts.append((x,y+1))
    return pts
def rectify(path,size=128,debug=None):
    im,(l,t,r,b)=crop2(path); a=np.array(im); H,W=a.shape[:2]; m=loose(a)
    lines={}
    for s in ('left','right','top'):
        ln=fit_line(edge_points(m,s,l,t,r,b,H,W)); lines[s]=ln
    lines['bottom']=fit_line(bottom_points(a,l,t,r,b))
    if lines['bottom'] is None or lines['top'] is None or lines['left'] is None or lines['right'] is None:
        return None
    tl=inter(lines['top'],lines['left']); tr=inter(lines['top'],lines['right']); br=inter(lines['bottom'],lines['right']); bl=inter(lines['bottom'],lines['left'])
    src=np.float32([tl,tr,br,bl]); dst=np.float32([[0,0],[size,0],[size,size],[0,size]])
    M=cv2.getPerspectiveTransform(src,dst)
    bgr=cv2.cvtColor(a,cv2.COLOR_RGB2BGR)
    big=cv2.warpPerspective(bgr,M*np.array([[4,0,0],[0,4,0],[0,0,1]]) if False else cv2.getPerspectiveTransform(src,dst*4),(size*4,size*4),flags=cv2.INTER_LINEAR)
    out=cv2.resize(big,(size,size),interpolation=cv2.INTER_AREA)
    return out, src
if __name__=='__main__':
    for p in sorted(glob.glob('/mnt/user-data/uploads/IMG_94[5-8]*.jpeg')):
        n=p.split('/')[-1][4:8]
        if n in ('9485','9486','9487','9488','9489','9469'): continue
        r=rectify(p)
        if r is None: print(n,'FAIL'); continue
        out,src=r; cv2.imwrite(f'rect_IMG_{n}.png',out); print(n, src.round().tolist())
