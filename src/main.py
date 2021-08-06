from flask import Flask, request,Response
from modules.utils import serializable
from models.Workflows import Workflow
import logging
import json
import glob
import os


app = Flask(__name__)

workflows = [ Workflow(file) for file in glob.iglob(f'{os.environ.get("WORKFLOWS_PATH","workflows")}/*.yml',recursive=True) ] 

@app.route('/<path:route>')
async def trigger_http(route):
    response = Response()
    try:
        for workflow in filter(lambda w: w.http, workflows):
            if request.path.lower() in workflow.http.path:
                if request.method.lower() in workflow.http.verbs:
                    response.headers["Content-Type"]  = "application/json"
                    result = await workflow.run(request)
                    
                    response.data = json.dumps(serializable({
                        "name" : workflow.name,
                        "steps": [s for s in filter(lambda s: not s.hidden or type(s.result) is Exception,workflow.steps)],
                        "success" : workflow.success
                    }))
                    response.status_code = 200 if result.success else 500 
                    return response
        response.data = "<h1> 404 - Workflow not found/h1>"
        response.status_code = 404
        return response
    except Exception as ex:
        logging.exception(ex)
        response.data = json.dumps({ "error": repr(ex)})
        response.status_code = 500
        return response

if __name__ == "__main__":
    app.run()   
