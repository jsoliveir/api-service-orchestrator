from models.WorkflowSteps.Base import WorkflowStep
from modules.expessions import Expression
import requests as request
import asyncio

class WorkflowStepHttp(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__(specs)

    async def run(self,context,timeout=600) -> dict:
        headers =   self._specs['request'].get('headers')
        loop = asyncio.get_event_loop()
        
        if headers:
            headers = { 
                h: Expression.eval(headers[h],context) for h in headers.keys() 
            }

        kargs={
            'verify':False,
            'headers': headers,
            'timeout': timeout,
            'url':Expression.eval(self._specs['request'].get('get'),context),
            'data':Expression.eval(self._specs['request'].get('data'),context)
        }

        if self._specs['request'].get('get'):
            output = await loop.run_in_executor(None,lambda: request.get(**kargs))
        if self._specs['request'].get('post'):
            output = await loop.run_in_executor(None,lambda: request.post(**kargs))
        if self._specs['request'].get('put'):
            output = await loop.run_in_executor(None,lambda: request.put(**kargs))
        if self._specs['request'].get('delete'):
            output = await loop.run_in_executor(None,lambda: request.delete(**kargs))
        
        self.result = type("Workflow.Step.Result", (), { 
            'code': output.status_code, 
            'headers': dict(output.headers),
            'content':output.content.decode('utf-8').strip()
        })

        if self._specs.get('result'):
            self.result = Expression.eval(self._specs.get('result'),context)

        return self
        