from pathlib import Path
import csv,math
p=Path(__file__).resolve().parent/'outputs';p.mkdir(exist_ok=True)
lam=.532;B=(1.03961212,.231792344,1.01046945);C=(.00600069867,.0200179144,103.560653)
n=math.sqrt(1+sum(b*lam**2/(lam**2-c) for b,c in zip(B,C)))
angles=list(range(0,31,5)); f=lambda theta:1000*(math.sqrt(n*n-math.sin(math.radians(theta))**2)-math.cos(math.radians(theta)))
with (p/'bk7_opd_table.csv').open('w',newline='',encoding='utf-8-sig') as o:
 w=csv.writer(o);w.writerow(['theta1 / theta2 (deg)']+angles)
 for i,a in enumerate(angles):w.writerow([a]+['' if j<i else f'{f(b)-f(a):.3f}' for j,b in enumerate(angles)])
print('N-BK7 n(532 nm) =',n)
