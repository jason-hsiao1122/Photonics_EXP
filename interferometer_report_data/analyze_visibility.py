from pathlib import Path
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter1d
import numpy as np,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent; im=p/'images'; out=p/'outputs';out.mkdir(exist_ok=True)
green=[(-.2,'d=-0.2.png'),(-.1,'d=-0.1.png'),(0,'d=0.png'),(.1,'d=0.1.png'),(.2,'d=0.2.png'),(.3,'d=0.3.png')]
red=[(-2.5,'d = -2.5.png',(.37,.49)),(-2,'d = -2.png',(.37,.50)),(-1.5,'d = -1.5.png',(.30,.49)),(-.5,'d = -0.5.png',(.25,.51)),(0,'d =  0(10.1).png',(.25,.51))]
items=[('green',d,im/'麥克森'/'綠光'/n,(.20,.51)) for d,n in green]+[('red',d,im/'麥克森'/'紅光'/n,box) for d,n,box in red]+[('young',1,im/'楊式干涉儀'/'原始.jpg',(.45,.55)),('young',2,im/'楊式干涉儀'/'加干擾2.jpg',(.065,.12)),('young',3,im/'楊式干涉儀'/'加干擾2+光圈.jpg',(.44,.56))]
rows=[]
for group,d,src,box in items:
 srcim=Image.open(src).convert('RGB');a=np.asarray(srcim.convert('L'),float);h,w=a.shape;y=h//2;x1=int(box[0]*w);x2=int(box[1]*w);q=gaussian_filter1d(a[y-4:y+5,x1:x2].mean(axis=0),6,mode='reflect');hi=q.max();lo=q.min();v=(hi-lo)/(hi+lo)
 rows.append([group,d,str(src.relative_to(p)),hi,lo,v,*box]);draw=ImageDraw.Draw(srcim);draw.rectangle((x1,y-4,x2-1,y+4),outline=(255,0,0),width=2);srcim.save(out/f'{group}_{d}.png')
for group in ['green','red']:
 select=sorted([r for r in rows if r[0]==group],key=lambda x:x[1]);fig,ax=plt.subplots(figsize=(6,3.3),dpi=180);ax.plot([r[1] for r in select],[r[5] for r in select],'-o',c='#25874a' if group=='green' else '#b33838',ms=5,lw=1.4);ax.set_xticks([r[1] for r in select]);ax.set_xlabel('Mirror displacement d (cm)');ax.set_ylabel('Estimated visibility V');ax.set_ylim(0,1);ax.grid(alpha=.3);fig.tight_layout();fig.savefig(out/f'{group}_chart.png');plt.close(fig)
with (out/'values.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['group','d_or_condition','file','Imax','Imin','V','roi_start','roi_end']);w.writerows(rows)
for r in rows:print(r[0],r[1],round(r[3],2),round(r[4],2),round(r[5],4))


