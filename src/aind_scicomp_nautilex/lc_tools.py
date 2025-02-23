from langchain_core.tools import tool
from aind_data_access_api.document_db import MetadataDbClient
from typing import List
import os

API_GATEWAY_HOST = os.getenv("API_GATEWAY_HOST", "api.allenneuraldynamics.org")
DATABASE = os.getenv("DATABASE", "metadata_index")
COLLECTION = os.getenv("COLLECTION", "data_assets")

client = MetadataDbClient(
    host=API_GATEWAY_HOST,
    database=DATABASE,
    collection=COLLECTION,
)

@tool
def query_docdb(query: dict) -> List[dict]:
    """Query the MongoDB document database and retrieve a set of matching records

    Parameters
    ----------
    query : dict
        MongoDB query

    Returns
    -------
    List[dict]
        List of records that match the query
    """
    return client.retrieve_docdb_records(
        filter_query=query
    )