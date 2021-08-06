from abc import abstractmethod
from expessions import Expression
import requests as request
import pyodbc 
import asyncio


class WorkflowStep:
    def __init__(self, specs : dict):
        self._specs = specs
        self.name = specs['name']
        self.result = None
        self.hidden = specs.get("hidden",False)

    @staticmethod
    def create(specs) -> dict:
        if specs.get('cmd'):
            return WorkflowStepCmd(specs)
        elif specs.get('request'):
            return WorkflowStepRequest(specs)
        elif specs.get('sql'):
            return WorkflowStepSQL(specs)
        else:
             return WorkflowStep(specs)

    async def run(self,context,timeout=600):
        if self._specs.get('result'):
            self.result = Expression.eval(self._specs.get('result'),context)
        return self

class WorkflowStepRequest(WorkflowStep):
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
        

class WorkflowStepCmd(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__( specs)

    async def run(self,context,timeout=600) -> dict:
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
                type("Workflow.Step.Result", (), {
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


class WorkflowStepSQL(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__( specs)

    async def run(self,context,timeout=600) -> dict:
        cstring = self._specs.get('cstring')
        driver = self._specs.get('driver','SQL Server')
        sql = self._specs.get('sql')
        conn = pyodbc.connect(f"Driver={{{driver}}};" + cstring)
        cursor = conn.cursor()
        cursor.execute(";".join(sql))
        columns =  [ c[0] for c in cursor.description ]
        if columns[0]:
            self.result = [type('Object',(),dict(zip(columns,row))) for row in cursor.fetchall()]
        else:
            self.result = [row[0] for row in cursor.fetchall()]
        return self