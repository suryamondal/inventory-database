import os
import json
from datetime import datetime, timedelta

class InventoryDatabase:
    def __init__(self, database_dir="database"):
        self.database_dir = database_dir
        os.makedirs(self.database_dir, exist_ok=True)

    def get_today_filename(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.database_dir, f"inventory_{today}.json")

    def get_last_available_filename(self):
        filenames = sorted(os.listdir(self.database_dir), reverse=True)
        for filename in filenames:
            if filename.startswith("inventory_"):
                return os.path.join(self.database_dir, filename)

    def load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as file:
                return json.load(file)
        else:
            return []

    def save_data(self, filename, data):
        with open(filename, "w") as file:
            json.dump(data, file, indent=2)

    def assign_item_number(self):
        # Check through all previous files to find a unique item number
        for filename in os.listdir(self.database_dir):
            if filename.endswith(".json"):
                data = self.load_data(os.path.join(self.database_dir, filename))
                item_numbers = set()
                for entry in data:
                    item_numbers.add(entry["item"].get("item_number"))
                if None not in item_numbers:
                    return max(item_numbers) + 1
                else:
                    return 1

    def find_or_assign_item_number(self, name):
        # Search through all previous files to find the item number associated with the given name
        for filename in os.listdir(self.database_dir):
            if filename.endswith(".json"):
                data = self.load_data(os.path.join(self.database_dir, filename))
                for entry in data:
                    item = entry.get("item", {})
                    if item.get("name") == name:
                        return item.get("item_number")

        # If no item_number found, assign a new one
        return self.assign_item_number()

    def add_item(self, name, quantity, price, batch_number=None, item_number=None, expire_date=None, extra_parameters=None):
        if extra_parameters is None:
            extra_parameters = {}

        if item_number is None:
            item_number = self.find_or_assign_item_number(name)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "item": {
                "name": name,
                "quantity": quantity,
                "price": price,
                "batch_number": batch_number,
                "item_number": item_number,
                "expire_date": expire_date,
                "extra_parameters": extra_parameters
            }
        }

        data = self.load_data(self.get_today_filename())
        data.append(entry)
        self.save_data(self.get_today_filename(), data)

    def remove_item(self, name, quantity, price, batch_number=None, item_number=None, expire_date=None, extra_parameters=None):
        # Call add_item with negative quantity to indicate removal
        self.add_item(name, -quantity, price, batch_number, item_number, expire_date, extra_parameters)

    def carry_forward(self):
        today_filename = self.get_today_filename()

        if not os.path.exists(today_filename):
            last_available_filename = self.get_last_available_filename()
            if last_available_filename:
                last_data = self.load_data(last_available_filename)
                today_data = self.load_data(today_filename)

                # Dictionary to keep track of net quantities for each item
                net_quantities = {}

                # Update net quantities based on the last available day
                for entry in last_data:
                    item_name = entry["item"]["name"]
                    quantity = entry["item"]["quantity"]
                    net_quantities[item_name] = net_quantities.get(item_name, 0) + quantity

                # Carry forward items with non-zero net quantities
                for item_name, net_quantity in net_quantities.items():
                    if net_quantity != 0:
                        today_data.append({"timestamp": str(datetime.now()), "item": {
                            "name": item_name,
                            "quantity": net_quantity,
                            "price": 0.0  # Adjust as needed
                        }})

                self.save_data(today_filename, today_data)

    def print_entries(self, name=None, item_number=None):
        data = self.load_data(self.get_today_filename())
        entries_for_item = [entry for entry in data if (name is None or entry["item"]["name"] == name) and (item_number is None or entry["item"].get("item_number") == item_number)]

        if not entries_for_item:
            print("No entries found for the specified item.")
            return

        for entry in entries_for_item:
            item = entry["item"]
            print(f"Timestamp: {entry['timestamp']}")
            print(f"Item Name: {item['name']}")
            print(f"Quantity: {item['quantity']}")
            print(f"Price: {item['price']}")
            print(f"Batch Number: {item.get('batch_number', 'N/A')}")
            print(f"Item Number: {item.get('item_number', 'N/A')}")
            print(f"Expire Date: {item.get('expire_date', 'N/A')}")
            print(f"Extra Parameters: {item.get('extra_parameters', 'N/A')}")
            print("\n" + "-"*30 + "\n")

    def print_summary(self, name=None, item_number=None):
        data = self.load_data(self.get_today_filename())
        entries_for_item = [entry for entry in data if (name is None or entry["item"]["name"] == name) and (item_number is None or entry["item"].get("item_number") == item_number)]

        if not entries_for_item:
            print("No entries found for the specified item.")
            return

        print("\nItem-wise Summary:")
        for current_name in set(entry["item"]["name"] for entry in entries_for_item):
            entries_for_current_item = [entry for entry in entries_for_item if entry["item"]["name"] == current_name]
            net_quantity_sum = sum(entry["item"]["quantity"] for entry in entries_for_current_item)
            average_price = "{:.2f}".format(sum(entry["item"]["price"] for entry in entries_for_current_item) / len(entries_for_current_item)) if entries_for_current_item else "N/A"
            item_number_list = [entry["item"].get("item_number") for entry in entries_for_current_item if entry["item"].get("item_number") is not None]
            item_number_str = ', '.join(map(str, set(item_number_list))) if item_number_list else "N/A"

            print(f"\nItem Name: {current_name}")
            print(f"Item Number(s): {item_number_str}")
            print(f"Net Quantity: {net_quantity_sum}")
            print(f"Average Price: {average_price}")

        if name is None and item_number is None:
            net_quantity_sum = sum(entry["item"]["quantity"] for entry in entries_for_item)
            print("\nSummary:")
            print(f"Net Quantity: {net_quantity_sum}")

    def get_inventory(self):
        return self.load_data(self.get_today_filename())

# Example Usage:
if __name__ == "__main__":
    db = InventoryDatabase()

    # Carry forward items from the last available day (if any)
    db.carry_forward()

    # Add items to inventory
    db.add_item("Product A", quantity=10, price=25.99)
    db.add_item("Product B", quantity=5, price=14.99)
    db.add_item("Product C", quantity=20, price=19.99)

    # Remove an item from inventory
    db.remove_item("Product B", quantity=3, price=14.99)  # Remove 3 items with a specific price

    # Print entries for all items
    db.print_entries()

    # Print entries for a specific item
    db.print_entries(name="Product A")

    # Print summary for all items
    db.print_summary()

    # Print summary for a specific item
    db.print_summary(name="Product C")
