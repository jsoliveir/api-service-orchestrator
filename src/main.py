from flask import Flask, request,Response
from threading import Thread
from workflow import Workflow
import asyncio
import logging
import json
import glob
import re
import os

app = Flask(__name__)

workflows = [ Workflow(file) for file in glob.iglob('workflows/*.yml',recursive=True) ] 

@app.route('/<path:route>')
async def trigger_http(route):
    response = Response()
    try:
        for workflow in filter(lambda w: w.http, workflows):
            if request.path.lower() in workflow.http.path:
                if request.method.lower() in workflow.http.verbs:
                    response.headers["Content-Type"]  = "application/json"
                    result = await workflow.run(request)
                    response.data = json.dumps(result)
                    response.status_code = 200
                    return response
        response.data = "<h1>Not Found</h1>"
        response.status_code = 404
        return response
    except Exception as ex:
        logging.exception(ex)
        response.data = json.dumps({ "error": repr(ex)})
        response.status_code = 500
        return response

if __name__ == "__main__":
    app.run()   
