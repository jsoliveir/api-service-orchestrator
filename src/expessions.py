import re
import copy

class Expression:
    @staticmethod
    def eval(expression,context:dict = {}):
        try:
            if type(expression) is list:
                return [ Expression.eval(e,context) for e in expression]
            elif type(expression) is str:
                expression = expression.strip()
                if re.search("\$\{{(.*)\}}",str(expression)):
                    match = re.split("\$\{{(.*?)\}}",str(expression))
                    obj = eval(str(match[1]),globals(),context)
                    if match[0]:
                        expression = re.sub("\$\{{.*?\}}",str(obj),str(expression),1)
                        return Expression.eval(expression,context)
                    else:
                        return copy.deepcopy(obj)
                return expression
            elif type(expression) is dict:
                return { k: Expression.eval(expression[k],context) for k in expression.keys() }
            elif hasattr(expression,"__dict__"):
                obj = expression.__dict__
                return { k: Expression.eval(obj[k],context) for k in obj.keys() }
            else:
                return expression
        except Exception as ex:
            raise SyntaxError(str(ex))
