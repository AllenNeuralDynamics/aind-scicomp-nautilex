# Nautilex Hackathon Lambda Functions

For our hackathon, please add the code for the lambda functions in this folder.

The Bedrock agent will have access to/ be able to trigger these lambda functions.

For each lambda function needs:
- requirements.txt
- lambda_function.py with main handler
- README.md


To build locally and upload to AWS Lambda Console:

Run a docker a python3.12 docker container and mount a current directory:
`docker run -it -v /${PWD}/lambdas/aind-github-connector/docker-build:/usr/src/app python:3.12 bash`

Copy `lambda_function.py` and `requirements.txt` to the **docker-build** folder

From the docker interactive shell
```sh
apt update -y
apt install zip -y
# navigate to lambda function's folder
cd usr/src/app
# create venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir build
cp lambda_function.py build && cp requirements.txt build && cp -r venv/lib/python3.12/site-packages/* build
rm -r build/pip
cd build
zip -r9 ../lambda.zip .
chmod 444 ../lambda.zip
```
Upload the lambda.zip found in docker-build folder to AWS lambda 

