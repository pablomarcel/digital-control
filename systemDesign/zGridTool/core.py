# -*- coding: utf-8 -*-
"""
Math core for z-grid curves.
"""
from __future__ import annotations
from typing import Tuple
import numpy as np
import math

def polar_to_cart(r: np.ndarray, theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    return r*np.cos(theta), r*np.sin(theta)

def ring_points(radius: float, n: int = 721):
    th = np.linspace(0, 2*np.pi, n)
    return polar_to_cart(radius*np.ones_like(th), th)

def spiral_const_zeta(zeta: float, theta_max: float, npts: int = 1501):
    if not (0.0 < zeta < 1.0):
        raise ValueError("ζ must be in (0,1) for underdamped spirals.")
    a = zeta / math.sqrt(1.0 - zeta*zeta)
    theta = np.linspace(0.0, float(theta_max), npts)
    r = np.exp(-a * theta)
    return polar_to_cart(r, theta)

def curve_const_wnT(wnT: float, npts: int = 1201):
    zeta = np.linspace(0.0, 0.999, npts)
    r = np.exp(-zeta * wnT)
    theta = wnT * np.sqrt(1.0 - zeta*zeta)
    return polar_to_cart(r, theta)

def ray_theta(theta: float, rmax: float = 1.0):
    return np.array([0.0, rmax*np.cos(theta)]), np.array([0.0, rmax*np.sin(theta)])
