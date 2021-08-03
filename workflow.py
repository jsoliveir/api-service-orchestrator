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

class Workflow:
    def __init__(self,file):
        with io.open(file, 'r') as stream:
            workflow = yaml.safe_load(stream)['workflow']
        self.name = workflow["name"]

        self._specs = workflow

        self.steps =  [ 
            WorkflowStep.create(s)
            for s in workflow["steps"] 
        ]

    async def run(self,ctx) -> dict:
        try:
            print("workflow:",self.name)
            context = {"workflow": self}
            if hasattr(ctx,"url"):
                context["url"]=ctx.url
                context["host"]=ctx.host
                context["scheme"]=ctx.scheme
                context["path"]=ctx.full_path
                context["headers"]= dict(ctx.headers)
                context["data"]=ctx.data.decode('utf-8')
            else:
                context = {**context, **ctx}
            
            context = {
                **context,
                "datetime": datetime,
                # expression functions
                "time": time,
                "asyncio": asyncio,
                "tojson" : json.dumps,
                "fromjson" : json.loads,
                "serializable" : serializable,
                "toxml" : xml.etree.ElementTree.tostring,
                "fromxml": xml.etree.ElementTree.fromstring
            }

            asynctasks = []
            for step in self.steps:
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