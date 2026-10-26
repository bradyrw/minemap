"""Relief from map shading (what the screenshots support). A Minecraft map shades each pixel against the pixel north of it (brighter = higher
than north, darker = lower). Tree canopy is lumpy, so that shading is only meaningful on open ground; we read it
there (relative to nearby pixels of the same colour class), integrate northwards with water pinned to sea level,
and calibrate the step size against pins that carry a Y. Integrating to a true height field was tried and does not survive the JPEG/angled-photo tiles (pin-Y calibration
correlates ~0), so the outputs are: img/relief.png = the map with its own slope shading exaggerated 3x on open
ground (bands = slopes; dense bands = steep), img/topo.png = red tint where open ground is rough + green hatch
where tree canopy hides the terrain. Flat held-map screenshots (nearest-neighbour, no angle) would allow a real DEM."""
import cv2, numpy as np, os, json
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsqr
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
w=cv2.imread(os.path.join(R,'img','world.png'),cv2.IMREAD_UNCHANGED); alpha=w[...,3]>0; bgr=w[...,:3].astype(np.float32)
H,W=alpha.shape; X0,Z0=-4160,-2112
hsv=cv2.cvtColor(w[...,:3],cv2.COLOR_BGR2HSV); hh,ss=hsv[...,0].astype(int),hsv[...,1].astype(int)
water=((hh>95)&(hh<135)&(ss>80))&alpha; land=alpha&~water
V=bgr.mean(2); chroma=bgr/np.maximum(bgr.sum(2,keepdims=True),1)
K=30; rs=np.random.RandomState(0)
samp=chroma[land].reshape(-1,3); samp=samp[rs.choice(len(samp),min(80000,len(samp)),replace=False)].astype(np.float32)
_,_,cen=cv2.kmeans(samp,K,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,50,1e-4),3,cv2.KMEANS_PP_CENTERS)
cls=((chroma.reshape(-1,1,3)-cen[None])**2).sum(2).argmin(1).reshape(H,W); cls[~land]=-1
# canopy = speckled texture: local std of brightness is high in both directions (slope shading is high in one)
Vf=V.astype(np.float32); lm=land.astype(np.float32)
def lstd(img,k):
    m1=cv2.blur(img*lm,k)/np.maximum(cv2.blur(lm,k),1e-3); m2=cv2.blur(img*img*lm,k)/np.maximum(cv2.blur(lm,k),1e-3); return np.sqrt(np.maximum(m2-m1*m1,0))
sx=lstd(Vf,(9,1)); sy=lstd(Vf,(1,9))
hue_var=lstd(chroma[...,1].astype(np.float32)*255,(7,7))
# combine: dark-green or pink colour classes (true canopy colours) OR strongly speckled texture
colcan=np.zeros((H,W),bool)
for k in range(K):
    m=cls==k
    if m.sum()==0: continue
    c=bgr[m].mean(0)[::-1]; g=c[1]/max(c.sum(),1)
    if (g>0.42 and V[m].mean()<98) or (c[0]>c[1] and c[0]>120 and c[1]<110): colcan|=m
tex=(np.minimum(sx,sy)>12)&(hue_var>6.5)
canopy=land&(colcan|tex)
canopy=cv2.morphologyEx(canopy.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)).astype(bool)&land
open_=land&~canopy
# shade relative to same-class open neighbours, with a little horizontal coherence (slope lines run E-W)
D=np.zeros((H,W),np.float32)
for k in range(K):
    m=(cls==k)&open_
    if m.sum()<100: continue
    Vk=np.where(m,V,0).astype(np.float32); cnt=m.astype(np.float32)
    ref=cv2.blur(Vk,(31,31))/np.maximum(cv2.blur(cnt,(31,31)),1e-3)
    D[m]=(V/np.maximum(ref,1)-1)[m]
Dm=np.where(open_,D,0).astype(np.float32); om=open_.astype(np.float32)
Dh=cv2.blur(Dm,(5,1))/np.maximum(cv2.blur(om,(5,1)),1e-3)
s=np.zeros((H,W),np.float32); s[(Dh>0.05)&open_]=1; s[(Dh<-0.05)&open_]=-1

# --- outputs
om=open_.astype(np.float32)
rough=cv2.blur((np.abs(s)>0).astype(np.float32),(9,9))/np.maximum(cv2.blur(om,(9,9)),0.15); rough[~open_]=0
# ignore dense speckle: a run of slope pixels that is mostly isolated 1-px dots is texture, not a slope line
runs=cv2.blur((np.abs(s)>0).astype(np.float32),(5,1)); lines=cv2.blur((runs>=0.8).astype(np.float32),(9,9))/np.maximum(cv2.blur(om,(9,9)),0.15)
rough=np.minimum(rough,lines*1.6)
relief=w[...,:3].astype(np.float32)
gain=np.clip(1+3.0*Dh,0.55,1.6)[...,None]; relief=np.where(open_[...,None],relief*gain,relief)
out=np.zeros((H,W,4),np.uint8); out[...,:3]=np.clip(relief,0,255); out[...,3]=np.where(alpha,255,0); cv2.imwrite(os.path.join(R,'img','relief.png'),out)
topo=np.zeros((H,W,4),np.uint8)
st=np.clip((rough-0.25)/0.5,0,1); topo[...,0]=30; topo[...,1]=30; topo[...,2]=255; topo[...,3]=(st*160).astype(np.uint8)
hatch=canopy&(((np.arange(W)[None,:]+np.arange(H)[:,None])%4)==0); topo[hatch]=(40,120,40,150)
cv2.imwrite(os.path.join(R,'img','topo.png'),topo)
np.save(os.path.join(R,'data','rough.npy'),rough.astype(np.float32))
json.dump({'note':'topo.png: red = rough/steep open ground (density of slope-shaded pixels), green hatch = tree canopy (terrain hidden). relief.png = map with slope shading exaggerated.'},open(os.path.join(R,'data','topo.json'),'w'),indent=1)
print('open ground px',int(open_.sum()),'canopy px',int(canopy.sum()),'rough>0.5 px',int((rough>0.5).sum()))
