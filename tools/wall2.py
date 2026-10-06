import cv2, numpy as np, json, glob
wall=cv2.imread('/mnt/user-data/uploads/IMG_9505.png'); wg=cv2.cvtColor(wall,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=30000); kw,dw=sift.detectAndCompute(wg,None); bf=cv2.BFMatcher()
l2=json.load(open('assign.json')); l2.update({'9475':(7,1),'9476':(4,2)})
res={}
for p in sorted(glob.glob('rect_IMG_*.png')):
    n=p[9:13]
    t=cv2.resize(cv2.imread(p),(400,400),interpolation=cv2.INTER_CUBIC); tg=cv2.cvtColor(t,cv2.COLOR_BGR2GRAY)
    kt,dt=sift.detectAndCompute(tg,None)
    if dt is None: continue
    good=[m for m,nn in bf.knnMatch(dt,dw,k=2) if m.distance<0.75*nn.distance]
    if len(good)<10: continue
    src=np.float32([kt[m.queryIdx].pt for m in good]); dst=np.float32([kw[m.trainIdx].pt for m in good])
    H,mask=cv2.findHomography(src,dst,cv2.RANSAC,5.0)
    if H is None: continue
    inl=int(mask.sum())
    if inl<25: continue
    c=cv2.perspectiveTransform(np.float32([[[0,0],[400,0],[400,400],[0,400]]]),H)[0]
    res[n]=(inl,c)
    print(n,'inl',inl,'corners',c.round().tolist(), 'known',l2.get(n))
# fit grid->photo homography from known tiles
gp=[];pp=[]
for n,(inl,c) in res.items():
    if n in l2:
        fx,fy=l2[n]
        for (dx,dy),pt in zip([(0,0),(1,0),(1,1),(0,1)],c): gp.append([fx+dx,fy+dy]); pp.append(pt)
Hg,m=cv2.findHomography(np.float32(gp),np.float32(pp),cv2.RANSAC,25.0); print('grid fit inliers',int(m.sum()),'/',len(gp))
Hi=np.linalg.inv(Hg)
for n,(inl,c) in res.items():
    g=cv2.perspectiveTransform(c.reshape(1,-1,2),Hi)[0]
    print(n,'grid corners',g.round(2).tolist(),'known',l2.get(n))
