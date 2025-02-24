from aind_data_migration_utils.migrate import Migrator
import pandas as pd


def fix_experimenter_full_name(record):
    if isinstance(record["acquisition"]["experimenter_full_name"], str):
        record["acquisition"]["experimenter_full_name"] = [record["acquisition"]["experimenter_full_name"]]
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--full-run", action=argparse.BooleanOptionalAction, required=False, default=False)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction, required=False, default=False)
    args = parser.parse_args()

    migrator = Migrator(
        query={},
        migration_callback=fix_experimenter_full_name,
        files=["acquisition"],
        path="./fix_experimenter_full_name",
        prod=not args.dev,
    )

    migrator.run(full_run=args.full_run, test_mode=args.test)