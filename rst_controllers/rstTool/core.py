
from __future__ import annotations
from typing import Sequence, Tuple, Optional
import numpy as np

def as_float_array(x: Sequence[float]) -> np.ndarray: return np.array(x, float)
def poly_conv(a, b): return np.convolve(a, b)
def poly_add(a, b):
    L=max(len(a),len(b)); aa=np.pad(a,(0,L-len(a))); bb=np.pad(b,(0,L-len(b))); return aa+bb
def poly_shift(p, d): return p if d<=0 else np.pad(p,(d,0))
def poly_from_z_poles(poles):
    out=np.array([1.0],complex)
    for z in poles: out=np.convolve(out,np.array([1.0,-z],complex))
    return np.real_if_close(out,1e-8).astype(float)
def poly_from_q_factors(ac, ao):
    if ac is None and ao is None: return None
    if ac is None: return ao.copy()
    if ao is None: return ac.copy()
    return np.convolve(ac, ao)
def eval_poly_at_one(p): return float(np.sum(p))
def deconv_poly_asc(num, den):
    qd, rd = np.polydiv(num[::-1], den[::-1])
    q = np.real_if_close(qd[::-1],1e-9).astype(float)
    r = np.real_if_close(rd[::-1],1e-9).astype(float)
    eps=1e-10
    while len(q)>1 and abs(q[-1])<eps: q=q[:-1]
    while len(r)>1 and abs(r[-1])<eps: r=r[:-1]
    if len(q)==0: q=np.array([0.0])
    if len(r)==0: r=np.array([0.0])
    return q, r
def stable_all(roots, tol=1-1e-10): return np.all(np.abs(roots)<tol)

class DiophantineSolver:
    @staticmethod
    def recommended_degrees(A,B,d,Acl,integrator,alloc):
        na=len(A)-1; nb=len(B)-1; Nc=len(Acl)-1; N0=na+d+nb-1; m=max(0,Nc-N0)
        if alloc.lower()=="r":
            return max(0,d+nb-1), max(0,na-1+m)
        else:
            return max(0,d+nb-1+m), max(0,na-1)

    @staticmethod
    def _build_conv_matrix(base,out_len,shift,cols):
        M=np.zeros((out_len,cols)); nb=len(base)
        for j in range(cols):
            for i in range(nb):
                k=i+j+shift
                if 0<=k<out_len: M[k,j]=base[i]
        return M

    @staticmethod
    def _ensure_rows_cover(Acl, base_A, B, d, degS_hat, degR):
        highest_MA_row = degS_hat + (len(base_A)-1)
        highest_MB_row = d + degR
        need = max(len(Acl), highest_MA_row+1, highest_MB_row+1)
        if len(Acl)<need: return np.pad(Acl,(0,need-len(Acl)))
        return Acl

    @classmethod
    def solve(cls, A,B,d,Acl,degS,degR,integrator,alloc):
        A=A.astype(float); B=B.astype(float); Acl=Acl.astype(float)
        if abs(A[0]-1.0)>1e-12: Acl/=A[0]; B/=A[0]; A/=A[0]
        degS_rec,degR_rec=cls.recommended_degrees(A,B,d,Acl,integrator,alloc)
        degS_tar=degS_rec if degS is None else max(0,int(degS))
        degR_tar=degR_rec if degR is None else max(0,int(degR))
        degS_eff,degR_eff=degS_tar,degR_tar
        S_fac = np.array([1.0,-1.0]) if integrator else np.array([1.0])
        base_A = np.convolve(A,S_fac)
        def n_unknowns(dS,dR): dS_hat=max(0,dS-(1 if integrator else 0)); return (dS_hat+1)+(dR+1)
        Acl_eff = cls._ensure_rows_cover(Acl, base_A,B,d, max(0,degS_eff-(1 if integrator else 0)), degR_eff)
        while n_unknowns(degS_eff,degR_eff)>len(Acl_eff):
            if degS_eff>degS_rec: degS_eff-=1
            elif degR_eff>degR_rec: degR_eff-=1
            else:
                if degS_eff>0: degS_eff-=1
                elif degR_eff>0: degR_eff-=1
                else: break
            Acl_eff = cls._ensure_rows_cover(Acl, base_A,B,d, max(0,degS_eff-(1 if integrator else 0)), degR_eff)
        degS_hat=max(0,degS_eff-(1 if integrator else 0)); nS=degS_hat+1; nR=degR_eff+1
        MA=cls._build_conv_matrix(base_A,len(Acl_eff),0,nS)
        MB=cls._build_conv_matrix(B,len(Acl_eff),d,nR)
        Phi=np.block([MA,MB]); bvec=Acl_eff.copy()
        for _ in range(10):
            x,_,rank,_=np.linalg.lstsq(Phi,bvec,rcond=None)
            if rank==Phi.shape[1]: break
            shrunk=False
            if degS_eff>degS_rec and nS>1:
                degS_eff-=1; degS_hat=max(0,degS_eff-(1 if integrator else 0)); nS=degS_hat+1; MA=cls._build_conv_matrix(base_A,len(Acl_eff),0,nS); Phi=np.block([MA,MB]); shrunk=True
            elif degR_eff>degR_rec and nR>1:
                degR_eff-=1; nR=degR_eff+1; MB=cls._build_conv_matrix(B,len(Acl_eff),d,nR); Phi=np.block([MA,MB]); shrunk=True
            if not shrunk: x=np.linalg.pinv(Phi)@bvec; break
        S_hat=x[:nS]; R=x[nS:]; S=np.convolve(S_fac,S_hat)
        if len(S)<degS_tar+1: S=np.pad(S,(0,degS_tar+1-len(S)))
        if len(R)<degR_tar+1: R=np.pad(R,(0,degR_tar+1-len(R)))
        return np.real_if_close(S,1e-9).astype(float), np.real_if_close(R,1e-9).astype(float)
