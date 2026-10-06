import cv2, numpy as np, json
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
# level 3 first (2x upscale)
l3={'9477':(0,0),'9478':(2,0),'9480':(4,0),'9483':(6,0),'9479':(0,2),'9484':(2,2)}
for n,(fx,fy) in l3.items():
    t=cv2.imread(f'clean_IMG_{n}.png'); up=cv2.resize(t,(256,256),interpolation=cv2.INTER_NEAREST)
    m=~paper(up)
    m=cv2.erode(m.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)  # trim ragged edge
    if n!='9484': m[:]=True
    else: m[200:]=False
    put(up,fx*128,fy*128,m)
l2=json.load(open('assign.json'))
def hudmask(t):
    m=np.zeros((128,128),bool); m[0:9,36:92]=True; m[121:128,52:78]=True; m[127:128,:]=True; m[61:68,61:68]=True
    hsv=cv2.cvtColor(t,cv2.COLOR_BGR2HSV); gray=(hsv[...,1]<40)&(hsv[...,2]>60)&(hsv[...,2]<200); m[:12]|=gray[:12]
    return m
for n,(fx,fy) in l2.items():
    t=cv2.imread(f'rect_IMG_{n}.png')
    put(t,fx*128,fy*128,~hudmask(t))
cv2.imwrite('world.png',canvas)
json.dump({'x0':X0,'z0':Z0,'blocks_per_px':4,'w':W,'h':H,'level2':l2,'level3':l3},open('world.json','w'),indent=1)
print('explored px',int((canvas[...,3]>0).sum()))
