import { Octokit } from "@octokit/rest";
// import dotenv from 'dotenv';

// dotenv.config();

// https://github.com/AllenNeuralDynamics/aind-scicomp-nautilex
const REPO_NAME = "AllenNeuralDynamics/aind-scicomp-nautilex";

// auth
const token = process.env.GITHUB_TOKEN;
const octokit = new Octokit({ auth: token });

// enum of possible actions
const Actions = {
  GET_ISSUES: "get_issues",
  GET_BRANCHES: "get_branches",
  GET_PULL_REQUESTS: "get_pull_requests"
};

async function getIssues(event, context) {
  try {
    const { data } = await octokit.issues.listForRepo({
      owner: REPO_NAME.split('/')[0],
      repo: REPO_NAME.split('/')[1],
      state: "open",
      per_page: 30,
      page: 1
    });
    console.log(data);
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

async function getBranches(event, context) {
  try {
    const { data } = await octokit.repos.listBranches({
      owner: REPO_NAME.split('/')[0],
      repo: REPO_NAME.split('/')[1],
      per_page: 30,
      page: 1
    });
    console.log(data);
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

async function getPullRequests(event, context) {
  try {
    const { data } = await octokit.pulls.list({
      owner: REPO_NAME.split('/')[0],
      repo: REPO_NAME.split('/')[1],
      state: "open",
      per_page: 30,
      page: 1
    });
    console.log(data);
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

export const handler = async (event, context) => {
  console.log(`Received lambda event: ${JSON.stringify(event)}`);
  console.log(`Received lambda context: ${JSON.stringify(context)}`);

  const action = event.action;
  let response;

  try {
    if (action === Actions.GET_ISSUES) {
      response = await getIssues(event, context);
    } else if (action === Actions.GET_BRANCHES) {
      response = await getBranches(event, context);
    } else if (action === Actions.GET_PULL_REQUESTS) {
      response = await getPullRequests(event, context);
    } else {
      console.log(`Unknown action: ${action}`);
      return {
        statusCode: 400,
        body: JSON.stringify(`Unknown action: ${action}`)
      };
    }
    return {
      statusCode: 200,
      body: JSON.stringify(response)
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify(error.message)
    };
  }
};

// local testing
// (async () => {
//   await getIssues(null, null);
//   await getBranches(null, null);
//   await getPullRequests(null, null);
// })();