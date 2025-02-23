from aind_data_migration_utils.migrate import Migrator
import pandas as pd
import re

def update_channel_name(record: dict) -> dict:
    if record.get('data_description', {}).get('project_name') == "Thalamus in the middle":
        acquisition = record.get('acquisition', {})
        if acquisition:
            for tile in acquisition.get('tiles', []):
                channel = tile.get('channel', {})
                channel_name = channel.get('channel_name')
                if channel_name and re.match(r'^\d+\.\d+$', channel_name):
                    channel['channel_name'] = int(float(channel_name))
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--full-run", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction, required=False, default=False)
    args = parser.parse_args()

    query = {
        "data_description.project_name": "Thalamus in the middle"
    }
    migrator = Migrator(
        query=query,
        migration_callback=update_channel_name,
        files=["acquisition"],
        path="./update_channel_name",
        prod=not args.dev,
    )

    # Run the dry run
    migrator.run(full_run=False, test_mode=args.test)

    # If requested, run the full run
    if args.full_run:
        migrator.run(full_run=True, test_mode=args.test)