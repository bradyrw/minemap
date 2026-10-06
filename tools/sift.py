import cv2, numpy as np, glob, json
wall=cv2.imread('/mnt/user-data/uploads/IMG_9489.jpeg'); wg=cv2.cvtColor(wall,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=20000)
kw,dw=sift.detectAndCompute(wg,None)
bf=cv2.BFMatcher()
out={}
for p in sorted(glob.glob('tiles_IMG_947[5-9].png')+glob.glob('tiles_IMG_948*.png')):
    n=p[10:14]
    t=cv2.imread(p); t=cv2.resize(t,(297,297),interpolation=cv2.INTER_CUBIC); tg=cv2.cvtColor(t,cv2.COLOR_BGR2GRAY)
    kt,dt=sift.detectAndCompute(tg,None)
    if dt is None: print(n,'no feats'); continue
    ms=bf.knnMatch(dt,dw,k=2)
    good=[m for m,nn in ms if m.distance<0.75*nn.distance]
    if len(good)<8: print(n,'few',len(good)); continue
    src=np.float32([kt[m.queryIdx].pt for m in good]); dst=np.float32([kw[m.trainIdx].pt for m in good])
    H,mask=cv2.findHomography(src,dst,cv2.RANSAC,6.0)
    if H is None: print(n,'noH'); continue
    inl=int(mask.sum())
    c=cv2.perspectiveTransform(np.float32([[[148,148]],[[0,0]],[[297,297]]]),H).reshape(-1,2)
    fx=(c[0][0]-40)/297; fy=(c[0][1]-125)/297
    out[n]=dict(inliers=inl,center=c[0].tolist(),tl=c[1].tolist(),br=c[2].tolist(),fx=round(fx,2),fy=round(fy,2))
    print(n,'inl',inl,'center',c[0].round(),'frame',round(fx-0.5,2),round(fy-0.5,2),'size',(c[2]-c[1]).round())

