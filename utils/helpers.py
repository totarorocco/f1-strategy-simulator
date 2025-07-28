import time
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import re

def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    
    if seconds < 0:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds:.3f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:06.3f}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}:{minutes:02d}:{remaining_seconds:06.3f}"

def calculate_gap(current_time: float, reference_time: float) -> str:
    """
    Calculate gap between two times and format as string.
    
    Args:
        current_time: Current driver's time
        reference_time: Reference time (usually leader)
        
    Returns:
        Formatted gap string
    """
    
    if current_time <= 0 or reference_time <= 0:
        return "N/A"
    
    gap = current_time - reference_time
    
    if abs(gap) < 0.001:
        return "0.000s"
    elif gap > 0:
        return f"+{format_time(gap)}"
    else:
        return f"-{format_time(abs(gap))}"

def format_api_response(response_data: Any) -> Dict[str, Any]:
    """
    Format and validate API response data.
    
    Args:
        response_data: Raw API response
        
    Returns:
        Formatted and validated response
    """
    
    if not response_data:
        return {"status": "error", "data": None, "message": "No data received"}
    
    try:
        if isinstance(response_data, str):
            data = json.loads(response_data)
        elif isinstance(response_data, dict):
            data = response_data
        elif isinstance(response_data, list):
            data = {"items": response_data, "count": len(response_data)}
        else:
            data = {"raw_data": str(response_data)}
        
        return {
            "status": "success",
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": "Data processed successfully"
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "data": None,
            "message": f"JSON decode error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Processing error: {str(e)}"
        }

def cache_data(cache_duration: int = 30):
    """
    Decorator for caching function results.
    
    Args:
        cache_duration: Cache duration in seconds
        
    Returns:
        Decorator function
    """
    
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < cache_duration:
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            # Clean old cache entries
            keys_to_remove = []
            for key, (_, timestamp) in cache.items():
                if current_time - timestamp >= cache_duration * 2:  # Double the cache duration for cleanup
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del cache[key]
            
            return result
        
        return wrapper
    return decorator

def validate_driver_number(driver_number: Any) -> Optional[int]:
    """
    Validate and convert driver number to integer.
    
    Args:
        driver_number: Driver number to validate
        
    Returns:
        Valid driver number or None
    """
    
    try:
        num = int(driver_number)
        if 1 <= num <= 99:  # Valid F1 driver numbers
            return num
    except (ValueError, TypeError):
        pass
    
    return None

def validate_lap_number(lap: Any, total_laps: int = 100) -> Optional[int]:
    """
    Validate lap number.
    
    Args:
        lap: Lap number to validate
        total_laps: Maximum number of laps
        
    Returns:
        Valid lap number or None
    """
    
    try:
        lap_num = int(lap)
        if 1 <= lap_num <= total_laps:
            return lap_num
    except (ValueError, TypeError):
        pass
    
    return None

def calculate_race_progress(current_lap: int, total_laps: int) -> float:
    """
    Calculate race progress as percentage.
    
    Args:
        current_lap: Current lap number
        total_laps: Total laps in race
        
    Returns:
        Progress as float between 0.0 and 1.0
    """
    
    if total_laps <= 0:
        return 0.0
    
    return min(1.0, max(0.0, current_lap / total_laps))

def estimate_remaining_time(current_lap: int, total_laps: int, avg_lap_time: float) -> str:
    """
    Estimate remaining race time.
    
    Args:
        current_lap: Current lap number
        total_laps: Total laps in race
        avg_lap_time: Average lap time in seconds
        
    Returns:
        Formatted remaining time string
    """
    
    remaining_laps = max(0, total_laps - current_lap)
    remaining_seconds = remaining_laps * avg_lap_time
    
    return format_time(remaining_seconds)

def parse_gap_string(gap_str: str) -> float:
    """
    Parse gap string to numeric value.
    
    Args:
        gap_str: Gap string (e.g., "+1.234s", "Leader")
        
    Returns:
        Gap in seconds (0.0 for leader)
    """
    
    if not gap_str or gap_str.lower() in ['leader', 'l', '0']:
        return 0.0
    
    # Remove common characters and extract numeric part
    cleaned = re.sub(r'[+\-s]', '', gap_str.lower())
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def generate_strategy_id(num_stops: int, tire_sequence: List[str], stop_laps: List[int]) -> str:
    """
    Generate unique strategy identifier.
    
    Args:
        num_stops: Number of pit stops
        tire_sequence: List of tire compounds
        stop_laps: List of stop lap numbers
        
    Returns:
        Unique strategy ID string
    """
    
    tire_str = "_".join([t[:1].upper() for t in tire_sequence])  # First letter of each tire
    stops_str = "_".join(map(str, stop_laps)) if stop_laps else "NOSTOP"
    
    strategy_string = f"{num_stops}STOP_{tire_str}_{stops_str}"
    
    # Create short hash for uniqueness
    hash_obj = hashlib.md5(strategy_string.encode())
    short_hash = hash_obj.hexdigest()[:6]
    
    return f"STRAT_{strategy_string}_{short_hash}"

def convert_compound_to_code(compound: str) -> str:
    """
    Convert tire compound name to single-letter code.
    
    Args:
        compound: Full compound name
        
    Returns:
        Single letter code
    """
    
    compound_codes = {
        'soft': 'S',
        'medium': 'M',
        'hard': 'H',
        'intermediate': 'I',
        'wet': 'W'
    }
    
    return compound_codes.get(compound.lower(), 'U')  # U for Unknown

def is_valid_tire_sequence(tire_sequence: List[str]) -> bool:
    """
    Validate tire sequence for F1 regulations.
    
    Args:
        tire_sequence: List of tire compound names
        
    Returns:
        True if sequence is valid
    """
    
    if not tire_sequence:
        return False
    
    valid_compounds = {'soft', 'medium', 'hard', 'intermediate', 'wet'}
    
    # Check all compounds are valid
    for compound in tire_sequence:
        if compound.lower() not in valid_compounds:
            return False
    
    # F1 regulation: Must use at least 2 different dry compounds during race
    dry_compounds = [c for c in tire_sequence if c.lower() in {'soft', 'medium', 'hard'}]
    unique_dry_compounds = set(c.lower() for c in dry_compounds)
    
    if len(dry_compounds) > 0 and len(unique_dry_compounds) < 2:
        return False  # Need at least 2 different dry compounds
    
    return True

def calculate_overtaking_difficulty(track_name: str, position: int) -> float:
    """
    Calculate difficulty multiplier for overtaking.
    
    Args:
        track_name: Name of the track
        position: Current track position
        
    Returns:
        Difficulty multiplier (1.0 = normal, >1.0 = harder)
    """
    
    # Base difficulty by track characteristics
    track_difficulties = {
        'monaco': 3.0,
        'hungary': 2.5,
        'singapore': 2.2,
        'zandvoort': 2.0,
        'spain': 1.8,
        'monza': 0.8,
        'spa': 0.9,
        'silverstone': 1.2,
        'austin': 1.3
    }
    
    base_difficulty = track_difficulties.get(track_name.lower(), 1.5)
    
    # Position-based difficulty (harder to overtake at front)
    if position <= 5:
        position_multiplier = 1.3
    elif position <= 10:
        position_multiplier = 1.1
    else:
        position_multiplier = 1.0
    
    return base_difficulty * position_multiplier

def estimate_pit_stop_loss(track_name: str, traffic_density: float = 1.0) -> float:
    """
    Estimate time loss from pit stop including track-specific factors.
    
    Args:
        track_name: Name of the track
        traffic_density: Traffic factor (1.0 = normal)
        
    Returns:
        Estimated time loss in seconds
    """
    
    # Base pit stop times by track
    base_times = {
        'monaco': 28.0,  # Longer due to narrow pit lane
        'singapore': 26.0,
        'silverstone': 23.0,
        'monza': 22.0,
        'spa': 24.0,
        'default': 25.0
    }
    
    base_time = base_times.get(track_name.lower(), base_times['default'])
    
    # Traffic adjustment
    traffic_penalty = (traffic_density - 1.0) * 3.0  # Up to 3 seconds penalty
    
    return base_time + traffic_penalty

def format_position(position: int) -> str:
    """
    Format position with ordinal suffix.
    
    Args:
        position: Position number
        
    Returns:
        Formatted position string (e.g., "1st", "2nd", "3rd")
    """
    
    if 10 <= position % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(position % 10, 'th')
    
    return f"{position}{suffix}"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or "unnamed_file"

def merge_race_data(*data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple race data sources with conflict resolution.
    
    Args:
        *data_sources: Variable number of data dictionaries
        
    Returns:
        Merged data dictionary
    """
    
    merged = {}
    
    for source in data_sources:
        if not isinstance(source, dict):
            continue
            
        for key, value in source.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Recursively merge dictionaries
                merged[key] = merge_race_data(merged[key], value)
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Combine lists, removing duplicates if they're dictionaries with IDs
                combined = merged[key] + value
                if combined and isinstance(combined[0], dict) and 'id' in combined[0]:
                    # Remove duplicates based on ID
                    seen_ids = set()
                    unique_items = []
                    for item in combined:
                        item_id = item.get('id')
                        if item_id not in seen_ids:
                            seen_ids.add(item_id)
                            unique_items.append(item)
                    merged[key] = unique_items
                else:
                    merged[key] = combined
            else:
                # For non-dict/list values, prefer the latest (last) source
                merged[key] = value
    
    return merged

def create_backup_data(data: Dict[str, Any], backup_dir: str = "data/backups") -> str:
    """
    Create backup of race data with timestamp.
    
    Args:
        data: Data to backup
        backup_dir: Directory for backups
        
    Returns:
        Path to backup file
    """
    
    import os
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"race_data_backup_{timestamp}.json"
    filepath = os.path.join(backup_dir, filename)
    
    # Save data
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return filepath
    except Exception as e:
        print(f"Error creating backup: {e}")
        return ""

def load_backup_data(backup_path: str) -> Optional[Dict[str, Any]]:
    """
    Load data from backup file.
    
    Args:
        backup_path: Path to backup file
        
    Returns:
        Loaded data or None if error
    """
    
    try:
        with open(backup_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading backup: {e}")
        return None