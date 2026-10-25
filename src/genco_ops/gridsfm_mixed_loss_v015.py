"""Versioned KCL precision overlay; no model or native source modification."""

from contextlib import contextmanager
from functools import wraps

import torch

from .gridsfm_flow_repair_v013 import exact_flows


ADAPTER_ID = 'stage_m_exact_impedance_fp64_kcl_v015'


def promote(value):
    if torch.is_tensor(value):
        return value.double() if value.is_floating_point() else value
    if hasattr(value, 'clone') and hasattr(value, 'node_types'):
        return value.clone().apply(promote)
    return value


@contextmanager
def installed(loss):
    names = ('_predicted_flows', '_kcl_residuals', 'kcl_residual_loss')
    originals = {name: getattr(loss, name) for name in names}
    original_flow = loss._flows_rx_bidir
    counts = {name: 0 for name in names}

    def wrap(name, function):
        @wraps(function)
        def call(*args, **kwargs):
            previous = torch.get_default_dtype()
            try:
                # Native accumulators omit dtype. Keep their equations but
                # scope the default to this synchronous physics call only.
                torch.set_default_dtype(torch.float64)
                counts[name] += 1
                return function(*(promote(v) for v in args),
                                **{key: promote(v) for key, v in kwargs.items()})
            finally:
                torch.set_default_dtype(previous)
        return call

    try:
        loss._flows_rx_bidir = exact_flows
        for name, function in originals.items():
            setattr(loss, name, wrap(name, function))
        yield counts
    finally:
        for name, function in originals.items():
            setattr(loss, name, function)
        loss._flows_rx_bidir = original_flow
