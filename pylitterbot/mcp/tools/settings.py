"""Settings tools for MCP server."""

from __future__ import annotations

from datetime import datetime

from pylitterbot.enums import BrightnessLevel, NightLightMode
from pylitterbot.mcp.helpers import (
    resolve_feeder_robot,
    resolve_litter_robot,
    resolve_robot,
)
from pylitterbot.mcp.server import mcp
from pylitterbot.robot.litterrobot3 import LitterRobot3
from pylitterbot.robot.litterrobot4 import LitterRobot4
from pylitterbot.robot.litterrobot5 import LitterRobot5


@mcp.tool()
async def set_name(robot: str, name: str) -> str:
    """Rename a robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        name: The new name for the robot.

    """
    name = name.strip()
    if not name:
        raise ValueError("name must be a non-empty string.")
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot rename.")
    ok = await resolved.set_name(name)
    if not ok:
        raise RuntimeError(f"Failed to rename '{resolved.name}'.")
    return f"Renamed robot to '{name}'."


@mcp.tool()
async def set_night_light(robot: str, enabled: bool) -> str:
    """Enable or disable the night light on a robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to enable, False to disable.

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set night light.")
    ok = await resolved.set_night_light(enabled)
    if not ok:
        raise RuntimeError(f"Failed to set night light on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Night light {state} on '{resolved.name}'."


@mcp.tool()
async def set_night_light_brightness(robot: str, brightness: int) -> str:
    """Set the night light brightness on a Litter-Robot 4 or 5.

    Args:
        robot: Robot name (case-insensitive) or ID.
        brightness: Brightness level. LR4: 25 (low), 50 (medium), 100 (high). LR5: 0-100.

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(
            f"'{resolved.name}' is offline; cannot set night light brightness."
        )
    if not isinstance(resolved, (LitterRobot4, LitterRobot5)):
        raise ValueError(
            f"Night light brightness is only supported on Litter-Robot 4 and 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if isinstance(resolved, LitterRobot5):
        if not 0 <= brightness <= 100:
            raise ValueError(
                f"Invalid brightness {brightness}. Must be between 0 and 100."
            )
    else:
        valid_brightness = {25, 50, 100}
        if brightness not in valid_brightness:
            raise ValueError(
                f"Invalid brightness {brightness}. Must be one of: {sorted(valid_brightness)}"
            )
    ok = await resolved.set_night_light_brightness(brightness)
    if not ok:
        raise RuntimeError(
            f"Failed to set night light brightness on '{resolved.name}'."
        )
    return f"Night light brightness set to {brightness} on '{resolved.name}'."


@mcp.tool()
async def set_night_light_mode(robot: str, mode: str) -> str:
    """Set the night light mode on a Litter-Robot 4 or 5.

    Args:
        robot: Robot name (case-insensitive) or ID.
        mode: Night light mode - "off", "on", or "auto" (case-insensitive).

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set night light mode.")
    if not isinstance(resolved, (LitterRobot4, LitterRobot5)):
        raise ValueError(
            f"Night light mode is only supported on Litter-Robot 4 and 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    try:
        night_light_mode = NightLightMode(mode.upper())
    except ValueError:
        valid = ", ".join(m.value.lower() for m in NightLightMode)
        raise ValueError(
            f"Invalid night light mode '{mode}'. Valid modes: {valid}"
        ) from None
    ok = await resolved.set_night_light_mode(night_light_mode)
    if not ok:
        raise RuntimeError(f"Failed to set night light mode on '{resolved.name}'.")
    return f"Night light mode set to '{mode.lower()}' on '{resolved.name}'."


@mcp.tool()
async def set_panel_lockout(robot: str, enabled: bool) -> str:
    """Enable or disable the button lock on a robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to lock buttons, False to unlock.

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set panel lockout.")
    ok = await resolved.set_panel_lockout(enabled)
    if not ok:
        raise RuntimeError(f"Failed to set panel lockout on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Panel lockout {state} on '{resolved.name}'."


@mcp.tool()
async def set_wait_time(robot: str, minutes: int) -> str:
    """Set the clean cycle delay on a Litter-Robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        minutes: Wait time in minutes. LR3: 3, 7, 15. LR4/LR5: 3, 7, 15, 25, 30.

    """
    resolved = await resolve_litter_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set wait time.")
    valid_wait_times = set(resolved.VALID_WAIT_TIMES)
    if minutes not in valid_wait_times:
        raise ValueError(
            f"Invalid wait time {minutes} for {resolved.model}. "
            f"Must be one of: {sorted(valid_wait_times)}"
        )
    ok = await resolved.set_wait_time(minutes)
    if not ok:
        raise RuntimeError(f"Failed to set wait time on '{resolved.name}'.")
    return f"Wait time set to {minutes} minutes on '{resolved.name}'."


@mcp.tool()
async def set_sleep_mode(
    robot: str, enabled: bool, start_time: str | None = None
) -> str:
    """Configure sleep mode on a Litter-Robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to enable sleep mode, False to disable.
        start_time: Sleep start time in HH:MM format (24-hour). Required when enabling.

    """
    resolved = await resolve_litter_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set sleep mode.")
    if not isinstance(resolved, (LitterRobot3, LitterRobot5)):
        raise ValueError(
            f"Sleep mode cannot be set via the API on "
            f"'{resolved.name}' ({resolved.model}). "
            f"Supported models: Litter-Robot 3, Litter-Robot 5."
        )
    sleep_time = None
    if enabled:
        if not start_time:
            raise ValueError("start_time is required when enabling sleep mode.")
        try:
            sleep_time = datetime.strptime(start_time, "%H:%M").time()
        except ValueError as exc:
            raise ValueError(
                f"Invalid start_time '{start_time}'. Expected HH:MM (24-hour), e.g. '22:30'."
            ) from exc
    ok = await resolved.set_sleep_mode(enabled, sleep_time)
    if not ok:
        raise RuntimeError(f"Failed to set sleep mode on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Sleep mode {state} on '{resolved.name}'."


@mcp.tool()
async def set_panel_brightness(robot: str, brightness: int) -> str:
    """Set the panel display brightness on a Litter-Robot 4 or 5.

    Args:
        robot: Robot name (case-insensitive) or ID.
        brightness: Brightness level (25=low, 50=medium, 100=high).

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set panel brightness.")
    if not isinstance(resolved, (LitterRobot4, LitterRobot5)):
        raise ValueError(
            f"Panel brightness is only supported on Litter-Robot 4 and 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    try:
        level = BrightnessLevel(brightness)
    except ValueError:
        valid = ", ".join(str(b.value) for b in BrightnessLevel)
        raise ValueError(
            f"Invalid brightness {brightness}. Must be one of: {valid}"
        ) from None
    ok = await resolved.set_panel_brightness(level)
    if not ok:
        raise RuntimeError(f"Failed to set panel brightness on '{resolved.name}'.")
    return f"Panel brightness set to {brightness} on '{resolved.name}'."


@mcp.tool()
async def set_volume(robot: str, volume: int) -> str:
    """Set the sound volume on a Litter-Robot 5.

    Args:
        robot: Robot name (case-insensitive) or ID.
        volume: Volume level (0-100).

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set volume.")
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Volume is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not 0 <= volume <= 100:
        raise ValueError(f"Invalid volume {volume}. Must be between 0 and 100.")
    ok = await resolved.set_volume(volume)
    if not ok:
        raise RuntimeError(f"Failed to set volume on '{resolved.name}'.")
    return f"Volume set to {volume} on '{resolved.name}'."


@mcp.tool()
async def set_privacy_mode(robot: str, enabled: bool) -> str:
    """Enable or disable privacy mode on a Litter-Robot 5.

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to enable privacy mode, False to disable.

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set privacy mode.")
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Privacy mode is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    ok = await resolved.set_privacy_mode(enabled)
    if not ok:
        raise RuntimeError(f"Failed to set privacy mode on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Privacy mode {state} on '{resolved.name}'."


@mcp.tool()
async def set_camera_audio(robot: str, enabled: bool) -> str:
    """Enable or disable camera audio on a Litter-Robot 5 (Pro only).

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to enable camera audio, False to disable.

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set camera audio.")
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera audio is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro:
        raise ValueError(
            f"Camera audio is only available on Litter-Robot 5 Pro devices, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    ok = await resolved.set_camera_audio(enabled)
    if not ok:
        raise RuntimeError(f"Failed to set camera audio on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Camera audio {state} on '{resolved.name}'."


@mcp.tool()
async def get_camera_videos(robot: str, limit: int = 5) -> list[dict]:
    """Fetch recent camera video clips from a Litter-Robot 5 Pro.

    Args:
        robot: Robot name (case-insensitive) or ID.
        limit: Maximum number of clips to return (default 5).

    Returns:
        List of video clips with id, thumbnail_url, event_type, and created_at.

    """
    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera clips are only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro or not resolved.camera_metadata:
        raise ValueError(
            f"'{resolved.name}' does not have a camera or is not a Pro model."
        )
    clips = await resolved.get_camera_videos(limit=limit)
    return [
        {
            "id": clip.id,
            "thumbnail_url": clip.thumbnail_url,
            "event_type": clip.event_type,
            "created_at": clip.created_at.isoformat(),
        }
        for clip in clips
    ]


@mcp.tool()
async def get_camera_video_settings(robot: str) -> dict:
    """Fetch camera video settings from a Litter-Robot 5 Pro.

    Args:
        robot: Robot name (case-insensitive) or ID.

    Returns:
        Camera configuration including resolution, bitrate, FPS, and sensor info.

    """
    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera settings are only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro or not resolved.camera_metadata:
        raise ValueError(
            f"'{resolved.name}' does not have a camera or is not a Pro model."
        )
    settings = await resolved.get_camera_video_settings()
    if settings is None:
        raise RuntimeError(f"Failed to fetch camera settings from '{resolved.name}'.")
    return settings


@mcp.tool()
async def set_camera_view(robot: str, view: str) -> str:
    """Switch the camera live-view canvas on a Litter-Robot 5 Pro.

    Args:
        robot: Robot name (case-insensitive) or ID.
        view: Camera view - 'front' or 'globe' (case-insensitive).

    """
    resolved = await resolve_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set camera view.")
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera view is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro or not resolved.camera_metadata:
        raise ValueError(
            f"'{resolved.name}' does not have a camera or is not a Pro model."
        )
    view = view.strip().lower()
    if view not in ("front", "globe"):
        raise ValueError(f"Invalid view '{view}'. Must be 'front' or 'globe'.")
    ok = await resolved.set_camera_view(view)
    if not ok:
        raise RuntimeError(f"Failed to set camera view on '{resolved.name}'.")
    return f"Camera view set to '{view}' on '{resolved.name}'."


@mcp.tool()
async def get_camera_audio_status(robot: str) -> bool:
    """Check if camera audio is currently enabled on a Litter-Robot 5 Pro.

    Args:
        robot: Robot name (case-insensitive) or ID.

    Returns:
        True if camera audio is enabled, False otherwise.

    """
    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera audio status is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro or not resolved.camera_metadata:
        raise ValueError(
            f"'{resolved.name}' does not have a camera or is not a Pro model."
        )
    enabled = await resolved.refresh_camera_audio_enabled()
    return enabled is True


@mcp.tool()
async def get_recent_cat_activity(robot: str, clips: int = 5) -> list[dict]:
    """Fetch recent camera clips and matching pet visits for review.

    Returns camera clips with their nearest pet visit by timestamp so you
    can visually verify which cat actually used the litter.

    Args:
        robot: Robot name (case-insensitive) or ID.
        clips: Number of recent clips to return (default 5).

    Returns:
        List of dicts with clip info and the closest matching pet visit.

    """
    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Camera clips are only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    if not resolved.is_pro or not resolved.camera_metadata:
        raise ValueError(
            f"'{resolved.name}' does not have a camera or is not a Pro model."
        )

    from pylitterbot.mcp.server import _account

    account = _account
    if not account:
        raise RuntimeError("Litter-Robot account not connected.")

    # Fetch clips
    video_clips = await resolved.get_camera_videos(limit=clips)

    # Build a mapping of pet visits by timestamp
    pet_visits = []
    for pet in account.pets:
        for entry in pet.weight_history:
            pet_visits.append(
                {
                    "pet_name": pet.name,
                    "pet_id": pet.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "weight": entry.weight,
                }
            )

    # Sort visits by timestamp (most recent first)
    pet_visits.sort(key=lambda x: x["timestamp"], reverse=True)

    # Match each clip to the nearest visit (within 2 minutes)
    results = []
    from datetime import datetime, timedelta

    for clip in video_clips:
        clip_time = clip.created_at
        nearest_visit = None
        min_diff = None

        for visit in pet_visits:
            visit_time = datetime.fromisoformat(visit["timestamp"])
            diff = abs((clip_time - visit_time).total_seconds())

            if diff <= 120:  # Within 2 minutes
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    nearest_visit = visit

        results.append(
            {
                "clip_id": clip.id,
                "thumbnail_url": clip.thumbnail_url,
                "event_type": clip.event_type,
                "clip_time": clip.created_at.isoformat(),
                "nearest_visit": nearest_visit,
                "time_diff_seconds": round(min_diff) if min_diff else None,
            }
        )

    return results


@mcp.tool()
async def reassign_pet_visit(
    robot: str,
    event_id: str,
    *,
    from_pet: str | None = None,
    to_pet: str | None = None,
) -> str:
    """Reassign a pet visit to a different cat on a Litter-Robot 5.

    Use this when the system attributed a visit to the wrong cat.
    You can also unassign a visit by omitting to_pet.

    Args:
        robot: Robot name (case-insensitive) or ID.
        event_id: The event ID of the visit to reassign.
        from_pet: Current pet name the visit is assigned to (case-insensitive).
        to_pet: Pet name to reassign the visit to. Omit to unassign.

    Returns:
        Confirmation message with the reassignment result.

    """
    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Pet visit reassignment is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )

    from pylitterbot.mcp.server import _account

    account = _account
    if not account:
        raise RuntimeError("Litter-Robot account not connected.")

    # Resolve pet IDs from names (case-insensitive)
    def find_pet_by_name(name: str):
        for pet in account.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    from_pet_id = None
    to_pet_id = None

    if from_pet:
        from_pet_obj = find_pet_by_name(from_pet)
        from_pet_id = from_pet_obj.id if from_pet_obj else None
        if not from_pet_obj:
            raise ValueError(
                f"Pet '{from_pet}' not found. Available pets: "
                f"{', '.join(p.name for p in account.pets)}"
            )

    if to_pet:
        to_pet_obj = find_pet_by_name(to_pet)
        to_pet_id = to_pet_obj.id if to_pet_obj else None
        if not to_pet_obj:
            raise ValueError(
                f"Pet '{to_pet}' not found. Available pets: "
                f"{', '.join(p.name for p in account.pets)}"
            )

    if not to_pet and not from_pet:
        raise ValueError("Must specify from_pet and/or to_pet.")

    result = await resolved.reassign_pet_visit(
        event_id=event_id,
        from_pet_id=from_pet_id,
        to_pet_id=to_pet_id,
    )

    if result is None:
        raise RuntimeError(f"Failed to reassign pet visit {event_id}.")

    action = "unassigned" if not to_pet else f"reassigned to '{to_pet}'"
    from_info = f" from '{from_pet}'" if from_pet else ""
    return f"Visit {event_id} {action}{from_info} on '{resolved.name}'."


@mcp.tool()
async def set_gravity_mode(robot: str, enabled: bool) -> str:
    """Enable or disable gravity mode on a Feeder-Robot.

    Args:
        robot: Robot name (case-insensitive) or ID.
        enabled: True to enable gravity mode, False to disable.

    """
    resolved = await resolve_feeder_robot(robot)
    if not resolved.is_online:
        raise ValueError(f"'{resolved.name}' is offline; cannot set gravity mode.")
    ok = await resolved.set_gravity_mode(enabled)
    if not ok:
        raise RuntimeError(f"Failed to set gravity mode on '{resolved.name}'.")
    state = "enabled" if enabled else "disabled"
    return f"Gravity mode {state} on '{resolved.name}'."
