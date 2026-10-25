"""Stage L report definitions shared with later, schema-adapted publications."""

import numpy as np
from scipy.stats import spearmanr


def empirical_frontier(rows):
    ordered = rows.sort_values(['l_shed_total', 'r_norm'])
    return ordered.loc[ordered.r_norm.lt(ordered.r_norm.cummin().shift(fill_value=np.inf))]


def topology_incumbent(rows):
    return rows.search_objective.where(rows.eligible).cummin()


def rank_divergence(left, right, final_left, final_right):
    left = left.sort_values(['search_objective', 'topology_key'])
    right = right.sort_values(['search_objective', 'topology_key'])
    aligned = left[['topology_key', 'search_objective']].merge(
        right[['topology_key', 'search_objective']], on='topology_key', validate='one_to_one')
    top_left, top_right = set(left.head(5).topology_key), set(right.head(5).topology_key)
    rho = (float(spearmanr(aligned.search_objective_x, aligned.search_objective_y).statistic)
           if aligned.search_objective_x.nunique() > 1 and aligned.search_objective_y.nunique() > 1 else np.nan)
    return dict(spearman=rho,
                top5_jaccard=len(top_left & top_right) / len(top_left | top_right) if top_left | top_right else np.nan,
                finalist_jaccard=len(final_left & final_right) / len(final_left | final_right)
                    if final_left | final_right else 1.0)
