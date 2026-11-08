from pathlib import Path
import csv,math
import numpy as np
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent/'outputs'
with (p/'values.csv').open(encoding='utf-8-sig',newline='') as f:data=list(csv.DictReader(f))
for group,color in [('green','#25874a'),('red','#b33838')]:
 a=sorted([(float(r['d_or_condition']),float(r['V'])) for r in data if r['group']==group]);d=np.array([x for x,y in a]);y=np.array([y for x,y in a]);v0=y[d==0][0];threshold=v0/math.e
 def ss(logL):return np.sum((y-v0*np.exp(-2*np.abs(d)/np.exp(logL)))**2)
 z=minimize_scalar(ss,bounds=(math.log(.001),math.log(1000)),method='bounded');L=np.exp(z.x)
 fig,ax=plt.subplots(figsize=(7,3.9),dpi=190);ax.plot(d,y,'o',color=color,markersize=5,label='Image estimates');grid=np.linspace(-.50,.50,600) if group=='green' else np.linspace(-2.7,.1,600);ax.plot(grid,v0*np.exp(-2*np.abs(grid)/L),color=color,lw=1.5,label='Exponential fit');ax.axhline(threshold,color='#274f93',ls='--',lw=1,label=f'V₀/e = {threshold:.3f}');cross=L/2*(1 if group=='green' else -1);ax.plot(cross,threshold,'o',color='#274f93',ms=5);ax.annotate(f'd = {cross:.3f} cm',(cross,threshold),xytext=(-95,25) if group=='green' else (10,28),textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'->','color':'#274f93'});ax.set_ylim(0,1.02);ax.set_xlabel('Mirror displacement d (cm)');ax.set_ylabel('Estimated visibility V');ax.grid(alpha=.3);ax.legend(fontsize=8,loc='upper right' if group=='red' else 'lower center',ncol=1 if group=='red' else 2);fig.tight_layout();fig.savefig(p/f'{group}_exponential_only.png');plt.close(fig);print(group,L,z.fun)

