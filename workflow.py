from expessions import Expression
from utils import serializable
from requests.api import get
from steps import WorkflowStep
import logging
import yaml
import io
import asyncio
import time
from datetime import datetime 
#plugins
import json 
import xml.etree.ElementTree
from dict2xml import dict2xml

class Workflow:
    def __init__(self,file):
        with io.open(file, 'r') as stream:
            workflow = yaml.safe_load(stream)['workflow']
            
        self.name = Expression.eval(workflow["name"],{'workflow':self})

        self._specs = workflow
        self._specs["trigger"] = Expression.eval(workflow.get("trigger"),{'workflow':self}) 

        self.steps =  [ 
            WorkflowStep.create(s)
            for s in workflow["steps"] 
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