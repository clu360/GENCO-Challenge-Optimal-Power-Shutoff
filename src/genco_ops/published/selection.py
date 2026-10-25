from .schemas import CandidateResult
def select_finalist(rows: list[CandidateResult]) -> CandidateResult:
    eligible = [row for row in rows if row.eligible and row.search_objective is not None]
    if not eligible:
        raise RuntimeError('evaluator produced no eligible finalist')
    return min(eligible, key=lambda row: (float(row.search_objective), row.k, row.topology_key))
