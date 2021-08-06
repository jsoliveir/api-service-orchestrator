from models.WorkflowSteps.Base import WorkflowStep
from modules.expessions import Expression
import asyncio

class WorkflowStepShell(WorkflowStep):
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

