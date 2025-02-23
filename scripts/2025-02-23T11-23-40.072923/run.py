from aind_data_migration_utils.migrate import Migrator
from aind_data_migration_utils.models import Modality
import pandas as pd

def migration_callback(record: dict) -> dict:
    # Convert modality string to a list
    modality_str = record["metadata"]["modality"]
    modality_list = [modality_str]
    
    # Convert modality list to Modality models
    modality_models = [Modality[modality] for modality in modality_list]
    
    # Update the record with the new modality list
    record["metadata"]["modality"] = modality_models
    
    return record

if __name__ == "__main__":
    # Read the list of affected record IDs from a CSV file
    affected_records = pd.read_csv("affected_record_ids.csv")
    
    query = {
        "_id": {"$in": affected_records["record_id"].tolist()}
    }
    
    migrator = Migrator(
        query=query,
        migration_callback=migration_callback,
        files=["modality"],
        path="./fix_modality_type",
        prod=True,
    )
    
    # Run the dry run
    migrator.run(full_run=False, test_mode=False)
    
    # Run the full migration
    migrator.run(full_run=True, test_mode=False)