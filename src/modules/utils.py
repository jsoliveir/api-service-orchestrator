from copy import Error
from datetime import datetime

def serializable(obj):
    if type(obj) is Exception:
        ref = repr(obj)
    elif type(obj) is list:
        ref = [serializable(v) for v in obj ]
    elif hasattr(obj,"__dict__"):
        ref = dict(obj.__dict__)
    elif type(obj) is dict:
        ref = obj
    elif type(obj) is datetime:
        ref = str(obj)
    else:
        ref = obj
    
    if type(ref) is dict:
        return { 
            key :serializable(ref[key])
            for key in list(filter(lambda k: not k.startswith("_"), ref.keys()))
        }
    else:
        return ref