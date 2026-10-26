"""Map-frame coverage for the viewer's Frames toggle. Frames at level L (size S=128*2^L) cover S*k-64 .. S*k+S-65.
Names are relative to the frame that contains Home at that level: H, N1, S1E2 ... Writes data/frames.json."""
import numpy as np, json, os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
w=json.load(open(os.path.join(R,'data','world.json'))); X0,Z0,W,H=w['x0'],w['z0'],w['w'],w['h']
src=np.load(os.path.join(R,'data','source.npy')); HOME=(-2428,-449)
out={}
for L in (2,3,4):
    S=128*2**L; hk=((HOME[0]+64)//S,(HOME[1]+64)//S)
    frames=[]
    kx0=(X0+64)//S-1; kx1=(X0+W*4+64)//S+1; kz0=(Z0+64)//S-1; kz1=(Z0+H*4+64)//S+1
    for kz in range(kz0,kz1+1):
        for kx in range(kx0,kx1+1):
            x0=S*kx-64; z0=S*kz-64
            px0=max(0,(x0-X0)//4); px1=min(W,(x0+S-X0)//4); pz0=max(0,(z0-Z0)//4); pz1=min(H,(z0+S-Z0)//4)
            area=(S//4)**2; sub=src[pz0:pz1,px0:px1] if px1>px0 and pz1>pz0 else np.zeros((0,0),np.uint8)
            n=sub.size; explored=int((sub>0).sum())
            fine=int(((sub>0)&(sub<=L)).sum())           # at this level or finer
            wall=int((sub==9).sum())
            dx=kx-hk[0]; dz=kz-hk[1]
            name=('H' if dx==0 and dz==0 else (('N%d'%-dz if dz<0 else 'S%d'%dz) if dz else '')+(('E%d'%dx if dx>0 else 'W%d'%-dx) if dx else ''))
            if explored==0 and n: status='none'
            elif explored==0: status='off'
            elif fine/area>=0.6: status='have'
            elif fine/area>=0.15: status='partial'
            else: status='coarse'
            if status=='off': continue
            frames.append({'name':name,'x0':x0,'z0':z0,'size':S,'explored':round(explored/area,2),'fine':round(fine/area,2),'wall':round(wall/area,2),'status':status})
    out['L%d'%L]=frames
    print('L%d'%L,{s:sum(1 for f in frames if f['status']==s) for s in ('have','partial','coarse','none')})
json.dump(out,open(os.path.join(R,'data','frames.json'),'w'),indent=0)
