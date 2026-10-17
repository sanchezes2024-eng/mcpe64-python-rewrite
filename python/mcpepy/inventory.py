"""Small item-stack and hotbar model for the Python MCPE port.

This is a deliberately narrow first porting step. It provides real inventory
state and stack operations; it does not claim to reproduce the native save format.
"""
from __future__ import annotations

from dataclasses import dataclass


MAX_STACK_SIZE = 64
HOTBAR_SIZE = 9
INVENTORY_SIZE = 27


@dataclass
class ItemStack:
    item_id: int
    count: int = 1
    max_stack: int = MAX_STACK_SIZE

    def __post_init__(self):
        self.item_id = int(self.item_id)
        self.count = int(self.count)
        self.max_stack = int(self.max_stack)
        if self.item_id <= 0:
            raise ValueError("item_id must be positive")
        if self.max_stack < 1 or self.count < 1 or self.count > self.max_stack:
            raise ValueError("stack count must be between 1 and max_stack")

    def copy(self) -> "ItemStack":
        return ItemStack(self.item_id, self.count, self.max_stack)


class Inventory:
    """Nine hotbar slots plus 27 main slots, with deterministic stack merging."""

    def __init__(self):
        self.slots: list[ItemStack | None] = [None] * (HOTBAR_SIZE + INVENTORY_SIZE)
        self.selected_hotbar = 0

    @property
    def selected(self) -> ItemStack | None:
        return self.slots[self.selected_hotbar]

    def select_hotbar(self, index: int) -> None:
        index = int(index)
        if not 0 <= index < HOTBAR_SIZE:
            raise IndexError("hotbar index must be 0..8")
        self.selected_hotbar = index

    def add(self, item_id: int, count: int = 1, max_stack: int = MAX_STACK_SIZE) -> int:
        """Add items and return the amount that did not fit."""
        item_id, count, max_stack = int(item_id), int(count), int(max_stack)
        if item_id <= 0 or count < 0 or max_stack < 1:
            raise ValueError("invalid item or stack amount")
        remaining = count
        for stack in self.slots:
            if stack is not None and stack.item_id == item_id and stack.count < stack.max_stack:
                moved = min(remaining, stack.max_stack - stack.count)
                stack.count += moved
                remaining -= moved
                if remaining == 0:
                    return 0
        for index, stack in enumerate(self.slots):
            if stack is None:
                moved = min(remaining, max_stack)
                self.slots[index] = ItemStack(item_id, moved, max_stack)
                remaining -= moved
                if remaining == 0:
                    return 0
        return remaining

    def consume_selected(self, amount: int = 1) -> bool:
        amount = int(amount)
        if amount < 1:
            raise ValueError("amount must be positive")
        stack = self.selected
        if stack is None or stack.count < amount:
            return False
        stack.count -= amount
        if stack.count == 0:
            self.slots[self.selected_hotbar] = None
        return True

    def to_dict(self) -> dict:
        return {
            "selected_hotbar": self.selected_hotbar,
            "slots": [
                None if stack is None else {
                    "item_id": stack.item_id,
                    "count": stack.count,
                    "max_stack": stack.max_stack,
                }
                for stack in self.slots
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        inventory = cls()
        slots = data.get("slots", [])
        for index, entry in enumerate(slots[:len(inventory.slots)]):
            if entry is not None:
                inventory.slots[index] = ItemStack(
                    entry["item_id"], entry["count"], entry.get("max_stack", MAX_STACK_SIZE)
                )
        inventory.select_hotbar(max(0, min(HOTBAR_SIZE - 1, data.get("selected_hotbar", 0))))
        return inventory
