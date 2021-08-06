from models.WorkflowSteps.Base import WorkflowStep
from modules.expessions import Expression
import pyodbc

class WorkflowStepSQL(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__( specs)

    async def run(self,context,timeout=600) -> dict:
        cstring = self._specs.get('cstring')
        driver = self._specs.get('driver','SQL Server')
        sql = self._specs.get('sql')
        conn = pyodbc.connect(f"Driver={{{driver}}};" + cstring)
        cursor = conn.cursor()
        cursor.execute(Expression.eval(";".join(sql),context))
        columns =  [ c[0] for c in cursor.description ]
        if columns[0]:
            self.result = [type('Object',(),dict(zip(columns,row))) for row in cursor.fetchall()]
        else:
            self.result = [row[0] for row in cursor.fetchall()]

        if self._specs.get('result'):
            self.result = Expression.eval(self._specs.get('result'),context)

        return self