
"""Versioned fixed-budget Powell blocks, independent of model/physics adapters."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Callable
import numpy as np
from scipy.optimize import minimize
PF_SEARCH_ID = 'stage_m_r_then_alpha_powell_v001'
ALPHA_SEARCH_ID = 'stage_m_alpha_only_powell_v001'

@dataclass(frozen=True)
class SearchResult:
    search_id: str
    best_x: tuple[float, ...]
    best_payload: dict | None
    trace: tuple[dict, ...]
    blocks: tuple[dict, ...]

class _BudgetStop(Exception):
    pass

def sequential_powell(*, alpha0, alpha_bounds, r0=(), r_bounds=(), evaluate: Callable[[tuple[float, ...]], dict]) -> SearchResult:
    """Evaluate x=(alpha,r). The adapter owns unchanged scoring and physical mapping.

    Payloads use Stage L's eligible/search_objective keys. Optional effective_x
    must describe actual alpha/r commands; absent that, physical coverage is
    explicitly unverified, even when optimizer coordinates have changed.
    """
    initial = tuple((float(v) for v in (*alpha0, *r0)))
    bounds = tuple((tuple(map(float, b)) for b in (*alpha_bounds, *r_bounds)))
    na, nr = (len(alpha0), len(r0))
    if not na or len(alpha_bounds) != na or len(r_bounds) != nr:
        raise ValueError('invalid alpha/r dimensions')
    if any((not isfinite(v) for v in initial)):
        raise ValueError('initial commands must be finite')
    if any((not (isfinite(lo) and isfinite(hi) and (lo < hi) and (lo <= v <= hi)) for v, (lo, hi) in zip(initial, bounds, strict=True))):
        raise ValueError('invalid bounds or initial commands')

    def canonical(value, lo, hi):
        return float(np.clip(round(float(np.clip(value, lo, hi)), 12), lo, hi))
    initial = tuple((canonical(v, lo, hi) for v, (lo, hi) in zip(initial, bounds, strict=True)))
    cache: dict[tuple, dict] = {}
    trace, blocks = ([], [])
    incumbent, best_payload, best_score = (initial, None, float('inf'))

    def run_block(name, indices, budget):
        nonlocal incumbent, best_payload, best_score
        start = incumbent
        calls = cache_hits = attempts = 0
        start_trace = len(trace)

        def objective(values):
            nonlocal calls, cache_hits, attempts, incumbent, best_payload, best_score
            attempts += 1
            x = list(start)
            for i, value in zip(indices, values, strict=True):
                lo, hi = bounds[i]
                x[i] = canonical(value, lo, hi)
            x = tuple(x)
            if x in cache:
                cache_hits += 1
                payload = cache[x]
            else:
                if calls >= budget or len(trace) >= 20:
                    raise _BudgetStop
                calls += 1
                try:
                    payload = dict(evaluate(x))
                except Exception as exc:
                    payload = {'eligible': False, 'search_objective': None, 'status': 'EVALUATOR_EXCEPTION', 'message': repr(exc)}
                value = payload.get('search_objective')
                try:
                    valid = bool(payload.get('eligible')) and value is not None and isfinite(float(value))
                except (TypeError, ValueError):
                    valid = False
                improved = valid and float(value) < best_score
                if improved:
                    incumbent, best_payload, best_score = (x, payload, float(value))
                effective = payload.get('effective_x')
                if effective is not None:
                    if len(effective) != len(initial) or any((not isfinite(float(v)) for v in effective)):
                        raise ValueError('adapter returned invalid effective_x')
                    effective = list(map(float, effective))
                cache[x] = payload
                trace.append({'evaluation_index': len(trace) + 1, 'block': name, 'block_evaluation_index': calls, 'x': list(x), 'effective_x': effective, 'eligible': valid, 'search_objective': float(value) if valid else None, 'status': payload.get('status'), 'message': payload.get('message'), 'incumbent_improved': bool(improved)})
            value = payload.get('search_objective')
            try:
                return float(value) if payload.get('eligible') and value is not None and isfinite(float(value)) else 1000000000000.0
            except (TypeError, ValueError):
                return 1000000000000.0
        objective([start[i] for i in indices])
        termination = 'NO_SEARCH'
        if calls < budget:
            try:
                result = minimize(objective, np.asarray([start[i] for i in indices]), method='Powell', bounds=[bounds[i] for i in indices], options={'maxfev': budget * 10, 'disp': False})
                termination = str(result.message)
            except _BudgetStop:
                termination = 'ACTUAL_EVALUATION_CAP'
        rows = trace[start_trace:]
        touched = [i for i in indices if any((row['x'][i] != start[i] for row in rows))]
        anchor = cache[start].get('effective_x')
        effective_touched = None if anchor is None or any((row['effective_x'] is None for row in rows)) else [i for i in indices if any((row['effective_x'][i] != float(anchor[i]) for row in rows))]
        blocks.append({'block': name, 'budget': budget, 'actual_evaluations': calls, 'cache_hits': cache_hits, 'optimizer_attempts': attempts, 'termination': termination, 'requested_coordinates_touched': touched, 'effective_coordinates_touched': effective_touched, 'untouched_coordinates': [i for i in indices if i not in touched], 'physical_coverage_verified': effective_touched is not None, 'effective_probe_observed': bool(effective_touched)})
    if nr:
        run_block('r', tuple(range(na, na + nr)), 10)
        if best_payload is not None:
            run_block('alpha', tuple(range(na)), 10)
        search_id = PF_SEARCH_ID
    else:
        run_block('alpha', tuple(range(na)), 20)
        search_id = ALPHA_SEARCH_ID
    return SearchResult(search_id, incumbent, best_payload, tuple(trace), tuple(blocks))
