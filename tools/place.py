"""Place level-2 map screenshots on the wall grid using a photo of the map wall.
Usage (from repo root):
  python3 tools/place.py <wall_photo> <tile_screenshot>...
Rectifies each tile into img/tiles/rect_IMG_<n>.png, then SIFT-matches every known tile
plus the new ones against the wall photo, fits the wall grid from the known tiles, and
prints each new tile's grid (fx,fy). Add confirmed ones to data/assign.json, then run compose.py.
"""
import cv2, numpy as np, json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rectify import rectify
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=os.path.join(R,'img','tiles')
wallp, shots = sys.argv[1], sys.argv[2:]
new=[]
for p in shots:
    n=os.path.basename(p).split('.')[0][-4:]
    r=rectify(p)
    if r is None: print(n,'RECTIFY FAILED'); continue
    cv2.imwrite(os.path.join(T,f'rect_IMG_{n}.png'),r[0]); new.append(n); print(n,'rectified')
wall=cv2.imread(wallp); wg=cv2.cvtColor(wall,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=30000); kw,dw=sift.detectAndCompute(wg,None); bf=cv2.BFMatcher()
l2=json.load(open(os.path.join(R,'data','assign.json')))
res={}
for p in sorted(glob.glob(os.path.join(T,'rect_IMG_*.png'))):
    n=os.path.basename(p)[9:13]
    t=cv2.resize(cv2.imread(p),(400,400),interpolation=cv2.INTER_CUBIC); tg=cv2.cvtColor(t,cv2.COLOR_BGR2GRAY)
    kt,dt=sift.detectAndCompute(tg,None)
    if dt is None: continue
    good=[m for m,nn in bf.knnMatch(dt,dw,k=2) if m.distance<0.75*nn.distance]
    if len(good)<10: continue
    src=np.float32([kt[m.queryIdx].pt for m in good]); dst=np.float32([kw[m.trainIdx].pt for m in good])
    H,mask=cv2.findHomography(src,dst,cv2.RANSAC,5.0)
    if H is None or int(mask.sum())<25: continue
    res[n]=(int(mask.sum()),cv2.perspectiveTransform(np.float32([[[0,0],[400,0],[400,400],[0,400]]]),H)[0])
gp=[];pp=[]
for n,(inl,c) in res.items():
    if n in l2:
        fx,fy=l2[n]
        for (dx,dy),pt in zip([(0,0),(1,0),(1,1),(0,1)],c): gp.append([fx+dx,fy+dy]); pp.append(pt)
if len(gp)<8: sys.exit('too few known tiles visible in wall photo')
Hg,m=cv2.findHomography(np.float32(gp),np.float32(pp),cv2.RANSAC,25.0)
print(f'grid fit: {int(m.sum())}/{len(gp)} inliers from {len(gp)//4} known tiles')
Hi=np.linalg.inv(Hg)
for n,(inl,c) in res.items():
    g=cv2.perspectiveTransform(c.reshape(1,-1,2),Hi)[0]
    tag='KNOWN' if n in l2 else 'NEW'
    print(f'{n} {tag:5s} inl {inl:3d} tl {g[0].round(2).tolist()} br {g[2].round(2).tolist()}', '' if n not in l2 else l2[n])
