from __future__ import annotations
import numpy as np
from typing import Dict, Any
from scipy.signal import dlti
from .core import diophantine, poly_conv_desc, poly_at1_desc, factor_z_from_F_and_update_d, dlsim_safe
from .io import save_json, save_csv

def _plot_series(x, y, y2=None, title='', backend='mpl', path=None, xlabel='k', ylabel='y[k]'):
    if backend=='none': return
    if backend=='mpl':
        import matplotlib.pyplot as plt
        plt.figure(); plt.plot(x,y,'o',label='y')
        if y2 is not None: plt.plot(x,y2,'-',label='ref')
        plt.grid(True); plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.legend()
        if path: from .utils import ensure_dir_for; ensure_dir_for(path); plt.savefig(path, dpi=150, bbox_inches='tight')
        else: plt.show()
        plt.close()
    elif backend=='plotly':
        import plotly.graph_objects as go
        fig = go.Figure(); fig.add_trace(go.Scatter(x=x,y=y,mode='markers',name='y'))
        if y2 is not None: fig.add_trace(go.Scatter(x=x,y=y2,mode='lines',name='ref'))
        fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel)
        if path: from .utils import ensure_dir_for; ensure_dir_for(path); fig.write_html(path)
        else: fig.show()
    else: raise ValueError('backend must be mpl|plotly|none')

def solve_alpha_beta(A,B,D,d=0,degS=None,degR=None,layout='ogata'):
    alpha,beta,E = diophantine(A,B,D,d,degS,degR,layout); return {'alpha':alpha,'beta':beta,'E':E}

def polydesign(A,B,D=None,H=None,F=None,d=0,degS=None,degR=None,layout='ogata',pretty=False,show_E=False,
               backend='none',save=None,T=1.0,kmax=40,config=None,export_json=None,export_csv=None,ogata_parity=False):
    d_eff=d
    if D is None:
        if H is None or F is None: raise ValueError('Provide D or both H and F.')
        if ogata_parity: _,F,d_eff = factor_z_from_F_and_update_d(F,d_eff)
        D = poly_conv_desc(F,H)
    res = solve_alpha_beta(A,B,D,d_eff,degS,degR,layout); alpha,beta,E = res['alpha'],res['beta'],res['E']
    if export_json: save_json(export_json, {'A':A,'B':B,'D':D,'alpha':alpha,'beta':beta,'layout':layout})
    if export_csv:  save_csv(export_csv, [('A',A),('B',B),('D',D),('alpha',alpha),('beta',beta)])
    if (H is not None and F is not None and config in (1,2)):
        K0 = poly_at1_desc(H) / poly_at1_desc(B) if config==2 else 1.0
        if config==2: num,den = (np.asarray(B)*K0).tolist(), H
        else:         num,den = (np.asarray(B)*K0).tolist(), poly_conv_desc(H,F)
        sys = dlti(num,den,dt=T); k = np.arange(0,kmax+1); _, y = dlsim_safe(sys, np.ones_like(k), t=k)
        path = (save+'_step'+('.png' if backend=='mpl' else '.html')) if save else None
        _plot_series(k, y.squeeze(), title='Unit-Step Response', backend=backend, path=path)
    return {'alpha':alpha,'beta':beta,'E':E}

def rst_design(A,B,H,F,d=0,degS=None,degR=None,layout='ogata',config=2,backend='mpl',save=None,T=1.0,kmax=40,
               export_json=None,pretty=False,ogata_parity=False):
    d_eff=d
    if ogata_parity: _,F,d_eff = factor_z_from_F_and_update_d(F,d_eff)
    D = poly_conv_desc(F,H); alpha,beta,_ = diophantine(A,B,D,d_eff,degS,degR,layout)
    K0 = poly_at1_desc(H) / poly_at1_desc(B) if config==2 else 1.0
    num = (np.asarray(B)*K0).tolist() if config==2 else B
    den = H if config==2 else poly_conv_desc(H,F)
    sys = dlti(num,den,dt=T); k = np.arange(0,kmax+1)
    _, y_step = dlsim_safe(sys, np.ones_like(k), t=k); _, y_ramp = dlsim_safe(sys, 0.2*k, t=k)
    if save:
        ext = '.png' if backend=='mpl' else '.html'
        _plot_series(k,y_step.squeeze(),title='Unit-Step Response',backend=backend,path=save+'_step'+ext)
        _plot_series(k,y_ramp.squeeze(),title='Unit-Ramp Response',backend=backend,path=save+'_ramp'+ext)
    else:
        _plot_series(k,y_step.squeeze(),title='Unit-Step Response',backend=backend,path=None)
        _plot_series(k,y_ramp.squeeze(),title='Unit-Ramp Response',backend=backend,path=None)
    if export_json:
        save_json(export_json, {'A':A,'B':B,'H':H,'F':F,'D':D,'d_eff':d_eff,'alpha':alpha,'beta':beta,'K0':K0,'closed_loop':{'num':num,'den':den,'T':T}})
    return {'alpha':alpha,'beta':beta,'K0':K0,'num':num,'den':den}

def model_match(A,B,Gnum,Gden,H1,F,d=0,degS=None,degR=None,layout='ogata',backend='mpl',save=None,T=1.0,kmax=40,
                export_json=None,pretty=False):
    D = poly_conv_desc(F,B,H1); alpha,beta,_ = diophantine(A,B,D,d,degS,degR,layout)
    sys = dlti(Gnum,Gden,dt=T); k = np.arange(0,kmax+1)
    _, y_step = dlsim_safe(sys, np.ones_like(k), t=k); _, y_ramp = dlsim_safe(sys, 0.2*k, t=k)
    if save:
        ext = '.png' if backend=='mpl' else '.html'
        _plot_series(k,y_step.squeeze(),title='Model Unit-Step Response',backend=backend,path=save+'_step'+ext)
        _plot_series(k,y_ramp.squeeze(),title='Model Unit-Ramp Response',backend=backend,path=save+'_ramp'+ext)
    else:
        _plot_series(k,y_step.squeeze(),title='Model Unit-Step Response',backend=backend,path=None)
        _plot_series(k,y_ramp.squeeze(),title='Model Unit-Ramp Response',backend=backend,path=None)
    if export_json: save_json(export_json, {'A':A,'B':B,'H1':H1,'F':F,'alpha':alpha,'beta':beta,'Gmodel':{'num':Gnum,'den':Gden},'T':T})
    return {'alpha':alpha,'beta':beta}
