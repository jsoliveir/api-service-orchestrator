from abc import abstractmethod
import asyncio
from re import I
import re
from sys import stdout
from expessions import Expression
import subprocess
import requests as request
import logging


class WorkflowStep:
    def __init__(self, specs : dict):
        self._specs = specs
        self.name = specs['name']
        self.result = None

    @staticmethod
    def create(specs) -> dict:
        if specs.get('cmd'):
            return WorkflowStepCmd(specs)
        elif specs.get('request'):
            return WorkflowStepRequest(specs)
        else:
             return WorkflowStep(specs)

    async def run(self,context,timeout=600):
        try:
            if self._specs.get('result'):
                self.result = Expression.eval(self._specs.get('result'),context)
            return self
        except Exception as ex:
           raise ex

class WorkflowStepRequest(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__(specs)

    async def run(self,context,timeout=600) -> dict:      
        try:
            headers =   self._specs['request'].get('headers')
            args =  {
                'verify':False,
                'timeout':timeout,
                'data':Expression.eval(self._specs['request'].get('data'),context),
                'url':Expression.eval(self._specs['request'].get('get'),context),
                'headers': headers
            }
            if headers:
                headers = { 
                    h: Expression.eval(headers[h],context) for h in headers.keys() 
                }
            if self._specs['request'].get('get'):
                output = await asyncio.run_in_executor(None,request.get,**args)
            if self._specs['request'].get('post'):
                output = await asyncio.run_in_executor(None,request.post,**args)
            if self._specs['request'].get('put'):
                output = await asyncio.run_in_executor(None,request.put,**args)
            if self._specs['request'].get('delete'):
                output = await asyncio.run_in_executor(None,request.delete,**args)
            
            self.result = type("Object", (), { 
                'code': output.status_code, 
                'headers': dict(output.headers),
                'content':output.content.decode('utf-8')
            })

            if self._specs.get('result'):
                self.result = Expression.eval(self._specs.get('result'),context)

            return self
        except Exception as ex:
           raise ex
        

class WorkflowStepCmd(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__( specs)

    async def run(self,context,timeout=600) -> dict:
        try:
            cmd =  self._specs.get('cmd')
            result = []
            for k in cmd.keys():
                args = Expression.eval(f"{cmd[k]}",context)
                process = await asyncio.create_subprocess_shell(
                    f"{k} {args}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)

                result.append(
                    type("Object", (), {
                    'exit': process.returncode, 
                    'stdout': stdout.decode("utf-8").strip() if stdout  else None, 
                    "stderr": stderr.decode("utf-8").strip() if stderr  else None
                }))
                
            if len(result) == 1:
                self.result = result[0]
            elif len(result) > 1:
                self.result = result

            if self._specs.get('result'):
                self.result = Expression.eval(self._specs.get('result'),context)
            return self
        except Exception as ex:
           raise ex
