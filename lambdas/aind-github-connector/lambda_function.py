import json
import requests

from github import Github
from github import Auth
import os
from pprint import pprint
import json

# loadenv
from dotenv import load_dotenv
load_dotenv()

# https://github.com/AllenNeuralDynamics/aind-scicomp-nautilex
REPO_NAME = "AllenNeuralDynamics/aind-scicomp-nautilex"

# auth
token = os.getenv('GITHUB_TOKEN', '...')
auth = Auth.Token(token)

# github instance
github = Github(auth=auth)
repo = github.get_repo(REPO_NAME)
  

# enum of possible actions
class Actions:
    GET_ISSUES = "get_issues"
    GET_BRANCHES = "get_branches"
    GET_PULL_REQUESTS = "get_pull_requests"

def get_issues(event, context):
    '''Gets first page of issues'''
    issues = repo.get_issues(state="open")
    first_page = issues.get_page(0)
    pprint(first_page)
    return json.dumps([issue.raw_data for issue in first_page])

def get_branches(event, context):
    '''Gets first page of branches'''
    branches = repo.get_branches()
    first_page = branches.get_page(0)
    pprint(first_page)
    return json.dumps([branch.raw_data for branch in first_page])

def get_pull_requests(event, context):
    '''Gets first page of OPEN PRs'''
    pulls = repo.get_pulls(state="open")
    first_page = pulls.get_page(0)
    pprint(first_page)
    return json.dumps([pr.raw_data for pr in first_page])

def lambda_handler(event, context):
    ''
    print(f"Received lambda event: {event}")
    print(f"Received lambda context: {context}")

    # expect event to have format:
    # {
    #   "action": "get_issues" # type of action to perform
    # }
    action = event.get("action")
    if action == Actions.GET_ISSUES:
        response = get_issues(event, context)
    elif action == Actions.GET_BRANCHES:
        response = get_branches(event, context)
    elif action == Actions.GET_PULL_REQUESTS:
        response = get_pull_requests(event, context)
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


# # local testing
# if __name__ == "__main__":
#     get_issues(None, None)
#     get_branches(None, None)
#     get_pull_requests(None, None)