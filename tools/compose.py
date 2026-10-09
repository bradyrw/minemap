"""Assemble img/world.png from img/tiles/ and data/assign.json. Run from repo root: python3 tools/compose.py"""
import cv2, numpy as np, json, os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=os.path.join(R,'img','tiles'); D=os.path.join(R,'data')
X0,Z0=-4160,-1088   # wall top-left in blocks; 4 blocks per px at level 2
W,H=1024,512
canvas=np.zeros((H,W,4),np.uint8)
def paper(img):
    b,g,r=[img[...,i].astype(int) for i in range(3)]
    return (r>170)&(r<235)&(g>150)&(g<215)&(b>100)&(b<170)&(r-b>40)&(r-b<90)&(abs(r-g)<35)
def put(img,x,y,explored=None):
    h,w=img.shape[:2]
    if explored is None: explored=np.ones((h,w),bool)
    region=canvas[y:y+h,x:x+w]
    region[explored]=np.concatenate([img[explored],np.full((explored.sum(),1),255,np.uint8)],1)
world=json.load(open(os.path.join(D,'world.json')))
def hudmask(t):
    m=np.zeros((128,128),bool); m[0:9,36:92]=True; m[121:128,52:78]=True; m[127:128,:]=True; m[61:68,61:68]=True
    hsv=cv2.cvtColor(t,cv2.COLOR_BGR2HSV); gray=(hsv[...,1]<40)&(hsv[...,2]>60)&(hsv[...,2]<200); m[:12]|=gray[:12]
    return m
# level 3 first (2x upscale), HUD pixels inpainted since nothing sits underneath
for n,(fx,fy) in world['level3'].items():
    t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png')); t=cv2.inpaint(t,hudmask(t).astype(np.uint8),3,cv2.INPAINT_TELEA)
    up=cv2.resize(t,(256,256),interpolation=cv2.INTER_NEAREST)
    m=~paper(up)
    m=cv2.erode(m.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)  # trim ragged edge
    if n!='9484': m[:]=True
    else: m[200:]=False
    put(up,fx*128,fy*128,m)
l2=json.load(open(os.path.join(D,'assign.json')))
for n,(fx,fy) in l2.items():
    t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png'))
    put(t,fx*128,fy*128,~hudmask(t))
cv2.imwrite(os.path.join(R,'img','world.png'),canvas)
world['level2']=l2; json.dump(world,open(os.path.join(D,'world.json'),'w'),indent=1)
print('explored px',int((canvas[...,3]>0).sum()))
