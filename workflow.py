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

class Workflow:
    def __init__(self,file):
        with io.open(file, 'r') as stream:
             self._specs = yaml.safe_load(stream)['workflow']
            
        self.name = Expression.eval(self._specs["name"],{'workflow':self})
        self.http = type('Workflow.Http',(),Expression.eval(self._specs["http"],{'workflow':self}))
        self.steps =  [ 
            WorkflowStep.create(s)
            for s in self._specs["steps"] 
        ]

    async def run(self,ctx) -> dict:
        try:
            print("workflow:",self.name)
            context = {"workflow": self}
            if hasattr(ctx,"url"):
                context["http"]= {
                    'url':ctx.url,
                    'host': ctx.host,
                    'scheme':ctx.scheme,
                    'path':ctx.full_path,
                    'headers':dict(ctx.headers),
                    'data':ctx.data.decode('utf-8')
                }
            else:
                context = {**context, **ctx}
            
            context = {
                **context,
                "datetime": datetime,
                "time": time,
                "fromjson" : json.loads,
                "serializable" : serializable,
                "tojson" : lambda o: json.dumps(serializable(o)),
                "toxml" : lambda o: dict2xml(serializable(o)),
                "fromxml": xml.etree.ElementTree.fromstring
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