
from __future__ import annotations
import numpy as np
from polePlacement.observerTool.design import (
    design_observer, closedloop_poles, compute_k0, select_L, simulate
)

A = '1 0.2; 0 1'
B = '0.02; 0.2'
C = '1 0'
K = '8 3.2'

def test_design_variants_and_closedloop(tmp_path):
    # prediction
    p = design_observer('prediction', A, C, poles='0,0', method='acker', csv='L_pred.csv', out='pred.json')
    assert 'L' in p
    # current
    c = design_observer('current', A, C, poles='0,0', method='acker', csv='L_cur.csv')
    assert 'Lc' in c
    # dlqe
    d = design_observer('dlqe', A, C, G='1 0; 0 1', Qn='1 0; 0 1', Rn='1', csv='L_dlqe.csv', out='dlqe.json')
    assert 'L' in d and 'eig(A-LC)' in d
    # min-order
    m = design_observer('min', A, C, B=B, poles='0', method='acker', csv='Ke.csv', out='min.json')
    assert 'Ke' in m
    # closed loop & separation
    L = p['L']
    sep = closedloop_poles(A, B, C, K, L, out='sep.json')
    assert sep['separation_ok'] is True

def test_k0_select_and_sim(tmp_path):
    Ls = design_observer('prediction', A, C, poles='0,0', method='acker')['L'].tolist()
    # k0 state
    k0s = compute_k0(A, B, C, K, mode='state', out='k0s.json')
    assert k0s['K0'] > 0
    # k0 ogata
    k0o = compute_k0(A, B, C, K, L=Ls, mode='ogata', ogata_extra_gain=1.0, out='k0o.json')
    assert k0o['K0'] > 0
    # select (rule of thumb)
    sel1 = select_L(A, B, C, K, method='place', rule_of_thumb='0.9,0.8', csv='L_sel.csv', out='sel.json')
    assert 'L' in sel1
    # sweep
    sel2 = select_L(A, B, C, K, sweep='0.2,0.2; 0.4+0.1j,0.4-0.1j', steps=5)
    assert 'best_score' in sel2
    # dlqe
    sel3 = select_L(A, B, C, K, dlqe=True, G='1 0; 0 1', Qn='1 0; 0 1', Rn='1')
    assert 'L' in sel3
    # simulate (no plots)
    sim = simulate(A, B, C, K, sel1['L'], N=8, Ts=0.2, ref='step', K0='auto', plot=False, plotly=False, csv='sim.csv', out='sim.json')
    assert 'y' in sim and len(sim['y']) == 8
