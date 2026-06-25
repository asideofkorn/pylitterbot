"""Pet tools for MCP server."""

from __future__ import annotations

from typing import Any

from pylitterbot.mcp.helpers import format_pet_summary, resolve_robot
from pylitterbot.mcp.server import get_account, mcp
from pylitterbot.pet import Pet
from pylitterbot.robot.litterrobot5 import LitterRobot5


def _resolve_pet_id(pets: list[Pet], identifier: str) -> str:
    """Find a pet by name (case-insensitive) or ID and return its ID."""
    normalized = identifier.casefold()
    for pet in pets:
        name = pet.name or ""
        if name.casefold() == normalized or str(pet.id) == identifier:
            return pet.id
    available = ", ".join(p.name for p in pets)
    raise ValueError(f"No pet found matching '{identifier}'. Available: {available}")


@mcp.tool()
async def get_pets() -> list[dict[str, Any]]:
    """List all pets linked to the account.

    Returns a list of pet summaries including name, type, gender, weight,
    and breeds.
    """
    account = await get_account()
    await account.load_pets()
    return [format_pet_summary(pet) for pet in account.pets]


@mcp.tool()
async def reassign_pet_visit(
    robot: str, event_id: str, *, from_pet: str | None = None, to_pet: str | None = None
) -> str:
    """Reassign or unassign a pet visit (Litter-Robot 5 only).

    Args:
        robot: Robot name (case-insensitive) or ID.
        event_id: The event ID of the activity to reassign.
        from_pet: Name or ID of the pet currently assigned to the visit.
            Omit or pass empty string if the visit is unattributed.
        to_pet: Name or ID of the pet to reassign the visit to.
            Omit to unassign the visit.

    Note:
        At least one of from_pet or to_pet must be provided (and non-empty).
        If from_pet is empty/omitted and the visit has no attribution, the
        underlying API will assign it directly to to_pet without a "from" check.

    """
    event_id = event_id.strip()
    if not event_id:
        raise ValueError("event_id must be a non-empty string.")

    # Normalize empty strings to None
    if from_pet is not None and not from_pet.strip():
        from_pet = None
    if to_pet is not None and not to_pet.strip():
        to_pet = None

    if not from_pet and not to_pet:
        raise ValueError("At least one of from_pet or to_pet must be provided.")

    resolved = await resolve_robot(robot)
    if not isinstance(resolved, LitterRobot5):
        raise ValueError(
            f"Pet visit reassignment is only supported on Litter-Robot 5, "
            f"but '{resolved.name}' is a {resolved.model}."
        )
    account = await get_account()
    from_pet_id = _resolve_pet_id(account.pets, from_pet) if from_pet else None
    to_pet_id = _resolve_pet_id(account.pets, to_pet) if to_pet else None
    await resolved.reassign_pet_visit(
        event_id, from_pet_id=from_pet_id, to_pet_id=to_pet_id
    )

    if to_pet:
        from_label = f"from '{from_pet}' " if from_pet else ""
        return (
            f"Reassigned visit '{event_id}' on '{resolved.name}' "
            f"{from_label}to '{to_pet}'."
        )
    else:
        from_label = f"from '{from_pet}'" if from_pet else ""
        return (
            f"Unassigned visit '{event_id}' on '{resolved.name}' "
            f"{from_label}."
        )
