"""Build img/wall.png: the map wall photographed, warped flat into world-image space (1024x512, 4 blocks/px).
compose.py uses it to fill pixels the screenshot HUD covered. Usage (repo root):
  python3 tools/wallfill.py <wall_photo>...
For each photo, the wall grid is fitted from every known tile SIFT-matched in it (global homography),
the photo is warped into world space, and each frame takes the photo in which its tile matched best."""
import cv2, numpy as np, json, os, sys
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=os.path.join(R,'img','tiles')
l2=json.load(open(os.path.join(R,'data','assign.json')))
sift=cv2.SIFT_create(nfeatures=30000); bf=cv2.BFMatcher()
feats={}
for n in l2:
    t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png'))
    feats[n]=sift.detectAndCompute(cv2.cvtColor(cv2.resize(t,(400,400),interpolation=cv2.INTER_CUBIC),cv2.COLOR_BGR2GRAY),None)
best={}   # n -> (inliers, photo index)
layers=[]
for wi,wp in enumerate(sys.argv[1:]):
    wall=cv2.imread(wp); kw,dw=sift.detectAndCompute(cv2.cvtColor(wall,cv2.COLOR_BGR2GRAY),None)
    gp=[];pp=[];seen={}
    for n,(kt,dt) in feats.items():
        if dt is None: continue
        good=[m for m,nn in bf.knnMatch(dt,dw,k=2) if m.distance<0.75*nn.distance]
        if len(good)<10: continue
        src=np.float32([kt[m.queryIdx].pt for m in good]); dst=np.float32([kw[m.trainIdx].pt for m in good])
        H,mask=cv2.findHomography(src,dst,cv2.RANSAC,5.0)
        if H is None or int(mask.sum())<40: continue
        seen[n]=int(mask.sum()); fx,fy=l2[n]
        c=cv2.perspectiveTransform(np.float32([[[0,0],[400,0],[400,400],[0,400]]]),H)[0]
        for (dx,dy),pt in zip([(0,0),(1,0),(1,1),(0,1)],c): gp.append([(fx+dx)*128,(fy+dy)*128]); pp.append(pt)
    if len(gp)<16: print(os.path.basename(wp),'too few tiles'); layers.append(None); continue
    Hg,m=cv2.findHomography(np.float32(pp),np.float32(gp),cv2.RANSAC,3.0)
    layer=cv2.warpPerspective(wall,Hg,(1024,512),flags=cv2.INTER_AREA)
    layers.append(layer); print(os.path.basename(wp),'tiles',len(seen),'grid inliers',int(m.sum()),'/',len(gp))
    for n,inl in seen.items():
        if inl>best.get(n,(0,))[0]: best[n]=(inl,wi)
out=np.zeros((512,1024,4),np.uint8)
for n,(inl,wi) in best.items():
    fx,fy=l2[n]; sl=(slice(fy*128,(fy+1)*128),slice(fx*128,(fx+1)*128))
    f=layers[wi][sl].astype(np.float32); t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png')).astype(np.float32)
    for c in range(3):   # match tile's colour statistics (photo lighting varies)
        mt,st=t[14:118,:,c].mean(),t[14:118,:,c].std(); mf,sf=f[14:118,:,c].mean(),f[14:118,:,c].std()
        f[...,c]=(f[...,c]-mf)*(st/max(sf,1e-3))+mt
    out[sl][...,:3]=np.clip(f,0,255); out[sl][...,3]=255
# the item frames on the wall leave thin dark seams at frame boundaries: inpaint a 3px band there
seam=np.zeros((512,1024),np.uint8)
for k in range(1,8): seam[:,k*128-1:k*128+2]=1
for k in range(1,4): seam[k*128-1:k*128+2,:]=1
out[...,:3]=cv2.inpaint(out[...,:3],seam,3,cv2.INPAINT_TELEA)
cv2.imwrite(os.path.join(R,'img','wall.png'),out); print('frames filled',len(best))
