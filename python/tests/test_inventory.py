"""Unit tests for the first item-stack inventory implementation."""
import unittest

from mcpepy.inventory import Inventory, ItemStack


class InventoryTests(unittest.TestCase):
    def test_add_merges_then_uses_empty_slots(self):
        inventory = Inventory()
        self.assertEqual(inventory.add(2, 60), 0)
        self.assertEqual(inventory.add(2, 10), 0)
        self.assertEqual(inventory.slots[0].count, 64)
        self.assertEqual(inventory.slots[1].count, 6)

    def test_add_reports_overflow_when_inventory_full(self):
        inventory = Inventory()
        for slot in range(len(inventory.slots)):
            inventory.slots[slot] = ItemStack(1, 64)
        self.assertEqual(inventory.add(2, 5), 5)

    def test_selected_stack_consumption_clears_empty_slot(self):
        inventory = Inventory()
        inventory.add(3, 2)
        self.assertTrue(inventory.consume_selected())
        self.assertEqual(inventory.selected.count, 1)
        self.assertTrue(inventory.consume_selected())
        self.assertIsNone(inventory.selected)
        self.assertFalse(inventory.consume_selected())

    def test_hotbar_selection_is_bounded(self):
        inventory = Inventory()
        inventory.select_hotbar(8)
        self.assertEqual(inventory.selected_hotbar, 8)
        with self.assertRaises(IndexError):
            inventory.select_hotbar(9)

    def test_serialization_round_trip(self):
        inventory = Inventory()
        inventory.add(4, 12)
        inventory.select_hotbar(4)
        restored = Inventory.from_dict(inventory.to_dict())
        self.assertEqual(restored.selected_hotbar, 4)
        self.assertEqual(restored.slots[0].item_id, 4)
        self.assertEqual(restored.slots[0].count, 12)


if __name__ == "__main__":
    unittest.main()
