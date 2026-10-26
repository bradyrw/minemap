"""Assemble img/world.png from img/tiles/ and data/assign.json. Run from repo root: python3 tools/compose.py"""
import cv2, numpy as np, json, os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=os.path.join(R,'img','tiles'); D=os.path.join(R,'data')
X0,Z0=-4160,-2112   # world image top-left in blocks; 4 blocks per px
W,H=1024,768
WALL_Z=-1088        # the 8x4 level-2 wall starts here; wall frame (fx,fy) -> px (fx*128, (WALL_Z-Z0)//4 + fy*128)
canvas=np.zeros((H,W,4),np.uint8)
def paper(img):
    b,g,r=[img[...,i].astype(int) for i in range(3)]
    return (r>170)&(r<235)&(g>150)&(g<215)&(b>100)&(b<170)&(r-b>40)&(r-b<90)&(abs(r-g)<35)
OY=(WALL_Z-Z0)//4
def put(img,x,y,explored=None):
    h,w=img.shape[:2]
    if explored is None: explored=np.ones((h,w),bool)
    region=canvas[y:y+h,x:x+w]
    region[explored]=np.concatenate([img[explored],np.full((explored.sum(),1),255,np.uint8)],1)
world=json.load(open(os.path.join(D,'world.json')))
def hudmask(t):
    m=np.zeros((128,128),bool); m[0:9,36:92]=True; m[121:128,52:78]=True; m[127:128,:]=True; m[61:68,61:68]=True
    hsv=cv2.cvtColor(t,cv2.COLOR_BGR2HSV); gray=(hsv[...,1]<40)&(hsv[...,2]>60)&(hsv[...,2]<200); m[:12]|=gray[:12]
    # slivers of the map's paper border that survived rectification, top and bottom edges
    dark=hsv[...,2]<70
    pp=paper(t)|dark; edge=np.zeros_like(m); edge[:9]=True; edge[117:]=True; m[:4]=True; m[123:]=True; m[:13,34:94]=True
    pm=pp&edge; pm=cv2.dilate(pm.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&edge
    # XP number (green digits) and dark ticks on the paper border near the bottom
    green=(hsv[...,0]>35)&(hsv[...,0]<90)&(hsv[...,1]>150)&(hsv[...,2]>200); m[118:]|=green[118:]
    return m|pm
# level 3 first (2x upscale), HUD pixels inpainted since nothing sits underneath
for n,(fx,fy) in world['level3'].items():
    t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png')); t=cv2.inpaint(t,hudmask(t).astype(np.uint8),3,cv2.INPAINT_TELEA)
    up=cv2.resize(t,(256,256),interpolation=cv2.INTER_NEAREST)
    m=~paper(up)
    m=cv2.erode(m.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)  # trim ragged edge
    if n!='9484': m[:]=True
    else: m[200:]=False
    put(up,fx*128,OY+fy*128,m)
l2=json.load(open(os.path.join(D,'assign.json')))
for n,(fx,fy) in l2.items():
    t=cv2.imread(os.path.join(T,f'rect_IMG_{n}.png'))
    put(t,fx*128,OY+fy*128,~hudmask(t))
# fill what the HUD covered (and anything else still empty) from the flattened wall photo, img/wall.png
wp=os.path.join(R,'img','wall.png')
if os.path.exists(wp):
    w=cv2.imread(wp,cv2.IMREAD_UNCHANGED)
    if w.shape[0]!=H:   # wall.png is wall-sized (1024x512); pad to world
        full=np.zeros((H,W,4),np.uint8); full[OY:OY+w.shape[0],:w.shape[1]]=w; w=full
    hole=(canvas[...,3]==0)&(w[...,3]>0)
    canvas[hole]=np.concatenate([w[hole][:,:3],np.full((hole.sum(),1),255,np.uint8)],1)
# level-4 maps last, 16 blocks/px upscaled 4x, only where nothing better exists
for name,(bx,bz) in world.get('level4',{}).items():
    t=cv2.imread(os.path.join(T,f'l4_{name}.png')); up=cv2.resize(t,(512,512),interpolation=cv2.INTER_NEAREST)
    hm=cv2.resize(hudmask(t).astype(np.uint8),(512,512),interpolation=cv2.INTER_NEAREST).astype(bool)
    pm=paper(up)|hm
    # unexplored paper = big connected blobs; single map pixels that happen to be paper-coloured (sand, birch) are kept
    n,lab,st,_=cv2.connectedComponentsWithStats(pm.astype(np.uint8),connectivity=4)
    big=np.zeros_like(pm)
    for j in range(1,n):
        if st[j,4]>=12*16: big[lab==j]=True
    m=~big; m=cv2.erode(m.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    px,pz=(bx-X0)//4,(bz-Z0)//4
    sub=canvas[pz:pz+512,px:px+512]; hole=(sub[...,3]==0)&m[:sub.shape[0],:sub.shape[1]]
    sub[hole]=np.concatenate([up[:sub.shape[0],:sub.shape[1]][hole],np.full((hole.sum(),1),255,np.uint8)],1)
cv2.imwrite(os.path.join(R,'img','world.png'),canvas)
world['level2']=l2; world.update({'x0':X0,'z0':Z0,'w':W,'h':H}); json.dump(world,open(os.path.join(D,'world.json'),'w'),indent=1)
print('explored px',int((canvas[...,3]>0).sum()))
