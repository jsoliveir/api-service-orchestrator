from expessions import Expression
from steps import WorkflowStep
from utils import serializable
from dict2xml import dict2xml
from datetime import datetime 
import xml.etree.ElementTree
import asyncio
import logging
import json 
import yaml
import time
import io
import os

class Workflow:
    def __init__(self,file):
        with io.open(file, 'r') as stream:
             self._specs = yaml.safe_load(stream)['workflow']
        
        self._context = {
            "time": time,
            "workflow": self,
            "datetime": datetime,
            "env": type('Workflow.Env',(),dict(os.environ)),           
            "fromjson" : json.loads,
            "serializable" : serializable,
            "tojson" : lambda o: json.dumps(serializable(o)),
            "toxml" : lambda o: dict2xml(serializable(o)),
            "fromxml": xml.etree.ElementTree.fromstring,
            "object": lambda d: type('Object',(),d)
        }

        self.vars = type('Workflow.Vars',(),Expression.eval(self._specs.get("vars",{}),self._context))
        self.name = Expression.eval(self._specs["name"],self._context)
        self.http = type('Workflow.Http',(),Expression.eval(self._specs["http"],self._context))
        self.steps =  [ 
            WorkflowStep.create(s)
            for s in self._specs["steps"] 
        ]
        
    async def run(self,http) -> dict:
        try:
            context = {
                **self._context,
                "http": {
                    'url':http.url,
                    'host': http.host,
                    'scheme':http.scheme,
                    'path':http.full_path,
                    'headers':dict(http.headers),
                    'data':http.data.decode('utf-8')
                }
            }
            asynctasks = []
            for step in self.steps:
                context["self"] = step
                if step._specs.get('async'):
                    asynctasks.append(asyncio.ensure_future(step.run(context)))
                else:
                    await asyncio.gather(*asynctasks)
                    await step.run(context)
                    asynctasks.clear()

            return serializable(self)
        except Exception as ex:
            logging.exception(ex)
            raise ex