"""Shared modifier-group catalog (milk/size/strength/serve).

Single source of truth for both pricing (server, trusted) and display (client, via
GET /api/modifier-groups/) — the frontend never hardcodes prices or labels.
"""

from decimal import Decimal
from typing import TypedDict


class ModifierOption(TypedDict):
    label: str
    price: str


class ModifierGroup(TypedDict):
    label: str
    default: str
    options: dict[str, ModifierOption]


MODIFIER_GROUPS: dict[str, ModifierGroup] = {
    "milk": {
        "label": "Milk",
        "default": "full",
        "options": {
            "full": {"label": "Full cream", "price": "0.00"},
            "skim": {"label": "Skim", "price": "0.00"},
            "oat": {"label": "Oat", "price": "0.70"},
            "almond": {"label": "Almond", "price": "0.70"},
        },
    },
    "size": {
        "label": "Size",
        "default": "reg",
        "options": {
            "reg": {"label": "Regular", "price": "0.00"},
            "lg": {"label": "Large", "price": "0.80"},
        },
    },
    "shot": {
        "label": "Strength",
        "default": "std",
        "options": {
            "std": {"label": "Standard", "price": "0.00"},
            "extra": {"label": "Extra shot", "price": "0.60"},
            "decaf": {"label": "Decaf", "price": "0.00"},
        },
    },
    "heat": {
        "label": "Serve",
        "default": "warm",
        "options": {
            "warm": {"label": "Heated", "price": "0.00"},
            "cold": {"label": "As is", "price": "0.00"},
        },
    },
}


def resolve_modifiers(
    modifier_groups: list[str],
    selections: dict[str, str],
) -> tuple[Decimal, str]:
    """Validate `selections` against `modifier_groups`; return (extra_price, label)."""
    extra = Decimal("0.00")
    labels = []
    for group_key in modifier_groups:
        group = MODIFIER_GROUPS[group_key]
        chosen = selections.get(group_key, group["default"])
        option = group["options"].get(chosen)
        if option is None:
            msg = f"Invalid option {chosen!r} for modifier group {group_key!r}."
            raise ValueError(msg)
        extra += Decimal(option["price"])
        if chosen != group["default"]:
            labels.append(option["label"])
    return extra, " · ".join(labels)
