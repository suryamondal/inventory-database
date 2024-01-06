#!/usr/bin/env python3

import os
import json
from datetime import datetime

class InventoryDatabase:
    def __init__(self, database_directory="database"):
        self.database_directory = database_directory
        os.makedirs(self.database_directory, exist_ok=True)

        # Create file for today if not available
        self.create_file_for_today()

    def get_todays_filename(self):
        return f"database_{datetime.now().strftime('%Y-%m-%d')}.json"

    def create_file_for_today(self):
        today_filename = self.get_todays_filename()
        file_path = os.path.join(self.database_directory, today_filename)

        # Check if the file already exists
        if not os.path.isfile(file_path):
            with open(file_path, "w") as new_file:
                json.dump({}, new_file, indent=2)
                print(f"File created: {file_path}")

    def list_all_filenames_except_today(self):
        today_filename = self.get_todays_filename()
        all_filenames = os.listdir(self.database_directory)

        # Exclude today's filename from the list
        valid_filenames_except_today = [filename for filename in all_filenames
                                         if "database_" in filename and "~" not in filename and filename != today_filename]

        # Check if the files are actually JSON files
        json_filenames_except_today = [filename for filename in valid_filenames_except_today
                                        if filename.endswith(".json")]

        return json_filenames_except_today

    def save_inventory_data(self, inventory_data):
        filename = self.get_todays_filename()
        file_path = os.path.join(self.database_directory, filename)

        # Load existing data from the file
        with open(file_path, "r") as json_file:
            existing_data = json.load(json_file)

        # Update the existing data with the new inventory_data
        existing_data.update(inventory_data)

        # Save the updated data back to the file
        with open(file_path, "w") as json_file:
            json.dump(existing_data, json_file, indent=2)

        print(f"Data saved to {file_path}")

    def carry_forward(self):
        today_date = datetime.now().strftime('%Y-%m-%d')
        filenames_except_today = self.list_all_filenames_except_today()

        non_zero_sum_entries = []
        id_sums = {}

        for filename in filenames_except_today:
            file_path = os.path.join(self.database_directory, filename)

            with open(file_path, "r") as json_file:
                data = json.load(json_file)

            # Sum quantities for each id
            for entry in data:
                item_id = entry["item"]["id"]
                quantity = entry["item"]["quantity"]
                id_sums[item_id] = id_sums.get(item_id, 0) + quantity

            # Check if there are non-zero sum entries
            if any(sum != 0 for sum in id_sums.values()):
                non_zero_sum_entries.extend([entry for entry in data if id_sums[entry["item"]["id"]] != 0])
                print(f"Non-zero sum entries found in {filename}")
            else:
                print(f"No non-zero sum entries found in {filename}")

        print(id_sums)

        # Remove leftover items with zero sum from non_zero_sum_entries using id_sums
        non_zero_sum_entries = [entry for entry in non_zero_sum_entries if id_sums[entry["item"]["id"]] != 0]

        # Create a new file for non-zero sum entries
        if non_zero_sum_entries:
            new_filename = f"carry_forward_{today_date}.json"
            new_file_path = os.path.join(self.database_directory, new_filename)

            with open(new_file_path, "w") as new_json_file:
                json.dump(non_zero_sum_entries, new_json_file, indent=2)

            print(f"Carry-forward data saved to {new_file_path}")
        else:
            print("No non-zero sum entries found in any file")


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

# Example usage
if __name__ == "__main__":
    # Create an instance of InventoryDatabase
    inventory_db = InventoryDatabase()

    # Example data
    inventory_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "item": {
            # ... your item data here ...
        }
    }

    # Save inventory data using the class method with today's filename
    inventory_db.save_inventory_data(inventory_data)

    # List all filenames except today's
    filenames_except_today = inventory_db.list_all_filenames_except_today()
    print("All filenames except today's:")
    for filename in filenames_except_today:
        print(filename)

    # Carry forward non-zero sum entries to a new file for each day
    inventory_db.carry_forward()
