"""Portable Stage J adapter, load-service and metric definitions (exact AST export)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

import numpy as np

SOURCE_SHA256 = {'schemas.py': '6cfe263e4dfa77e929c070a4eeb311e81ef8e67df325bea47102084654f27db0', 'contracts.py': '437cc6adbe98577cf4b9b438555ec452e1cc6a52a22467dc437b030306f4b961', 'load_service.py': '80b6e2f5a13ea1dd9dfec2cd4794eebd4c175b6959f64a6e7bf0c147b55f7d94', 'goc500_adapter.py': 'c6161ae6417896c3e4d240ab62ffd9211ac789ec96ccd460f8f7fdb536d97d89', 'metrics.py': '920d035e89669e9fcf3921713d4b83e58900c2af71824c7ee79a92652745e216'}


class EvaluationStatus(str, Enum):
    """Locked Stage J evaluation status labels."""

    OK = "ok"
    DC_INFEASIBLE = "dc_infeasible"
    GRIDSFM_PREPROCESSING_FAILURE = "gridsfm_preprocessing_failure"
    GRIDSFM_INFERENCE_FAILURE = "gridsfm_inference_failure"
    MODEL_OUTPUT_PENALIZED = "model_output_penalized"
    INPUT_INTEGRITY_FAILURE = "input_integrity_failure"
    AC_REFERENCE_INFEASIBLE = "ac_reference_infeasible"
    METHODOLOGY_FAILURE = "methodology_failure"


@dataclass(frozen=True)
class InputIntegrityReport:
    """Hard GridSFM interface invariant report.

    A failed input-integrity report is a methodology failure, not a soft
    candidate penalty.
    """

    checks: dict[str, bool]
    notes: str = ""

    @property
    def d_input(self) -> float:
        if not self.checks:
            return 0.0
        failed = sum(1 for ok in self.checks.values() if not ok)
        return failed / len(self.checks)

    @property
    def evaluation_status(self) -> EvaluationStatus:
        return EvaluationStatus.OK if self.d_input == 0.0 else EvaluationStatus.INPUT_INTEGRITY_FAILURE

    def require_ok(self) -> None:
        if self.evaluation_status is not EvaluationStatus.OK:
            failed = [name for name, ok in self.checks.items() if not ok]
            raise ValueError(f"Stage J input-integrity failure: {failed}. {self.notes}")


@dataclass(frozen=True)
class LoadSheddingBreakdown:
    """Model-independent Stage J load shedding terms."""

    l_shed_total: float
    l_shed_control: float
    l_shed_island: float
    alpha_requested: dict[int, float]
    alpha_effective: dict[int, float]
    source_less_load_ids: tuple[int, ...]


def _coerce_by_load(load_ids: Iterable[int], values: Mapping[int, float] | Iterable[float], name: str) -> dict[int, float]:
    ids = [int(load_id) for load_id in load_ids]
    if isinstance(values, Mapping):
        missing = [load_id for load_id in ids if load_id not in values]
        if missing:
            raise KeyError(f"{name} is missing load ids: {missing}")
        return {load_id: float(values[load_id]) for load_id in ids}

    seq = [float(value) for value in values]
    if len(seq) != len(ids):
        raise ValueError(f"{name} length {len(seq)} does not match load_ids length {len(ids)}")
    return dict(zip(ids, seq))


def compute_alpha_effective(
    load_ids: Iterable[int],
    alpha_requested: Mapping[int, float] | Iterable[float],
    source_less_load_ids: Iterable[int],
) -> dict[int, float]:
    """Apply hard source-less island enforcement to a full per-load alpha vector."""

    ids = [int(load_id) for load_id in load_ids]
    requested = _coerce_by_load(ids, alpha_requested, "alpha_requested")
    source_less = {int(load_id) for load_id in source_less_load_ids}

    unknown_source_less = sorted(source_less.difference(ids))
    if unknown_source_less:
        raise KeyError(f"source_less_load_ids are not in load_ids: {unknown_source_less}")

    effective: dict[int, float] = {}
    for load_id in ids:
        value = requested[load_id]
        if value < 0.0 or value > 1.0:
            raise ValueError(f"alpha_requested[{load_id}] must be in [0, 1], got {value}")
        effective[load_id] = 0.0 if load_id in source_less else value
    return effective


def compute_load_shedding(
    load_ids: Iterable[int],
    pd_pre: Mapping[int, float] | Iterable[float],
    alpha_requested: Mapping[int, float] | Iterable[float],
    source_less_load_ids: Iterable[int],
    *,
    epsilon: float = 1e-6,
) -> LoadSheddingBreakdown:
    """Compute total, control, and island load shedding with no double counting."""

    ids = [int(load_id) for load_id in load_ids]
    source_less = tuple(sorted(int(load_id) for load_id in source_less_load_ids))
    source_less_set = set(source_less)
    demand = _coerce_by_load(ids, pd_pre, "pd_pre")
    requested = _coerce_by_load(ids, alpha_requested, "alpha_requested")
    effective = compute_alpha_effective(ids, requested, source_less)

    total_demand = float(sum(max(0.0, demand[load_id]) for load_id in ids))
    if total_demand <= epsilon:
        raise ValueError(f"total positive demand must exceed epsilon={epsilon}, got {total_demand}")

    island = float(sum(max(0.0, demand[load_id]) for load_id in source_less) / total_demand)
    control = float(
        sum(
            max(0.0, demand[load_id]) * (1.0 - requested[load_id])
            for load_id in ids
            if load_id not in source_less_set
        )
        / total_demand
    )
    total = float(sum(max(0.0, demand[load_id]) * (1.0 - effective[load_id]) for load_id in ids) / total_demand)

    if not np.isclose(total, control + island, atol=1e-9):
        raise AssertionError("load shedding decomposition failed: total != control + island")

    return LoadSheddingBreakdown(
        l_shed_total=total,
        l_shed_control=control,
        l_shed_island=island,
        alpha_requested={load_id: requested[load_id] for load_id in ids},
        alpha_effective=effective,
        source_less_load_ids=source_less,
    )


LOAD_PD_IDX = 0


LOAD_QD_IDX = 1


AC_LINE_RATE_A_IDX = 6


TR_RATE_A_IDX = 4


TR_TAP_IDX = 7


TR_SHIFT_IDX = 8


AC_LINE_FAMILY = "ac_line"


TRANSFORMER_FAMILY = "transformer"


PREPARED_NODE_TYPES = ("branch_ac", "branch_tr", "cycle")


PREPARED_EDGE_MARKERS = ("endpoint_of", "in_cycle")


@dataclass(frozen=True)
class BranchIdentity:
    """Immutable mapping between Stage J physical IDs and GridSFM edge rows."""

    canonical_branch_id: int
    original_case_branch_id: int
    edge_family: str
    family_index: int
    from_bus_id: int
    to_bus_id: int
    from_bus_index: int
    to_bus_index: int
    orientation_sign: int
    rate_a: float
    is_risk: bool
    is_candidate: bool


@dataclass(frozen=True)
class LoadIdentity:
    """Immutable mapping between Stage J load IDs and GridSFM load rows."""

    canonical_load_id: int
    load_index: int
    bus_id: int
    bus_index: int
    pd_pre: float
    qd_pre: float


@dataclass(frozen=True)
class GOC500Identity:
    """Canonical identity tables extracted from raw GridSFM GOC-500 JSON."""

    branches: tuple[BranchIdentity, ...]
    loads: tuple[LoadIdentity, ...]
    bus_ids: tuple[int, ...]
    generator_bus_ids: tuple[int, ...]

    @property
    def branch_by_id(self) -> dict[int, BranchIdentity]:
        return {record.canonical_branch_id: record for record in self.branches}

    @property
    def load_by_id(self) -> dict[int, LoadIdentity]:
        return {record.canonical_load_id: record for record in self.loads}


def assert_raw_gridsfm_case(raw_case: Mapping[str, Any]) -> InputIntegrityReport:
    """Validate that Stage J is mutating raw `.pyg.json`, not prepared data."""

    grid = raw_case.get("grid") if isinstance(raw_case, Mapping) else None
    nodes = grid.get("nodes", {}) if isinstance(grid, Mapping) else {}
    edges = grid.get("edges", {}) if isinstance(grid, Mapping) else {}
    checks = {
        "has_grid": isinstance(grid, Mapping),
        "has_nodes": isinstance(nodes, Mapping),
        "has_edges": isinstance(edges, Mapping),
        "has_bus_nodes": bool(nodes.get("bus")),
        "has_load_nodes": "load" in nodes,
        "has_branch_edges": AC_LINE_FAMILY in edges or TRANSFORMER_FAMILY in edges,
        "not_prepared_branch_nodes": not any(node_type in nodes for node_type in PREPARED_NODE_TYPES),
        "not_prepared_auxiliary_edges": not any(marker in str(edge_type) for edge_type in edges for marker in PREPARED_EDGE_MARKERS),
    }
    return InputIntegrityReport(
        checks=checks,
        notes="Stage J must mutate raw topology/load before official GridSFM prepare_for_inference.",
    )


def _edge_block(raw_case: Mapping[str, Any], family: str) -> Mapping[str, Any]:
    return raw_case["grid"]["edges"][family]


def _edge_features(block: Mapping[str, Any]) -> list[list[float]]:
    if "features" in block:
        return block["features"]
    if "edge_attr" in block:
        return block["edge_attr"]
    raise KeyError("GridSFM edge block has neither features nor edge_attr")


def _branch_ids(metadata: Mapping[str, Any], family: str, count: int) -> list[int]:
    key = "ac_line_branch_ids" if family == AC_LINE_FAMILY else "transformer_branch_ids"
    values = metadata.get(key)
    if values is None:
        return list(range(count))
    if len(values) != count:
        raise ValueError(f"metadata {key} length {len(values)} != {family} edge count {count}")
    return [int(value) for value in values]


def build_goc500_identity(
    raw_case: Mapping[str, Any],
    *,
    candidate_branch_ids: Iterable[int] | None = None,
    risk_families: Iterable[str] = (AC_LINE_FAMILY,),
) -> GOC500Identity:
    """Build canonical branch/load identity from GridSFM raw `.pyg.json`."""

    assert_raw_gridsfm_case(raw_case).require_ok()

    metadata = raw_case.get("metadata", {})
    bus_ids = tuple(int(value) for value in metadata.get("bus_id_map", range(len(raw_case["grid"]["nodes"]["bus"]))))
    risk_family_set = {str(family) for family in risk_families}
    candidate_set = {int(branch_id) for branch_id in candidate_branch_ids or []}

    branches: list[BranchIdentity] = []
    for family, rate_idx in ((AC_LINE_FAMILY, AC_LINE_RATE_A_IDX), (TRANSFORMER_FAMILY, TR_RATE_A_IDX)):
        if family not in raw_case["grid"]["edges"]:
            continue
        block = _edge_block(raw_case, family)
        features = _edge_features(block)
        senders = block["senders"]
        receivers = block["receivers"]
        if len(senders) != len(receivers) or len(senders) != len(features):
            raise ValueError(f"{family} senders/receivers/features lengths do not match")
        branch_ids = _branch_ids(metadata, family, len(features))
        for idx, (branch_id, sender, receiver, attrs) in enumerate(zip(branch_ids, senders, receivers, features)):
            if rate_idx >= len(attrs):
                raise ValueError(f"{family}[{idx}] missing rateA column {rate_idx}")
            rate_a = float(attrs[rate_idx])
            branches.append(
                BranchIdentity(
                    canonical_branch_id=int(branch_id),
                    original_case_branch_id=int(branch_id),
                    edge_family=family,
                    family_index=int(idx),
                    from_bus_id=bus_ids[int(sender)],
                    to_bus_id=bus_ids[int(receiver)],
                    from_bus_index=int(sender),
                    to_bus_index=int(receiver),
                    orientation_sign=1,
                    rate_a=rate_a,
                    is_risk=family in risk_family_set,
                    is_candidate=int(branch_id) in candidate_set,
                )
            )

    load_rows = raw_case["grid"]["nodes"].get("load", [])
    load_ids = metadata.get("load_id_map", range(len(load_rows)))
    load_bus_map = metadata.get("load_bus_map")
    if len(load_ids) != len(load_rows):
        raise ValueError("metadata load_id_map length does not match load rows")

    if load_bus_map is None:
        link = raw_case["grid"]["edges"]["load_link"]
        load_to_bus = link["receivers"]
        load_bus_ids = [bus_ids[int(bus_idx)] for bus_idx in load_to_bus]
    else:
        load_bus_ids = [int(value) for value in load_bus_map]
    if len(load_bus_ids) != len(load_rows):
        raise ValueError("load_bus_map length does not match load rows")

    bus_id_to_index = {bus_id: idx for idx, bus_id in enumerate(bus_ids)}
    loads = tuple(
        LoadIdentity(
            canonical_load_id=int(load_id),
            load_index=int(idx),
            bus_id=int(bus_id),
            bus_index=int(bus_id_to_index[int(bus_id)]),
            pd_pre=float(row[LOAD_PD_IDX]),
            qd_pre=float(row[LOAD_QD_IDX]),
        )
        for idx, (load_id, bus_id, row) in enumerate(zip(load_ids, load_bus_ids, load_rows))
    )

    generator_bus_ids = tuple(int(value) for value in metadata.get("gen_bus_map", []))

    return GOC500Identity(branches=tuple(branches), loads=loads, bus_ids=bus_ids, generator_bus_ids=generator_bus_ids)


def require_valid_risk_ratings(identity: GOC500Identity, *, epsilon: float = 1e-9) -> None:
    """Validate finite positive rateA values for branches entering wildfire risk."""

    for branch in identity.branches:
        if branch.is_risk and (not np.isfinite(branch.rate_a) or branch.rate_a <= epsilon):
            raise ValueError(f"risk branch {branch.canonical_branch_id} has invalid rateA {branch.rate_a}")


def source_less_load_ids(identity: GOC500Identity, offline_branch_ids: Iterable[int]) -> tuple[int, ...]:
    """Return load IDs in components without any generator source."""

    offline = {int(branch_id) for branch_id in offline_branch_ids}
    parent = {bus_id: bus_id for bus_id in identity.bus_ids}

    def find(bus_id: int) -> int:
        while parent[bus_id] != bus_id:
            parent[bus_id] = parent[parent[bus_id]]
            bus_id = parent[bus_id]
        return bus_id

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for branch in identity.branches:
        if branch.canonical_branch_id not in offline:
            union(branch.from_bus_id, branch.to_bus_id)

    source_roots = {find(bus_id) for bus_id in identity.generator_bus_ids if bus_id in parent}
    return tuple(sorted(load.canonical_load_id for load in identity.loads if find(load.bus_id) not in source_roots))


def _filter_edge_rows(raw_case: dict[str, Any], family: str, keep_mask: list[bool]) -> None:
    block = raw_case["grid"]["edges"][family]
    for key in ("senders", "receivers", "features", "edge_attr"):
        if key in block:
            block[key] = [row for row, keep in zip(block[key], keep_mask) if keep]

    solution_edges = raw_case.get("solution", {}).get("edges", {})
    if family in solution_edges:
        solution_edges[family] = [row for row, keep in zip(solution_edges[family], keep_mask) if keep]


def mutate_raw_case_for_candidate(
    raw_case: Mapping[str, Any],
    identity: GOC500Identity,
    *,
    offline_branch_ids: Iterable[int],
    alpha_requested: Mapping[int, float],
) -> tuple[dict[str, Any], LoadSheddingBreakdown, InputIntegrityReport]:
    """Apply Stage J candidate `(z, alpha)` to raw GridSFM JSON.

    The returned case is still raw GridSFM JSON. The caller must pass it through
    official `load_pyg_json` / `prepare_for_inference` in the GridSFM env.
    """

    assert_raw_gridsfm_case(raw_case).require_ok()

    offline = {int(branch_id) for branch_id in offline_branch_ids}
    branch_by_id = identity.branch_by_id
    unknown = sorted(offline.difference(branch_by_id))
    if unknown:
        raise KeyError(f"offline branches are not in identity: {unknown}")

    mutated = deepcopy(raw_case)
    source_less = source_less_load_ids(identity, offline)
    load_ids = [record.canonical_load_id for record in identity.loads]
    pd_pre = {record.canonical_load_id: record.pd_pre for record in identity.loads}
    qd_pre = {record.canonical_load_id: record.qd_pre for record in identity.loads}
    breakdown = compute_load_shedding(load_ids, pd_pre, alpha_requested, source_less)
    alpha_effective = compute_alpha_effective(load_ids, alpha_requested, source_less)

    for load in identity.loads:
        row = mutated["grid"]["nodes"]["load"][load.load_index]
        row[LOAD_PD_IDX] = float(alpha_effective[load.canonical_load_id]) * pd_pre[load.canonical_load_id]
        row[LOAD_QD_IDX] = float(alpha_effective[load.canonical_load_id]) * qd_pre[load.canonical_load_id]

    for family in (AC_LINE_FAMILY, TRANSFORMER_FAMILY):
        family_records = [branch for branch in identity.branches if branch.edge_family == family]
        if not family_records or family not in mutated["grid"]["edges"]:
            continue
        keep_mask = [branch.canonical_branch_id not in offline for branch in family_records]
        _filter_edge_rows(mutated, family, keep_mask)
        metadata_key = "ac_line_branch_ids" if family == AC_LINE_FAMILY else "transformer_branch_ids"
        if metadata_key in mutated.get("metadata", {}):
            mutated["metadata"][metadata_key] = [
                branch.canonical_branch_id for branch in family_records if branch.canonical_branch_id not in offline
            ]

    mutated.setdefault("metadata", {})["stage_j_mutation"] = {
        "mutation_level": "raw_pyg_json_before_prepare_for_inference",
        "offline_branch_ids": sorted(offline),
        "active_branch_ids": sorted(set(branch_by_id).difference(offline)),
        "alpha_requested": {str(load_id): float(alpha_requested[load_id]) for load_id in load_ids},
        "alpha_effective": {str(load_id): float(alpha_effective[load_id]) for load_id in load_ids},
        "source_less_load_ids": [int(load_id) for load_id in breakdown.source_less_load_ids],
        "l_shed_total": breakdown.l_shed_total,
        "l_shed_control": breakdown.l_shed_control,
        "l_shed_island": breakdown.l_shed_island,
        "official_preprocessing_required_next": True,
    }

    report = validate_candidate_mutation(raw_case, mutated, identity, offline, alpha_effective)
    report.require_ok()
    return mutated, breakdown, report


def validate_candidate_mutation(
    raw_case: Mapping[str, Any],
    mutated_case: Mapping[str, Any],
    identity: GOC500Identity,
    offline_branch_ids: Iterable[int],
    alpha_effective: Mapping[int, float],
    *,
    atol: float = 1e-10,
) -> InputIntegrityReport:
    """Validate hard input invariants after raw candidate mutation."""

    offline = {int(branch_id) for branch_id in offline_branch_ids}
    checks: dict[str, bool] = {}

    checks["bus_nodes_preserved"] = raw_case["grid"]["nodes"]["bus"] == mutated_case["grid"]["nodes"]["bus"]
    checks["generator_nodes_preserved"] = raw_case["grid"]["nodes"].get("generator", []) == mutated_case["grid"]["nodes"].get("generator", [])
    raw_report = assert_raw_gridsfm_case(mutated_case)
    checks["raw_schema_not_prepared_after_mutation"] = raw_report.d_input == 0.0

    load_checks = []
    for load in identity.loads:
        row = mutated_case["grid"]["nodes"]["load"][load.load_index]
        load_checks.append(abs(float(row[LOAD_PD_IDX]) - alpha_effective[load.canonical_load_id] * load.pd_pre) <= atol)
        load_checks.append(abs(float(row[LOAD_QD_IDX]) - alpha_effective[load.canonical_load_id] * load.qd_pre) <= atol)
    checks["load_commands_match_alpha_effective"] = all(load_checks)
    mutation_md = mutated_case.get("metadata", {}).get("stage_j_mutation", {})
    checks["full_alpha_requested_saved"] = len(mutation_md.get("alpha_requested", {})) == len(identity.loads)
    checks["full_alpha_effective_saved"] = len(mutation_md.get("alpha_effective", {})) == len(identity.loads)
    checks["mutation_marked_raw_before_preprocessing"] = (
        mutation_md.get("mutation_level") == "raw_pyg_json_before_prepare_for_inference"
        and mutation_md.get("official_preprocessing_required_next") is True
    )

    for family in (AC_LINE_FAMILY, TRANSFORMER_FAMILY):
        metadata_key = "ac_line_branch_ids" if family == AC_LINE_FAMILY else "transformer_branch_ids"
        expected = [
            branch.canonical_branch_id
            for branch in identity.branches
            if branch.edge_family == family and branch.canonical_branch_id not in offline
        ]
        observed = [int(value) for value in mutated_case.get("metadata", {}).get(metadata_key, [])]
        checks[f"{family}_metadata_branch_ids_match_topology"] = observed == expected
        if family in mutated_case["grid"]["edges"]:
            block = mutated_case["grid"]["edges"][family]
            features = _edge_features(block)
            checks[f"{family}_edge_lengths_match"] = len(block["senders"]) == len(block["receivers"]) == len(features) == len(expected)

    return InputIntegrityReport(checks=checks)


def require_positive_ratea(ratea_by_line: Mapping[int, float], line_ids: Iterable[int], *, epsilon: float = 1e-9) -> None:
    """Raise if any risk branch lacks a finite positive thermal rating."""

    for line_id in line_ids:
        value = float(ratea_by_line[int(line_id)])
        if not np.isfinite(value) or value <= epsilon:
            raise ValueError(f"rateA for line {line_id} must be finite and positive, got {value}")


def compute_ac_loading_two_ended(
    p_from: Mapping[int, float],
    q_from: Mapping[int, float],
    p_to: Mapping[int, float],
    q_to: Mapping[int, float],
    ratea_by_line: Mapping[int, float],
    line_ids: Iterable[int],
) -> dict[int, float]:
    """Compute AC/GridSFM branch loading using the larger apparent flow at either end."""

    ids = [int(line_id) for line_id in line_ids]
    require_positive_ratea(ratea_by_line, ids)
    loading: dict[int, float] = {}
    for line_id in ids:
        s_from = float(np.hypot(float(p_from[line_id]), float(q_from[line_id])))
        s_to = float(np.hypot(float(p_to[line_id]), float(q_to[line_id])))
        loading[line_id] = max(s_from, s_to) / float(ratea_by_line[line_id])
    return loading


def compute_r_base(
    p_env_by_line: Mapping[int, float],
    baseline_loading_by_line: Mapping[int, float],
    risk_line_ids: Iterable[int],
    *,
    epsilon: float = 1e-6,
) -> float:
    """Compute and validate the shared Stage J risk denominator."""

    total = 0.0
    for line_id in risk_line_ids:
        lid = int(line_id)
        p_env = float(p_env_by_line[lid])
        loading = float(baseline_loading_by_line[lid])
        if not np.isfinite(p_env) or not np.isfinite(loading):
            raise ValueError(f"nonfinite R_base input for line {lid}")
        total += p_env * loading * loading
    if total <= epsilon:
        raise ValueError(f"R_base must exceed epsilon={epsilon}, got {total}")
    return float(total)


def compute_j_trade(lambda_r: float, r_norm: float, l_shed_total: float) -> float:
    """Compute the weighted wildfire/service tradeoff objective."""

    if lambda_r < 0.0 or lambda_r > 1.0:
        raise ValueError(f"lambda_r must be in [0, 1], got {lambda_r}")
    return float(lambda_r * r_norm + (1.0 - lambda_r) * l_shed_total)
