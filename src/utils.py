from copy import Error


def serializable(obj):
  
    if type(obj) is Error:
        return repr(obj)
    elif type(obj) is list:
        return [serializable(v) for v in obj ]
    elif hasattr(obj,"__dict__"):
        ref = obj.__dict__
    elif type(obj) is dict:
        ref = obj
    else:
        return obj

    new={}
    for key in list(filter(lambda k: not k.startswith("_"), ref.keys())):
        new[key] = serializable(ref[key]) 
    
    return new