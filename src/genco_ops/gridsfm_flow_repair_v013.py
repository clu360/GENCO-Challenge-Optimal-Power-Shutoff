"""Authorized diagnostic repair: exact positive-impedance native pi-model loss."""

import torch


REPAIR_ID = "stage_m_exact_positive_impedance_loss_v013"


def exact_flows(theta, voltage, i_idx, j_idx, r, x, b_fr, b_to, tau, phi):
    z2 = r * r + x * x
    if not bool(torch.isfinite(z2).all()) or bool((z2 <= 0).any()):
        raise ValueError("zero, underflowed or nonfinite series impedance; no silent regularization")
    g, b = r / z2, -x / z2
    vi, vj = voltage[i_idx], voltage[j_idx]
    vi2, vj2 = vi * vi, vj * vj
    # Preserve the pinned native tap convention; only the series floor changes.
    tau = tau.clamp_min(1e-8)
    inv_tau = 1.0 / tau
    inv_tau2 = inv_tau * inv_tau
    delta = theta[i_idx] - theta[j_idx] - phi
    c, s = torch.cos(delta), torch.sin(delta)
    pij = vi2 * g * inv_tau2 - vi * vj * inv_tau * (g * c + b * s)
    qij = -vi2 * (b + b_fr) * inv_tau2 + vi * vj * inv_tau * (b * c - g * s)
    pji = vj2 * g - vi * vj * inv_tau * (g * c - b * s)
    qji = -vj2 * (b + b_to) + vi * vj * inv_tau * (b * c + g * s)
    return pij, qij, pji, qji
