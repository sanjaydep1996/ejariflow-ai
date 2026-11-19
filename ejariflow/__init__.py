# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""EjariFlow AI: Dubai tenancy compliance, RERA smart index, RDSC legal risk, DEWA/Cooling, Golden Visa, and SZR Digital Twin."""

from .notice import generate_90day_notice
from .smart_index import calculate_building_score, evaluate_smart_index
from .rdsc import forecast_eviction_case
from .uaedds import generate_uaedds_schedule, validate_uae_iban
from .dewa_cooling import forecast_tenancy_utilities
from .golden_visa import evaluate_golden_visa_eligibility
from .notice_bot import dispatch_renewal_notice
from .transit_twin import calculate_transit_profile

__version__ = "1.1.0"
__all__ = [
    "__version__",
    "generate_90day_notice",
    "calculate_building_score",
    "evaluate_smart_index",
    "forecast_eviction_case",
    "generate_uaedds_schedule",
    "validate_uae_iban",
    "forecast_tenancy_utilities",
    "evaluate_golden_visa_eligibility",
    "dispatch_renewal_notice",
    "calculate_transit_profile",
]


