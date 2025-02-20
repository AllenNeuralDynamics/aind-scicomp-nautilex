# Nautilex Hackathon Lambda Functions

For our hackathon, please add the code for the lambda functions in this folder.

The Bedrock agent will have access to/ be able to trigger these lambda functions.

For each lambda function needs:
- requirements.txt
- lambda_function.py with main handler
- README.md


To build locally and upload to AWS Lambda Console:

```sh
# navigate to lambda function's folder
cd lambdas/aind-github-connector
# create venv
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
# copy to build folder
cp -r venv/Lib/site-packages build/
cp lambda_function.py build
```
Then zip the build folder and upload to lambda function in aws console.