# aind-scicomp-nautilex

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
![Python](https://img.shields.io/badge/python->=3.10-blue?logo=python)



## Hackathon goals

Our goal is a closed-loop set of agents that discover issues in the metadata, report those as issues on GitHub, and then suggest code in a pull request to repair the issue. 

### Issue Discovery

Agents that use aind-data-schema, and DocDB via the `aind-data-access-api` to discover issues in the database, and write those issues to GitHub (to this repo).

  - [ ] Lambda: Pull from DocDB with a query
  - [ ] Lambda: Github add issue
  - [x] Knowledge base: aind-data-schema / aind-data-access-api
  - [ ] Exploration agent: pulls records from docdb to explore the issue in detail
  - [ ] Issue agent: summarizes results and posts a GitHub issue with the suggested fix

### Creating Migration Scripts

Agents that pull issues from the repo and use the `aind-data-migration-utils` wrapper to write a query and migrator function to 

- [ ] Lambda: Pull issues from Github
- [ ] Lambda: Push code to Github (lambda should probably handle creating a named subfolder and put code in a `run.py` file)
- [ ] Lambda: Open PR
- [ ] Migration agent: Uses the issue to create a query + migration function that should fix the issue
- [ ] Dry run agent: Runs the dry run (is this possible?) and checks for errors, sends code back to migration agent with errors if needed
- [ ] PR agent: Commits code and creates a pull request describing what was done and the suggested plan to fix it
