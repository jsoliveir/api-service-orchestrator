from models.WorkflowSteps.Base import WorkflowStep
from modules.expessions import Expression
import requests as request
import asyncio

class WorkflowStepHttp(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__(specs)

    async def run(self,context,timeout=600) -> dict:
        try:
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
                'data':Expression.eval(self._specs['request'].get('data'),context)
            }

            if self._specs['request'].get('get'):
                kargs["url"] = Expression.eval(self._specs['request'].get('get'),context)
                output = await loop.run_in_executor(None,lambda: request.get(**kargs))
            if self._specs['request'].get('post'):
                kargs["url"] = Expression.eval(self._specs['request'].get('post'),context)
                output = await loop.run_in_executor(None,lambda: request.post(**kargs))
            if self._specs['request'].get('put'):
                kargs["url"] = Expression.eval(self._specs['request'].get('put'),context)
                output = await loop.run_in_executor(None,lambda: request.put(**kargs))
            if self._specs['request'].get('delete'):
                kargs["url"] = Expression.eval(self._specs['request'].get('delete'),context)
                output = await loop.run_in_executor(None,lambda: request.delete(**kargs))
            
            self.result = output

            if self._specs.get('result'):
                self.result = Expression.eval(self._specs.get('result'),context)

            return self
        except Exception as ex:
            self.result = Exception(repr(ex))
            raise ex
        