from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7,2.6),dpi=160)
ax.plot([0,1],[0,0],color='black');ax.scatter([0,0],[.08,-.08],color='black');ax.plot([0,1],[.08,.23],color='black');ax.plot([0,1],[-.08,.23],color='black');ax.plot([1,1],[-.35,.45],color='black',lw=2);ax.annotate('slits',(.01,-.1),(.1,-.3),arrowprops={'arrowstyle':'->'});ax.text(.43,.2,'z = 1 m');ax.text(.008,.13,'B = 1 mm');ax.text(.80,-.26,'screen');ax.text(.30,.37,'overlap interval (rectangular pulse)');ax.plot([1,1],[-.1,.3],color='#b22',lw=4);ax.text(1.03,.08,'width = 2cTz/B');ax.set_xlim(-.1,1.5);ax.set_ylim(-.45,.55);ax.axis('off');fig.tight_layout();fig.savefig(Path(__file__).resolve().parent/'outputs'/'pulse_interference_diagram.png')
