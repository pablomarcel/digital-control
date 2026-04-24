
from __future__ import annotations
import numpy as np
from .apis import RunRequest, RunResult
from .core import as_float_array, poly_from_q_factors, poly_from_z_poles, DiophantineSolver
from .design import TSelector, Simulator
from .io import load_json, parse_coeffs, parse_complex_list, as_array, save_json_design, save_csv

class RSTApp:
    def run(self, req: RunRequest) -> RunResult:
        from_file = load_json(req.in_json) if req.in_json else {}
        A = as_float_array(req.A) if req.A else as_array(from_file.get("plant",{}).get("A"))
        B = as_float_array(req.B) if req.B else as_array(from_file.get("plant",{}).get("B"))
        d = req.d if req.d is not None else int(from_file.get("plant",{}).get("d",0))
        Ts = req.Ts if req.Ts is not None else float(from_file.get("notes",{}).get("Ts",1.0))
        if A is None or B is None: raise ValueError("Plant A and B must be provided.")
        lead_zeros=0
        for c in B:
            if abs(c)<1e-14: lead_zeros+=1
            else: break
        if lead_zeros>0:
            d+=lead_zeros; B=B[lead_zeros:]
            if len(B)==0: raise ValueError("B(q) cannot be all zeros after removing implicit delay.")
        Ac = as_array(req.Ac) if req.Ac else as_array(from_file.get("target",{}).get("Ac"))
        Ao = as_array(req.Ao) if req.Ao else as_array(from_file.get("target",{}).get("Ao"))
        if req.Acl is not None:
            Acl = as_float_array(req.Acl)
        else:
            base_Acl = poly_from_q_factors(Ac, Ao)
            if req.poles is not None:
                Acl_p = poly_from_z_poles(req.poles); Acl = Acl_p if base_Acl is None else np.convolve(base_Acl, Acl_p)
            elif req.spoles is not None:
                z_roots=[complex(np.exp(s*Ts)) for s in req.spoles]
                Acl_p=poly_from_z_poles(z_roots); Acl=Acl_p if base_Acl is None else np.convolve(base_Acl, Acl_p)
            else:
                Acl_json = as_array(from_file.get("target",{}).get("Acl"))
                if Acl_json is not None: Acl=Acl_json
                elif base_Acl is not None: Acl=base_Acl
                else: raise ValueError("Provide Acl, poles, spoles, or Ac/Ao/JSON to define A_cl(q).")
        degS = req.degS if req.degS is not None else from_file.get("controller",{}).get("degS")
        degR = req.degR if req.degR is not None else from_file.get("controller",{}).get("degR")
        alloc = req.alloc if req.alloc is not None else from_file.get("controller",{}).get("alloc","S")
        integrator = bool(req.integrator or from_file.get("controller",{}).get("integrator",False))
        S,R = DiophantineSolver.solve(A,B,d,Acl,degS,degR,integrator,alloc)
        Tmode = req.Tmode or from_file.get("controller",{}).get("Tmode","unity_dc")
        T_manual = as_array(req.T) if (Tmode=="manual" and req.T is not None) else as_array(from_file.get("controller",{}).get("T"))
        Tq = TSelector.choose(Tmode,B,Acl,Ac, Ao, T_manual, integrator, R)
        N=int(req.N or from_file.get("simulation",{}).get("N",200))
        r_step=float(req.r_step or from_file.get("simulation",{}).get("r_step",1.0))
        v_step=float(req.v_step or from_file.get("simulation",{}).get("v_step",0.0))
        v_k0=int(req.v_k0 or from_file.get("simulation",{}).get("v_k0",0))
        noise_sigma=float(req.noise_sigma or from_file.get("simulation",{}).get("noise_sigma",0.0))
        sim = Simulator.simulate(A,B,d,R,S,Tq,N,r_step,v_step,v_k0,noise_sigma)
        e=sim.r-sim.y; sse=float(abs(e[-1])) if len(e) else 0.0
        y_final=float(sim.y[-1]) if len(sim.y) else 0.0
        u_final=float(sim.u[-1]) if len(sim.u) else 0.0
        rows=[(int(sim.t[k]), float(sim.r[k]), float(sim.y[k]), float(sim.u[k]), float(sim.v[k])) for k in range(len(sim.t))]
        csv_path = save_csv(req.save_csv or "rst.csv", rows)
        payload={'plant':{'A':A.tolist(),'B':B.tolist(),'d':d},
                 'target':{'Acl':Acl.tolist(),'Ac':(Ac.tolist() if Ac is not None else None),'Ao':(Ao.tolist() if Ao is not None else None)},
                 'controller':{'R':R.tolist(),'S':S.tolist(),'T':Tq.tolist(),'Tmode':Tmode,'integrator':integrator,'degS':(int(degS) if degS is not None else None),'degR':(int(degR) if degR is not None else None),'alloc':alloc},
                 'simulation':{'N':N,'r_step':r_step,'v_step':v_step,'v_k0':v_k0,'noise_sigma':noise_sigma},
                 'notes':{'Ts':Ts}}
        json_path = save_json_design(req.export_json or "rst_design.json", payload)
        return RunResult(R=R.tolist(), S=S.tolist(), Tq=Tq.tolist(), Acl=Acl.tolist(), y_final=y_final, u_final=u_final, sse=sse, csv_path=csv_path, json_path=json_path)
