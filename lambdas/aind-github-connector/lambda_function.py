from datetime import datetime
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
    GET_ONE_ISSUE = "get_one_issue"
    GET_BRANCHES = "get_branches"
    GET_PULL_REQUESTS = "get_pull_requests"
    GET_ONE_PULL_REQUEST = "get_one_pull_request"

def get_issues(event, context):
    '''Gets first page of issues'''
    issues = repo.get_issues(state="open")
    first_page = issues.get_page(0)
    return json.dumps([issue.raw_data for issue in first_page])

def get_one_issue(event, context):
    '''Gets one issue given an issue number'''
    # get issue number from event parameters'
    issue_number = int(event['parameters'][0]['value'])
    issue = repo.get_issue(issue_number)
    return json.dumps(issue.raw_data)

def get_branches(event, context):
    '''Gets first page of branches'''
    branches = repo.get_branches()
    first_page = branches.get_page(0)
    return json.dumps([branch.raw_data for branch in first_page])

def get_pull_requests(event, context):
    '''Gets first page of OPEN PRs'''
    pulls = repo.get_pulls(state="open")
    first_page = pulls.get_page(0)
    return json.dumps([pr.raw_data for pr in first_page])

def get_one_pull_request(event, context):
    '''Gets one PR given a PR number'''
    # get pr number from event parameters'
    pr_number = int(event['parameters'][0]['value'])
    pr = repo.get_issue(pr_number)
    return json.dumps(pr.raw_data)

# create PR with title and body
def create_pull_request(event, context):
    '''Creates a PR with code from event body'''
    # get issue number from api path
    apiPath = event['apiPath']
    issue_number = int(apiPath.split('/')[-1])
    # get source issue
    issue = repo.get_issue(issue_number)
    issue_title = issue.title
    # get the code content from the event body
    # code = event['requestBody']['code']
    code = "print('Hello World')"
    # create a new branch
    # datetime stamp
    datetime_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"autofix-issue-{issue_number}-{datetime_stamp}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=repo.get_branch("main").commit.sha)
    # create a new folder at root/scripts/{issue_number}-{datetime_stamp}
    folder_name = f"scripts/{issue_number}-{datetime_stamp}"
    repo.create_file(path=f"{folder_name}/run.py", message=f"feat: add script for issue {issue_number}", content=code, branch=branch_name)
    # create a PR
    pr = repo.create_pull(title=f"Fix: {issue_title} ({datetime_stamp})", body=f"Auto-fix for issue {issue_number}", head=branch_name, base="main")
    # return the PR data
    return json.dumps(pr.raw_data)

def lambda_handler(event, context):
    '''Main lambda handler'''
    print(f"Received lambda event: {event}")
    print(f"Received lambda context: {context}")

    # this lambda can only can be triggered by a Bedrock Agent
    # agent = event['agent']
    actionGroup = event['actionGroup']
    apiPath = event['apiPath']
    httpMethod =  event['httpMethod']
    # parameters = event.get('parameters', [])
    # requestBody = event.get('requestBody', {})


    # Extract action from httpMethod and apiPath
    action = None
    if httpMethod == "GET":
        # /issues
        if apiPath == "/issues":
            action = Actions.GET_ISSUES
        # /issue/{issueNumber}
        elif apiPath.startswith("/issue/"):
            action = Actions.GET_ONE_ISSUE
        # /branches
        elif apiPath == "/branches":
            action = Actions.GET_BRANCHES
        # /pull-requests
        elif apiPath == "/pull-requests":
            action = Actions.GET_PULL_REQUESTS
        # /pull-request/{pullRequestNumber}
        elif apiPath.startswith("/pull-request/"):
            action = Actions.GET_ONE_PULL_REQUEST

    else:
        print(f"Unsupported HTTP method: {httpMethod}")
        return {
            "statusCode": 400,
            "body": json.dumps(f"Unsupported HTTP method: {httpMethod}")
        }
    
    # Perform action
    if action == Actions.GET_ISSUES:
        response = get_issues(event, context)
    elif action == Actions.GET_ONE_ISSUE:
        response = get_one_issue(event, context)
    elif action == Actions.GET_BRANCHES:
        response = get_branches(event, context)
    elif action == Actions.GET_PULL_REQUESTS:
        response = get_pull_requests(event, context)
    else:
        print(f"Unknown action: {apiPath}")
        return {
            "statusCode": 400,
            "body": json.dumps(f"Unknown action: {apiPath}")
        }

    # this response format is requred for Bedrock agent!
    responseBody =  {
        "application/json": {
            "body": response # "The API {} was called successfully!".format(apiPath)
        }
    }

    action_response = {
        'actionGroup': actionGroup,
        'apiPath': apiPath,
        'httpMethod': httpMethod,
        'httpStatusCode': 200,
        'responseBody': responseBody
    }

    api_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    print("Response: {}".format(api_response))

    return api_response


# # local testing
# if __name__ == "__main__":
#     get_issues(None, None)
#     get_branches(None, None)
#     get_pull_requests(None, None)