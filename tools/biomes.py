"""Best-guess biome layer from map colours: img/biomes.png (flat colours, alpha where explored) + data/biomes.json (key).
Run from repo root after compose.py: python3 tools/biomes.py"""
import cv2, numpy as np, json, os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c=cv2.imread(os.path.join(R,'img','world.png'),cv2.IMREAD_UNCHANGED); explored=c[...,3]>0; bgr=c[...,:3]
b=cv2.blur(cv2.medianBlur(bgr,3),(3,3))
lab=cv2.cvtColor(b,cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
# reference colours (BGR) for each class, found by k-means on this map; nearest-centre in Lab
REF={
 'Deep ocean':[[124,56,18]],
 'Water (lake / river / shallows)':[[166,70,27],[144,87,56]],
 'Plains':[[81,150,130]],
 'Meadow / highland grass':[[101,161,159]],
 'Forest':[[75,121,103],[58,105,86]],
 'Dark forest':[[42,89,67]],
 'Taiga (spruce)':[[90,139,120]],
 'Snowy taiga':[[73,95,85]],
 'Swamp':[[87,75,59]],
 'Mountains / stone':[[122,111,87]],
 'Snow':[[163,192,197],[174,147,148]],
}
names=list(REF); cents=[];owner=[]
for i,n in enumerate(names):
    for col in REF[n]: cents.append(col); owner.append(i)
cents=cv2.cvtColor(np.uint8([cents]),cv2.COLOR_BGR2LAB)[0].astype(np.float32); owner=np.array(owner)
d=((lab[:,None,:]-cents[None,:,:])**2).sum(2); cls=owner[d.argmin(1)].reshape(512,1024)
# colour rules on the unblurred image, as cell densities (8x8 px = 32 blocks)
hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV); h,s,v=hsv[...,0].astype(int),hsv[...,1].astype(int),hsv[...,2].astype(int)
pink=(((h<12)|(h>150))&(s>35)&(s<170)&(v>150)).astype(np.float32)
orange=((h>=5)&(h<22)&(s>120)&(v>110)).astype(np.float32)
sand=((h>=18)&(h<36)&(s>35)&(s<130)&(v>165)).astype(np.float32)
def dens(m): return cv2.blur(m,(9,9))
for nm,m,th in [('Cherry grove',pink,0.06),('Autumn forest',orange,0.10),('Beach / sand',sand,0.45)]:
    names.append(nm); cls[dens(m)>th]=len(names)-1
# smooth: majority vote in 7x7, then drop specks
K=len(names)
def mode_filter(cls,k=7):
    best=np.zeros_like(cls); bestc=np.zeros(cls.shape,np.float32)
    for i in range(K):
        cnt=cv2.blur((cls==i).astype(np.float32),(k,k)); upd=cnt>bestc; best[upd]=i; bestc[upd]=cnt[upd]
    return best
cls=mode_filter(cls,7)
for _ in range(2):
    for i in range(K):
        n,cc,st,_=cv2.connectedComponentsWithStats((cls==i).astype(np.uint8),connectivity=4)
        for j in range(1,n):
            if st[j,4]<(60 if names[i] in ('Autumn forest','Cherry grove','Mountains / stone') else 30):
                m=cc==j; ring=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&~m
                vals=cls[ring]; vals=vals[vals!=i]
                if len(vals): cls[m]=np.bincount(vals).argmax()
PAL={'Deep ocean':'#1f3f8f','Water (lake / river / shallows)':'#3f8fe0','Plains':'#9bd54a','Meadow / highland grass':'#d8e36a',
 'Forest':'#2e8b3a','Dark forest':'#145a22','Taiga (spruce)':'#3f8f7a','Snowy taiga':'#6f8f8a','Swamp':'#5a5a2a',
 'Mountains / stone':'#8a8a8a','Snow':'#f0f4ff','Cherry grove':'#ff9ad5','Autumn forest':'#e07a2a','Beach / sand':'#f2e2a0'}
out=np.zeros((512,1024,4),np.uint8)
for i,n in enumerate(names):
    hx=PAL[n].lstrip('#'); rgb=tuple(int(hx[k:k+2],16) for k in (0,2,4))
    m=(cls==i)&explored; out[m]=(rgb[2],rgb[1],rgb[0],255)
cv2.imwrite(os.path.join(R,'img','biomes.png'),out)
json.dump([{'name':n,'color':PAL[n],'px':int(((cls==i)&explored).sum())} for i,n in enumerate(names)],open(os.path.join(R,'data','biomes.json'),'w'),indent=1)
for i,n in enumerate(names): print(f'{n:35s} {((cls==i)&explored).sum():7d}')
