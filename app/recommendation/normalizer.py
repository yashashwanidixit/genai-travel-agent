from typing import List, Dict


class Normalizer:
    """Provides scaling and normalization utilities for recommendation features."""

    @staticmethod
    def min_max_scale(values: List[float], invert: bool = False) -> List[float]:
        if not values:
            return []
        min_v, max_v = min(values), max(values)
        if max_v == min_v:
            return [1.0 if not invert else 1.0 for _ in values]

        scaled = [(v - min_v) / (max_v - min_v) for v in values]
        if invert:
            scaled = [1.0 - s for s in scaled]
        return scaled

    @staticmethod
    def normalize_feature_matrix(records: List[Dict[str, float]], invert_keys: List[str]) -> List[Dict[str, float]]:
        if not records:
            return []
        keys = records[0].keys()
        normalized_cols = {}

        for k in keys:
            col_vals = [r[k] for r in records]
            invert = k in invert_keys
            normalized_cols[k] = Normalizer.min_max_scale(col_vals, invert=invert)

        out = []
        for i in range(len(records)):
            row = {k: normalized_cols[k][i] for k in keys}
            out.append(row)
        return out
