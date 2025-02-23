from aind_data_migration_utils.migrate import Migrator
import pandas as pd
import re
import argparse
import logging

mangled_data = pd.read_csv('results_mangled.csv')

def fix_channel_names(record: dict) -> dict:
    if record.get("data_description", {}).get("project_name") == "Thalamus in the middle":
        for tile in record.get("acquisition", {}).get("tiles", []):
            channel = tile.get("channel", {})
            channel_name = channel.get("channel_name")
            if channel_name:
                try:
                    wavelength = int(float(channel_name))
                    channel["channel_name"] = str(wavelength)
                except ValueError:
                    pass
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--full-run", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction, required=False, default=False)
    args = parser.parse_args()

    # Split into batches of 100 mangled records
    for i in range(0, len(mangled_data), 150):
        mangled_data_batch = mangled_data[i:i + 150]
        query = {
            "_id": {"$in": mangled_data_batch['record_id'].tolist()}
        }
        migrator = Migrator(
            query=query,
            migration_callback=fix_channel_names,
            files=["acquisition", "data_description"],
            path=f"./{i}_fix_channel_names",
            prod=not args.dev,
        )

        # Run the dry run
        migrator.run(full_run=False, test_mode=args.test)

        # If requested, run the full run
        if args.full_run:
            migrator.run(full_run=True, test_mode=args.test)