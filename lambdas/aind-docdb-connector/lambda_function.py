import json

from aind_data_access_api.document_db import MetadataDbClient

DOCDB_HOST = "api.allenneuraldynamics.org"
DOCDB_DATABASE = "metadata_index"
DOCDB_COLLECTION = "data_assets"
  

docdb_api_client = MetadataDbClient(DOCDB_HOST, DOCDB_DATABASE, DOCDB_COLLECTION)
# enum of possible actions
class Actions:
    COUNT = "count"
    FILTER = "filter"
    AGGREGATE = "aggregation"

def count_documents(event, context):
    '''Gets count of all documents'''
    count = docdb_api_client._count_records()
    print(f"Found {count} records")
    return count


def filter_documents(event, context):
    '''Gets documents that match filter'''
    # TODO: implement parsing from request
    # filter = event.get("filter")

    # temporary filter/ projections
    filter = {
        "data_description.project_name": "Thalamus in the Middle"
    }
    projection = {
        "_id": 1,
        "name": 1,
        "location": 1,
        "created": 1,
        "last_modified": 1,
        "data_description": 1
    }
    limit = 100
    records = docdb_api_client.retrieve_docdb_records(
        filter_query=filter,
        projection=projection,
        limit=limit
    )
    print(f"Found {len(records)} records from filter")
    return records

def aggregate_documents(event, context):
    '''Gets first page of OPEN PRs'''
    raise NotImplementedError("Aggregation not implemented yet")

def lambda_handler(event, context):
    ''
    print(f"Received lambda event: {event}")
    print(f"Received lambda context: {context}")

    # expect event to have format:
    # {
    #   "action": "count" # type of action to perform
    # }
    action = event.get("action")
    if action == Actions.COUNT:
        response = count_documents(event, context)
    elif action == Actions.FILTER:
        response = filter_documents(event, context)
    elif action == Actions.AGGREGATE:
        response = aggregate_documents(event, context)
    else:
        print(f"Unknown action: {action}")
        return {
            "statusCode": 400,
            "body": json.dumps(f"Unknown action: {action}")
        }
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }


# # # local testing
# if __name__ == "__main__":
#     count_documents(None, None)
#     filter_documents(None, None)
#     aggregate_documents(None, None)