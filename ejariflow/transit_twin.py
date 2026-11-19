"""Interactive Dubai Metro Transit & Commute Isochrone Twin.

Models the Dubai Metro Red Line viaduct running along Sheikh Zayed Road (SZR):
- Key stations along SZR:
    * World Trade Centre (WTC)
    * Emirates Towers
    * Financial Centre (DIFC)
    * Burj Khalifa / Dubai Mall
    * Business Bay
- 5-minute (400m) and 10-minute (800m) pedestrian walk-shed isochrone rings.
- Real-time transit commute matrices to major Dubai job hubs:
    * DIFC Gate Building
    * Downtown Dubai / Dubai Mall
    * Dubai International Airport (DXB Terminal 3)
    * Dubai Marina / DMCC
- Calculates Transit Mobility Index (0 to 100) for any property along the corridor.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math

# Dubai Metro Red Line Stations along Sheikh Zayed Road Corridor
METRO_STATIONS = [
    {
        "id": "ST-WTC",
        "name": "World Trade Centre",
        "name_ar": "المركز التجاري العالمي",
        "code": "R22",
        "szr_position": {"x": 300.0, "z": -50.0},
        "line": "Red Line",
        "commutes": {
            "difc": 3,
            "downtown": 7,
            "dxb_t3": 18,
            "dubai_marina": 26,
        }
    },
    {
        "id": "ST-EMIRATES",
        "name": "Emirates Towers",
        "name_ar": "أبراج الإمارات",
        "code": "R23",
        "szr_position": {"x": 160.0, "z": -48.0},
        "line": "Red Line",
        "commutes": {
            "difc": 2,
            "downtown": 5,
            "dxb_t3": 21,
            "dubai_marina": 23,
        }
    },
    {
        "id": "ST-FINANCIAL",
        "name": "Financial Centre",
        "name_ar": "المركز المالي",
        "code": "R24",
        "szr_position": {"x": 10.0, "z": -46.0},
        "line": "Red Line",
        "commutes": {
            "difc": 1,
            "downtown": 4,
            "dxb_t3": 23,
            "dubai_marina": 21,
        }
    },
    {
        "id": "ST-BURJ",
        "name": "Burj Khalifa / Dubai Mall",
        "name_ar": "برج خليفة / دبي مول",
        "code": "R25",
        "szr_position": {"x": -150.0, "z": -45.0},
        "line": "Red Line",
        "commutes": {
            "difc": 4,
            "downtown": 2,
            "dxb_t3": 26,
            "dubai_marina": 18,
        }
    },
    {
        "id": "ST-BUSINESSBAY",
        "name": "Business Bay",
        "name_ar": "الخليج التجاري",
        "code": "R26",
        "szr_position": {"x": -310.0, "z": -45.0},
        "line": "Red Line",
        "commutes": {
            "difc": 6,
            "downtown": 4,
            "dxb_t3": 29,
            "dubai_marina": 15,
        }
    }
]

# Destination Hub Profiles
DESTINATION_HUBS = {
    "difc": {"name": "DIFC Gate Precinct", "icon": "🏛️", "desc": "Prime financial district"},
    "downtown": {"name": "Downtown Dubai & Dubai Mall", "icon": "🏙️", "desc": "Tourism & commercial hub"},
    "dxb_t3": {"name": "Dubai International Airport (DXB)", "icon": "✈️", "desc": "Global aviation hub"},
    "dubai_marina": {"name": "Dubai Marina & DMCC", "icon": "⛵", "desc": "Freezone & waterfront lifestyle"},
}


def find_nearest_metro_station(x: float, z: float) -> Dict[str, Any]:
    """Find the nearest Dubai Metro station and compute walking distance in meters."""
    best_station = None
    min_dist_m = float("inf")
    
    # 1 unit in our 3D space is approx 2.5 meters in real scale along SZR
    SCALE_FACTOR = 2.5
    
    for s in METRO_STATIONS:
        sx = s["szr_position"]["x"]
        sz = s["szr_position"]["z"]
        dx = (x - sx) * SCALE_FACTOR
        dz = (z - sz) * SCALE_FACTOR
        dist = math.hypot(dx, dz)
        if dist < min_dist_m:
            min_dist_m = dist
            best_station = s
            
    # Walking speed in Dubai climate: ~4.5 km/h (75 meters / minute)
    walk_mins = max(1, round(min_dist_m / 75.0))
    isochrone_5min = min_dist_m <= 400.0
    isochrone_10min = min_dist_m <= 800.0
    
    return {
        "station": best_station,
        "walking_distance_meters": round(min_dist_m, 1),
        "walking_duration_mins": walk_mins,
        "in_5min_isochrone": isochrone_5min,
        "in_10min_isochrone": isochrone_10min,
    }


def calculate_transit_profile(
    property_name: str,
    x: float,
    z: float,
) -> Dict[str, Any]:
    """Generate comprehensive transit connectivity report for a building along SZR."""
    nearest = find_nearest_metro_station(x, z)
    st = nearest["station"]
    walk_mins = nearest["walking_duration_mins"]
    
    # Calculate door-to-door commute times to destinations
    commute_matrix = []
    total_commute_sum = 0
    for hub_key, hub_info in DESTINATION_HUBS.items():
        train_mins = st["commutes"].get(hub_key, 15)
        door_to_door = walk_mins + train_mins + 2  # 2 mins avg wait time for Red Line
        total_commute_sum += door_to_door
        commute_matrix.append({
            "hub_id": hub_key,
            "destination": hub_info["name"],
            "icon": hub_info["icon"],
            "metro_ride_mins": train_mins,
            "door_to_door_mins": door_to_door,
            "summary": f"{door_to_door} mins total ({walk_mins}m walk + {train_mins}m train)"
        })
        
    # Transit Mobility Score (0-100)
    # 400m walk (5m) = high score; penalize long walks
    walk_penalty = max(0, (walk_mins - 5) * 4)
    avg_commute = total_commute_sum / len(DESTINATION_HUBS)
    mobility_score = max(30, min(100, int(105 - (walk_mins * 3.5) - (avg_commute * 0.8))))
    
    tier = "Super-Transit Hub (5★)" if mobility_score >= 85 else ("Transit Accessible (4★)" if mobility_score >= 70 else "Car-Reliant (3★)")

    return {
        "property_name": property_name,
        "coordinates": {"x": x, "z": z},
        "nearest_metro_station": {
            "id": st["id"],
            "name": st["name"],
            "name_ar": st["name_ar"],
            "code": st["code"],
            "line": st["line"],
            "walking_distance_meters": nearest["walking_distance_meters"],
            "walking_duration_mins": walk_mins,
            "within_5min_shed": nearest["in_5min_isochrone"],
            "within_10min_shed": nearest["in_10min_isochrone"],
        },
        "transit_mobility_score": mobility_score,
        "transit_tier": tier,
        "commute_destinations": commute_matrix,
        "all_stations": METRO_STATIONS,
    }
