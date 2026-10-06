import cv2, numpy as np, json, glob
from rectify import rectify
l2=json.load(open('assign.json')); l2.update({'9475':(7,1),'9476':(4,2)})
l3={'9477':(0,0),'9478':(2,0),'9480':(4,0),'9483':(6,0),'9479':(0,2),'9484':(2,2)}
sift=cv2.SIFT_create(nfeatures=8000); bf=cv2.BFMatcher()
# reference: level-3 tiles at 512px (2 blocks/px)
ref={}
for n,(fx,fy) in l3.items():
    t=cv2.imread(f'rect_IMG_{n}.png') if n!='9484' else cv2.imread('tiles_IMG_9484.png')
    ref[(fx,fy)]=cv2.resize(t,(512,512),interpolation=cv2.INTER_CUBIC)
report={}
for n,(fx,fy) in l2.items():
    key=(fx//2*2,fy//2*2)
    if key not in ref: print(n,'no ref'); continue
    R=ref[key]; qx,qy=(fx%2)*256,(fy%2)*256
    big=cv2.resize(cv2.imread(f'rect_IMG_{n}.png'),(256,256),interpolation=cv2.INTER_CUBIC)
    k1,d1=sift.detectAndCompute(cv2.cvtColor(big,cv2.COLOR_BGR2GRAY),None)
    k2,d2=sift.detectAndCompute(cv2.cvtColor(R,cv2.COLOR_BGR2GRAY),None)
    if d1 is None or d2 is None: print(n,'nofeat'); continue
    good=[m for m,nn in bf.knnMatch(d1,d2,k=2) if m.distance<0.8*nn.distance]
    if len(good)<8: print(n,'few',len(good)); continue
    src=np.float32([k1[m.queryIdx].pt for m in good]); dst=np.float32([k2[m.trainIdx].pt for m in good])-[qx,qy]
    H,mask=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=3.0)
    if H is None: print(n,'noH'); continue
    inl=int(mask.sum()); sc=np.hypot(H[0,0],H[0,1]); tx,ty=H[0,2],H[1,2]
    # corner shift at 128-scale: where does big's (0,0) and (256,256) land
    c=cv2.transform(np.float32([[[0,0],[256,256]]]),H)[0]/2
    print(n,f'inl {inl:3d} scale {sc:.3f} tl {c[0].round(1)} br {c[1].round(1)}')
    report[n]=dict(inl=inl,scale=float(sc),tl=c[0].tolist(),br=c[1].tolist())
json.dump(report,open('refine.json','w'),indent=1)
