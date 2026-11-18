# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""EjariFlow AI: Dubai tenancy contract parsing, RERA rent cap checks, smart index, RDSC risk and portfolio compliance."""

from .notice import generate_90day_notice
from .smart_index import calculate_building_score, evaluate_smart_index
from .rdsc import forecast_eviction_case
from .uaedds import generate_uaedds_schedule, validate_uae_iban

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "generate_90day_notice",
    "calculate_building_score",
    "evaluate_smart_index",
    "forecast_eviction_case",
    "generate_uaedds_schedule",
    "validate_uae_iban"
]

