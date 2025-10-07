
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple
import numpy as np
from .core import poly_conv, poly_add, poly_shift, eval_poly_at_one, deconv_poly_asc

@dataclass
class SimResult:
    t: np.ndarray; r: np.ndarray; y: np.ndarray; u: np.ndarray; v: np.ndarray

class TSelector:
    @staticmethod
    def choose(mode, B, Acl, Ac, Ao, T_manual, integrator, R):
        mode=(mode or "unity_dc").lower()
        B1=eval_poly_at_one(B); Acl1=eval_poly_at_one(Acl); R1=eval_poly_at_one(R)
        if mode=="unity_dc":
            if integrator: return np.array([R1],float)
            if abs(B1)<1e-12: return np.array([1.0],float)
            return np.array([Acl1/B1],float)
        if mode=="ac":
            Ac_use=Ac
            if Ac_use is None and Ao is not None:
                q,r=deconv_poly_asc(Acl, Ao)
                if np.linalg.norm(r)<1e-8: Ac_use=q
            if Ac_use is None: raise ValueError("T 'ac' requires Ac or Acl/Ao.")
            Ac1=eval_poly_at_one(Ac_use)
            if integrator: K=1.0 if abs(Ac1)<1e-12 else (R1/Ac1)
            else:
                denom=B1*Ac1; K=1.0 if abs(denom)<1e-12 else (Acl1/denom)
            return (K*Ac_use).astype(float)
        if mode=="manual":
            if T_manual is None: raise ValueError("T 'manual' requires coefficients.")
            return np.array(T_manual,float)
        raise ValueError("Unknown T mode.")

class Simulator:
    @staticmethod
    def simulate(A,B,d,R,S,Tq,N,r_step,v_step,v_k0,noise_sigma,seed=0):
        rng=np.random.default_rng(seed)
        if abs(A[0]-1.0)>1e-12: B=B/A[0]; A=A/A[0]
        na=len(A)-1; nb=len(B)-1; mS=len(S)-1; mR=len(R)-1; mT=len(Tq)-1
        y=np.zeros(N); u=np.zeros(N); r=np.zeros(N); v=np.zeros(N)
        r[:]=r_step
        if v_step!=0.0 and 0<=v_k0<N: v[v_k0:]=v_step
        def get(arr,k): return 0.0 if k<0 else arr[k]
        for k in range(N):
            noise=rng.normal(0.0,noise_sigma) if noise_sigma>0 else 0.0
            if d>=1:
                Bu=sum(B[j]*get(u,k-d-j) for j in range(0,nb+1))
                Ay=sum(A[i]*get(y,k-i) for i in range(1,na+1))
                y[k]=Bu+v[k]+noise-Ay
                Su=sum(S[i]*get(u,k-i) for i in range(1,mS+1))
                Tr=sum(Tq[i]*get(r,k-i) for i in range(0,mT+1))
                Ry=sum(R[i]*get(y,k-i) for i in range(0,mR+1))
                u[k]=(Tr-Ry-Su)/S[0]
            else:
                Su_hist=sum(S[i]*get(u,k-i) for i in range(1,mS+1))
                Tr=sum(Tq[i]*get(r,k-i) for i in range(0,mT+1))
                Ry_hist=sum(R[i]*get(y,k-i) for i in range(1,mR+1))
                c1=Tr-Su_hist-Ry_hist
                Ay_hist=sum(A[i]*get(y,k-i) for i in range(1,na+1))
                Bu_hist=sum(B[j]*get(u,k-j) for j in range(1,nb+1))
                c2=-Ay_hist+Bu_hist+v[k]+noise
                S0=S[0]; R0=R[0] if mR>=0 else 0.0; B0=B[0] if nb>=0 else 0.0
                det=S0*1.0 + B0*R0
                if abs(det)<1e-12: det+=1e-9
                u[k]=(c1*1.0 - R0*c2)/det
                y[k]=(S0*c2 + B0*c1)/det
        t=np.arange(N); return SimResult(t=t,r=r,y=y,u=u,v=v)

def poly_to_str(p: Sequence[float], var='q')->str:
    terms=[]; 
    for k,c in enumerate(p):
        if abs(c)<1e-14: continue
        if k==0: terms.append(f"{c:.6g}")
        elif k==1: terms.append(f"{c:.6g}{var}")
        else: terms.append(f"{c:.6g}{var}^{k}")
    return ' + '.join(terms) if terms else '0'

def diff_eq_strings(R,S,Tq):
    def rhs(name,p):
        terms=[]
        for i,c in enumerate(p):
            if abs(c)<1e-14: continue
            idx='' if i==0 else f"-{i}"
            terms.append(f"{c:.6g} {name}[k{'' if i==0 else '-'+str(i)}]")
        return ' + '.join(terms) if terms else '0'
    left = rhs('u', S)
    right_T = rhs('r', Tq)
    right_R = rhs('y', R)
    ctrl = f"{left} = ({right_T}) - ({right_R})"
    num=[]
    for i,c in enumerate(Tq):
        if abs(c)>=1e-14: num.append(f"{c:.6g} r[k{'' if i==0 else f'-{i}'}]")
    for i,c in enumerate(R):
        if abs(c)>=1e-14: num.append(f"{-c:.6g} y[k{'' if i==0 else f'-{i}'}]")
    for i,c in enumerate(S[1:],start=1):
        if abs(c)>=1e-14: num.append(f"{-c:.6g} u[k-{i}]")
    ueq = "u[k] = (" + ' + '.join(num) + f") / {S[0]:.6g}"
    return ctrl, ueq
