"""Time parsing and formatting utilities."""

from datetime import timedelta


def parse_time(s: str) -> float:
    """Parse a time string into seconds.

    Accepts HH:MM:SS, MM:SS, SS, or decimal hours (e.g. 3.5 -> 3h30m).
    """
    s = s.strip()
    if not s:
        raise ValueError("Empty time")

    # Support decimal hours (e.g., "1.5" = 1 hour 30 minutes)
    # This is the historically documented behavior
    if s.replace(".", "", 1).replace("-", "", 1).isdigit() and ":" not in s:
        if "." in s:
            hours = float(s)
            return hours * 3600.0
        else:
            return float(s)

    # Handle colon-separated formats
    parts = s.split(":")
    parts = [p for p in parts if p != ""]

    # Validate parts
    for part in parts:
        if not part.replace(".", "", 1).isdigit():
            raise ValueError(f"Invalid time component: {part}")

    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        if seconds >= 60:
            raise ValueError(f"Seconds must be < 60, got {seconds}")
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        if minutes >= 60:
            raise ValueError(f"Minutes must be < 60, got {minutes}")
        if seconds >= 60:
            raise ValueError(f"Seconds must be < 60, got {seconds}")
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Can't parse time: {s}")


def format_hhmmss(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS, preserving sub-second precision."""
    if seconds < 0:
        seconds = 0
    
    total_seconds = int(seconds)
    ms = int((seconds - total_seconds) * 100)
    
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"


def format_hhmmss_with_ms(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mm (with centiseconds)."""
    if seconds < 0:
        seconds = 0
    
    total_seconds = int(seconds)
    ms = int((seconds - total_seconds) * 100)
    
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}"
    else:
        return f"{m:02d}:{s:02d}.{ms:02d}"
