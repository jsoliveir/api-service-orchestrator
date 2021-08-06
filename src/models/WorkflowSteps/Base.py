from modules.expessions import Expression

class WorkflowStep:
    def __init__(self, specs : dict):
        self._specs = specs
        self.name = specs['name']
        self.result = None
        self.hidden = specs.get("hidden",False)

    async def run(self,context,timeout=600):
        if self._specs.get('result'):
            self.result = Expression.eval(self._specs.get('result'),context)
        return self

    class Factory:
        @staticmethod
        def create(specs) -> dict:
            if specs.get('cmd'):
                from models.WorkflowSteps.Shell import WorkflowStepShell
                return WorkflowStepShell(specs)
            elif specs.get('request'):
                from models.WorkflowSteps.Http import WorkflowStepHttp
                return WorkflowStepHttp(specs)
            elif specs.get('sql'):
                from models.WorkflowSteps.SQL import WorkflowStepSQL
                return WorkflowStepSQL(specs)
            else:
                return WorkflowStep(specs)