import os
import requests
import json
from typing import List, Dict
import boto3
from botocore.config import Config


def load_schema_context(file: str) -> str:
    """Load the AIND data schema context from file."""
    schema_file = os.path.join(os.path.dirname(__file__), file)
    with open(schema_file, "r", encoding="utf-8") as f:
        return f.read()

schema_context = load_schema_context("aind_data_schema_context.txt")
models_context = load_schema_context("aind_data_schema_models_context.txt")



system_prompt=f"""
Your task is to solve this issue using the aind-data-migration-utils package. You will need to provide a query, a migration_callback, and a set of metadata core files to limit use to. You should return a run.py file (and ONLY the contents of the run.py, no extra context) which will solve the issue. Your run.py file should look something like this example file:

from aind_data_migration_utils.migrate import Migrator
import pandas as pd
import boto3
import json
import argparse
import logging

s3 = boto3.client('s3')
mangled_data = pd.read_csv('results_mangled.csv')


def repair_processing(record: dict) -> dict:
    \"\"\" Pull the record's original processing data from the original data source\"\"\"

    location = record['location']

    # location looks like s3://codeocean-s3datasetsbucket-1u41qdg42ur9/d48ec453-4cd6-47b7-8ad0-c08176bb42c1
    # separate the bucket and key prefix
    bucket_name, object_key = location.split('/')[2], '/'.join(location.split('/')[3:])

    # add the processing json
    object_key = object_key + '/processing.json'

    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    # Check that the response succeeded
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError(f"Failed to retrieve processing data from {{location}}")

    # # Read and parse JSON content
    json_content = response['Body'].read().decode('utf-8')  # Read and decode bytes
    processing_data = json.loads(json_content)  # Convert JSON string to dictionary

    logging.info(f"Retrieved processing data from {{location}} for record {{record['_id']}}")

    record["processing"] = processing_data

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
        query = {{
            "_id": {{"$in": mangled_data_batch['record_id'].tolist()}}
        }}
        migrator = Migrator(
            query=query,
            migration_callback=repair_processing,
            files=["processing"],
            path=f"./{{i}}_repair_processing",
            prod=not args.dev,
        )

        # Run the dry run
        migrator.run(full_run=False, test_mode=args.test)

        # If requested, run the full run
        if args.full_run:
            migrator.run(full_run=True, test_mode=args.test)

To help you understand how the data is organized I'm going to provide you with the full list of all models in the aind-data-schema and aind-data-schema-models pydantic packages, which are used to create records. This is a metadata schema built in pydantic and stored in a MongoDB database as JSON. Each record has a top-level "metadata" file that contains 7 files inside of it, "acquisition", "data_description", "procedures", "processing", "quality_control", "rig", "session", and "subject". Not all records use all these fields, and you should be careful to use the files parameter on the Migrator to only select for files that you actually need to make changes to. Be VERY CAREFUL to modify a real field in the metadata when you create your migration_callback function!

Here's the aind-data-schema classes:
{schema_context}

Here are the aind-data-schema-model classes:
{models_context}

Create the run.py to solve the issue and return the contents of the file. DO NOT provide any other text in your response, you should only return python code.
"""

def get_github_issues(repo_owner: str = "AllenNeuralDynamics", 
                     repo_name: str = "aind-scicomp-nautilex") -> List[Dict]:
    """
    Fetch GitHub issues for the specified repository using a personal access token.
    
    Args:
        repo_owner: The owner of the repository
        repo_name: The name of the repository
        
    Returns:
        List of dictionaries containing issue information
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GitHub access token not found in environment variables")
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch issues: {response.status_code}, {response.text}")
        
    return response.json()


def analyze_issues_with_bedrock(issues: List[Dict], system_prompt: str) -> List[str]:
    """
    Analyze GitHub issues using Amazon Bedrock Claude model.
    
    Args:
        issues: List of GitHub issue dictionaries
        system_prompt: System prompt to send to Claude
        
    Returns:
        List of Claude's responses as strings
    """
        
    # Create bedrock client with increased timeout
    config = Config(
        region_name='us-west-2',
        connect_timeout=20,  # a short time
        read_timeout=2400,     # a long time
        retries={'max_attempts': 1}
    )
    bedrock = boto3.client('bedrock-runtime', config=config)
    
    responses = []
    
    for issue in issues:
        # Combine issue content into a single string
        issue_content = f"Title: {issue['title']}\nBody: {issue['body']}"
        
        # Prepare the prompt
        prompt = f"{system_prompt}\n\nIssue Content:\n{issue_content}"
        
        # Call Bedrock Claude
        body = {
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 100000,
            "temperature": 0.5,
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-v2",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        run_py_str = response_body['completion']
        responses.append(run_py_str)
        
    return responses

if __name__ == "__main__":
    try:
        issues = get_github_issues()
        for issue in issues:
            print(f"Issue #{issue['number']}: {issue['title']}")
            print(f"State: {issue['state']}")
            print(f"URL: {issue['html_url']}")
            print("-" * 50)

        responses = analyze_issues_with_bedrock(issues, system_prompt=system_prompt)
        for i, response in enumerate(responses):
            print(f"\nAnalysis for issue #{i+1}:")
            print(response)
            print("-" * 50)
    
    except Exception as e:
        print(f"Error: {str(e)}")
