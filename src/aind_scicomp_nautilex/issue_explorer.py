import os
import requests
import json
from typing import List, Dict
import boto3
from botocore.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from aind_scicomp_nautilex.lc_tools import query_docdb
from langchain_aws import ChatBedrock


def load_schema_context(file: str) -> str:
    """Load the AIND data schema context from file."""
    schema_file = os.path.join(os.path.dirname(__file__), file)
    with open(schema_file, "r", encoding="utf-8") as f:
        return f.read()

schema_context = load_schema_context("schema_context.txt")
models_context = load_schema_context("models_context.txt")


query1 = '{{"subject.subject_id": "731015"}}'
query2 = '{{"subject.breeding_info.breeding_group": "Slc17a6-IRES-Cre;Ai230-hyg(ND)"}}'
query3 = '{{"data_description.modality.abbreviation": {{"$in": ["ecephys"]}}}}'

system_prompt=f"""
Your task is to explore the issue provided by the user, which has to do with incorrect metadata stored in our document database. We're going to need to figure out the boundaries of the issue, how many records it affects, and make a suggestion for how the issue should be fixed. 

To help you understand how the data is organized I'm going to provide you with the full list of all models in the aind-data-schema and aind-data-schema-models pydantic packages, which are used to create records. This is a metadata schema built in pydantic and stored in a MongoDB database as JSON. Each record has a top-level "metadata" file that contains 7 files inside of it, "acquisition", "data_description", "procedures", "processing", "quality_control", "rig", "session", and "subject".

Here's the aind-data-schema classes:
{schema_context}

Here are the aind-data-schema-model classes:
{models_context}

And here are some examples of how you would make database queries for our metadata:
filter_query = {query1}
filter_query = {query2}
filter_query = {query3}
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


def post_github_comment(issue_number: int, comment: str,
                       repo_owner: str = "AllenNeuralDynamics",
                       repo_name: str = "aind-scicomp-nautilex") -> None:
    """
    Post a comment on a GitHub issue.
    
    Args:
        issue_number: The number of the issue to comment on
        comment: The comment text to post
        repo_owner: The owner of the repository
        repo_name: The name of the repository
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GitHub access token not found in environment variables")
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
    
    data = {
        "body": comment
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        raise Exception(f"Failed to post comment: {response.status_code}, {response.text}")



def explore_issues_with_bedrock(issues: List[Dict], system_prompt: str) -> List[str]:
    """
    Analyze GitHub issues using LangChain and Amazon Bedrock Claude model.
    
    Args:
        issues: List of GitHub issue dictionaries
        system_prompt: System prompt to send to Claude
        
    Returns:
        List of Claude's responses as strings
    """
    # Initialize Bedrock Claude via LangChain
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs={"max_tokens": 4096},
        region_name="us-west-2"
    )
    
    # Create prompt templates for each step
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + """
        Based on the issue description, create a MongoDB filter query (without any projections, aggregations, or modifications) that will help identify affected records.
        
        For example, a query to find all records with the funder "PGA" could be done with 
        {{
            "data_description.funding_source": {{
            "$elemMatch": {{
                "funder": "PGA"
            }}
            }}
        }}
        Respond now with a simple filter query that will find the affected records. Note that the `Metadata` class containing the seven subfiles is what's stored in each record therefore you should NOT start your queries with "metadata". Queries in our database should always use the pattern "file.field.subfield" (etc, as necessary). Your query should not use any special mongodb features that require the $ symbol. 

        Format your response as a JSON object with a single key 'query' containing the MongoDB query dictionary. Do not include any other text in your response.
        """),
        ("user", "{issue_content}")
    ])
    
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + """
        Analyze the query results and the original issue to create a comprehensive understanding of what's occuring and how we will fix it. Note that we won't be using MongoDB directly to fix the issue we'll be using a wrapper to do it that we've developed. The wrapper only needs to be provided with the query, which metadata core files are affected, and a callback function that will modify individual records in the database. The callback function will take a dictionary containing the record and return the same dictionary, with the issue repaired.

        Include:
        1. How many records are affected 
        2. What the specific metadata issues are
        3. What simple filter query can be used to retrieve the appropriate records
        4. What metadata core file classes are affected
        5. What your suggested callback function would look like
        4. Any potential risks or considerations"""),
        ("user", "Issue: {issue_content}\n\nNumber of records: {query_len}\n\nQuery Results (note that these were truncated at five if there were more): {query_results}")
    ])
    
    json_parser = JsonOutputParser()
    
    responses = []
    for issue in issues:
        print(f"\nProcessing Issue #{issue['number']}: {issue['title']}")
        
        # Step 1: Generate query
        print("\nStep 1: Generating MongoDB query...")
        issue_content = f"Title: {issue['title']}\nBody: {issue['body']}"
        query_chain = query_prompt | llm | json_parser
        query_result = query_chain.invoke({"issue_content": issue_content})
        print(f"Generated query: {json.dumps(query_result['query'], indent=2)}")
        
        # Step 2: Execute query
        print("\nStep 2: Executing query against database...")
        db_results = query_docdb({
            "query": query_result['query'],
        })
        print(f"Found {len(db_results)} matching records")

        if len(db_results) == 0:
            # Query failed, retry
            print("\nNo results found. Retrying with simplified query...")
            retry_prompt = ChatPromptTemplate.from_messages([
                ("system", """The original query returned no results. Please generate a simplified version of the query that is more likely to match records.
                Format your response as a JSON object with a single key 'query' containing the MongoDB query dictionary. Do not include any other text in your response.
                Consider:
                - Using fewer filter conditions
                - Checking if field names are correct
                - Using simpler MongoDB operators
                - Broadening the search criteria"""),
                ("user", f"Original query: {json.dumps(query_result['query'], indent=2)}\nIssue: {issue_content}")
            ])
            
            retry_chain = retry_prompt | llm | json_parser
            retry_query = retry_chain.invoke({})
            print(f"Retrying with query: {json.dumps(retry_query['query'], indent=2)}")
            
            db_results = query_docdb({
                "query": retry_query['query']
            })
            print(f"Found {len(db_results)} matching records after retry")
            
            if len(db_results) == 0:
                print("Warning: Still no results found after retry")
                raise ValueError("Unable to generate valid query")

        if len(db_results) > 5:
            db_results = db_results[:5]
        
        # Step 3: Analyze results and generate response
        print("\nStep 3: Analyzing results...")
        print(f"\n\nFound {len(db_results)} records:\n\n{db_results}")
        analysis_chain = analysis_prompt | llm
        analysis = analysis_chain.invoke({
            "issue_content": issue_content,
            "query_results": db_results,
            "query_len": len(db_results),
        })
        print("Analysis complete")
        
        # Step 4: Post response as comment
        print("\nStep 4: Posting response to GitHub...")
        post_github_comment(issue['number'], analysis.content)
        responses.append(analysis.content)
        print("Response posted successfully")
    
    return responses

if __name__ == "__main__":
    try:
        # Get and display all issues
        issues = get_github_issues()
        issues = [issues[0]]
        print("\nFetched GitHub Issues:")
        for issue in issues:
            print(f"Issue #{issue['number']}: {issue['title']}")
            print(f"State: {issue['state']}")
            print(f"URL: {issue['html_url']}")
            print("-" * 50)

        # Explore issues and post results
        print("\nExploring issues and posting results...")
        explore_issues_with_bedrock(issues, system_prompt=system_prompt)
        print("\nCompleted issue exploration and posted responses to GitHub.")
    
    except Exception as e:
        print(f"Error occurred during issue exploration: {str(e)}")
        raise e
