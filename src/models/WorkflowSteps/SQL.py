from models.WorkflowSteps.Base import WorkflowStep
from modules.expessions import Expression
import pyodbc
import os
import re

class WorkflowStepSql(WorkflowStep):
    def __init__(self, specs: dict):
        super().__init__( specs)

    async def run(self,context,timeout=600) -> dict:
        cstring = self._specs.get('cstring')
        drivers =  list(filter(lambda d: re.search(self._specs.get('driver',''),d) ,pyodbc.drivers()))
        print(drivers,pyodbc.drivers())
        sql = Expression.eval(self._specs.get('sql'),context)
        conn = pyodbc.connect(f"Driver={{{drivers[0]}}};" + cstring)
        cursor = conn.cursor()
        cursor.execute(";".join(sql))
        columns =  [ c[0] for c in cursor.description ]
        if columns[0]:
            self.result = [type('Object',(),dict(zip(columns,row))) for row in cursor.fetchall()]
        else:
            self.result = [row[0] for row in cursor.fetchall()]

        if self._specs.get('result'):
            self.result = Expression.eval(self._specs.get('result'),context)

        return self