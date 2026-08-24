"""Recommendation layer.

This package starts with R1 (feature extraction) only. Future stages
(R2 utility normalization, R3 basic recommendation, preference fusion,
ranking, exploration) will be added incrementally as separate modules
so each stage stays independently testable and none of them collapse
into a single monolithic "RecommendationEngine".
"""