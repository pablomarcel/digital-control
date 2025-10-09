from __future__ import annotations
from typing import Dict, Any
import sys
import numpy as np

from .apis import RunRequest, DesignResult, ObserverResult, SimResult
from . import io as iox
from .core import (design_servo_ogata, design_servo_aug,
                   design_min_observer, simulate_servo, MinObserver)
from .design import servo_eqs, observer_eqs, emit_equations
from .plot import plot_matplotlib, plot_plotly
import os
from .utils import out_path, timed

def _fit_poles(poles, needed):
    if poles is None:
        return None
    p = list(poles)
    if len(p) == needed:
        return p
    if len(p) < needed:
        # pad with zeros (deadbeat) — common for Ogata
        return p + [0.0]*(needed - len(p))
    return p[:needed]

class ServoApp:
    @timed
    def run(self, req: RunRequest):
        mode = (req.mode or 'design').lower()
        if mode == 'example':
            return self._run_example(req)
        elif mode == 'design':
            return self._run_design(req)
        elif mode == 'observer':
            return self._run_observer(req)
        elif mode == 'sim':
            return self._run_sim(req)
        else:
            raise ValueError(f'Unknown mode: {req.mode}')

    def _merge(self, req: RunRequest) -> Dict[str, Any]:
        cfg = iox.load_yaml(req.config)
        def G(k, default=None): return getattr(req, k) if getattr(req, k) is not None else cfg.get(k, default)
        return {k: G(k) for k in ['G','H','C','K1','K2','Ke','T','poles','which','method','observer_mode','N','ref']}

    # ----------------- modes -----------------
    def _run_example(self, req: RunRequest):
        G = np.array([[0, 1, 0],
                      [0, 0, 1],
                      [-0.12, -0.01, 1.0]], float)
        H = np.array([[0.0],[0.0],[1.0]], float)
        C = np.array([[0.5, 1.0, 0.0]], float)

        K1, K2 = design_servo_ogata(G, H, C, poles=None, method='acker')
        mob = design_min_observer(G, H, C, poles=[0,0], method='acker')

        sim = simulate_servo(G, H, C, K1, K2, N=10, r_type='step', use_observer=False)

        if req.eq:
            eqs = servo_eqs(G, H, C, K1, K2) + observer_eqs('current', Ke_shape=mob.Ke.shape)
            text = emit_equations(eqs, req.eq_file, req.eq_stdout)
            if req.eq_file:
                with open(out_path(req.eq_file), 'w') as f: f.write(text)
            else:
                stream = sys.stdout if req.eq_stdout else sys.stderr
                stream.write(text); stream.flush()

        return {'K1': K1.tolist(), 'K2': K2.tolist(), 'y_end': sim.y[-1], 'u0': sim.k0_u}

    def _run_design(self, req: RunRequest) -> DesignResult:
        M = self._merge(req)
        G = iox.parse_matrix(M['G']); H = iox.parse_matrix(M['H']); C = iox.parse_matrix(M['C'])
        if G is None or H is None or C is None:
            raise ValueError('design requires G,H,C.')
        n = G.shape[0]; m = C.shape[0] if C.ndim == 2 else 1
        poles = _fit_poles( iox.parse_poles(M['poles']), n + m )
        which = (M.get('which') or req.which or 'ogata').lower()
        method = (M.get('method') or req.method or 'acker').lower()

        if which == 'ogata':
            K1, K2 = design_servo_ogata(G, H, C, poles=poles, method=method)
        elif which == 'aug':
            K1, K2 = design_servo_aug(G, H, C, poles=poles, method=method)
        else:
            raise ValueError("--which must be 'ogata' or 'aug'.")

        out_json = out_path(req.out)
        iox.write_json({'K1': K1.tolist(), 'K2': K2.tolist()}, out_json)
        if req.csv:
            import numpy as np
            iox.write_csv_matrix(np.atleast_2d(np.hstack([K2, K1])), out_path(req.csv))

        if req.eq:
            text = emit_equations(servo_eqs(G, H, C, K1, K2), req.eq_file, req.eq_stdout)
            if req.eq_file:
                with open(out_path(req.eq_file), 'w') as f: f.write(text)
            else:
                stream = sys.stdout if req.eq_stdout else sys.stderr
                stream.write(text); stream.flush()

        return DesignResult(K1=K1.tolist(), K2=K2.tolist(), meta={'which': which, 'method': method})

    def _run_observer(self, req: RunRequest) -> ObserverResult:
        M = self._merge(req)
        G = iox.parse_matrix(M['G']); H = iox.parse_matrix(M['H']); C = iox.parse_matrix(M['C'])
        if G is None or H is None or C is None:
            raise ValueError('observer requires G,H,C.')
        n = G.shape[0]; m = C.shape[0] if C.ndim == 2 else 1
        poles = _fit_poles( iox.parse_poles(M['poles']), n - m )
        method = (M.get('method') or req.method or 'acker').lower()

        mob = design_min_observer(G, H, C, poles=poles, method=method)
        out_json = out_path(req.out)
        iox.write_json({'Ke': mob.Ke.tolist(), 'T': mob.T.tolist(),
                        'notes': 'Ke,T are in measured-form coordinates (C*T = [I 0]).'}, out_json)
        if req.csv:
            iox.write_csv_matrix(mob.Ke, out_path(req.csv))

        if req.eq:
            txt = emit_equations(observer_eqs(req.observer_mode, Ke_shape=mob.Ke.shape), req.eq_file, req.eq_stdout)
            if req.eq_file:
                with open(out_path(req.eq_file), 'w') as f: f.write(txt)
            else:
                stream = sys.stdout if req.eq_stdout else sys.stderr
                stream.write(txt); stream.flush()

        return ObserverResult(Ke=mob.Ke.tolist(), T=mob.T.tolist(), notes='C*T=[I 0] measured form')

    def _run_sim(self, req: RunRequest) -> SimResult:
        M = self._merge(req)
        G = iox.parse_matrix(M['G']); H = iox.parse_matrix(M['H']); C = iox.parse_matrix(M['C'])
        if G is None or H is None or C is None:
            raise ValueError('sim requires G,H,C.')

        K1 = iox.force_col(iox.parse_matrix(M['K1'])); K2 = iox.parse_matrix(M['K2'])
        if K1 is None or K2 is None:
            raise ValueError('sim requires K1 and K2.')
        N = int(M.get('N') or req.N or 10)
        rtype = (M.get('ref') or req.ref or 'step')
        use_obs = bool(req.use_observer)
        obs_mode = (M.get('observer_mode') or req.observer_mode or 'current')

        mob = None
        if use_obs:
            Ke = iox.force_col(iox.parse_matrix(M['Ke'])); T  = iox.parse_matrix(M['T'])
            if Ke is None or T is None:
                # Auto-design a min-order observer if not provided
                n = G.shape[0]; m = C.shape[0] if C.ndim == 2 else 1
                poles = _fit_poles( iox.parse_poles(M['poles']), n - m )
                mo = design_min_observer(G, H, C, poles=poles, method=(M.get('method') or req.method or 'acker').lower())
                mob = MinObserver(Ke=mo.Ke, T=mo.T)
            else:
                mob = MinObserver(Ke=Ke, T=T)

        sim = simulate_servo(G, H, C, K1, K2, N=N, r_type=rtype,
                             use_observer=use_obs, minobs=mob, observer_mode=obs_mode)

        if req.csv:
            iox.write_csv_series(sim.y, out_path(req.csv))
        if req.out:
            iox.write_json({'y_end': sim.y[-1], 'u0': sim.k0_u}, out_path(req.out))

        if req.eq:
            eqs = servo_eqs(G, H, C, K1, K2)
            if use_obs and mob is not None:
                eqs += observer_eqs(obs_mode, Ke_shape=mob.Ke.shape if hasattr(mob,'Ke') else None)
            txt = emit_equations(eqs, req.eq_file, req.eq_stdout)
            if req.eq_file:
                with open(out_path(req.eq_file), 'w') as f: f.write(txt)
            else:
                stream = sys.stdout if req.eq_stdout else sys.stderr
                stream.write(txt); stream.flush()


        # Plotting (optional)
        if req.plot and req.savefig:
            savefig_path = out_path(req.savefig)
            if savefig_path:
                os.makedirs(os.path.dirname(savefig_path) or ".", exist_ok=True)
                plot_matplotlib(sim.y, savefig=savefig_path, show=False)

        if req.plotly and req.html:
            html_path = out_path(req.html)
            if html_path:
                os.makedirs(os.path.dirname(html_path) or ".", exist_ok=True)
                plot_plotly(sim.y, html=html_path, open_after=req.open_html)

        return SimResult(y=sim.y, u=sim.u, k0_u=sim.k0_u, summary={'N': N, 'ref': rtype})
