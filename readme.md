# **What is the orchestrator**

It's a simple API written in python that runs steps configured in yaml files.

The orchestrator runs workflows, and each workflow is like a separate HTTP endpoint.

When an incoming request matches with the configurations (path + verbs), the workflow steps run sequentially, mirroring the results of the data collected during the execution of the steps. 

![](docs/result.jpg)

# **How it works**

## The Workflow configuration

The configuration is a yaml structure that must be placed in the `workflows/` directory

A workflow file looks like the following example:

```yaml
workflow:
  name: weather
  http:
    path: /${{ workflow.name }}
    verbs: [ 'get' ]

  steps:
    
    - name: Date
      async: true
      cmd:
        powershell: -NoProfile -Command "Get-Date"

    - name: Weather
      async: true
      request:
        get: https://wttr.in/Lisbon?format=3

    - name: Weather + Date
      async: false
      result: 
        - ${{ workflow.steps[0].result.stdout }}
        - ${{ workflow.steps[1].result.content }}
```

The curly braces `${{ ... }}` allow you to run small python scripts. It is very useful when it comes to playing with data transformation and formatting the output result.

The content of the curly braces runs within a `context` where you can find variables and functions for manipulating data.

Example:

* **python `fstrings`:**
  
  >${{ f"`{http.url}`/my-url/"} }} 

* **incomming workflow data (http post):**

  >${{ fromjson( `http.data` ) }}

* **accessing environment variables**

  >${{ workflow.env.PATH }}

* **accessing workflow data**

  >${{ workflow.steps[0].name }}


## **List of builtin functions and variables**

### **variables**

* `workflow` :  the current workflow configuration parsed as object

* `env` :  environment variables

* `http` :  the incomming http request object (orchestrator) 

    >`url` : http request full url

    >`host` : http request host name

    >`scheme` : http request scheme

    >`path` : http request path

    >`headers` : http request headers

    >`data` : http request post raw data (must be deserialized if json)

* `time` :  the python time module
    
    >https://docs.python.org/3/library/time.html

* `datetime` :  the python datetime module
    
    >https://docs.python.org/3/library/datetime.html


### **functions**

* `serializable()` :      converts an object to dictionary to be serializable

* `fromjson()` :          deserializes a json string to object

* `tojson()`:             serializes an object to json 

* `fromxml()` :           serializes an object to xml 

* `toxml()`               deserializes a xml string to object

* `object()`            converts a dictionary to object


## **Workflow Documentation**

```yaml
workflow:
  name: weather                       # just a name
  http:
    path: /weather                    # url path that triggers the workflow
    verbs: [ 'get' ]                  # http verb where the workflow is listening on

  steps:

    # STEP TYPE CMD
    - name: Date                      # just a name
      async: true                     # if true, the cmd will be async  (default is false)
      hidden: true                    # if true, the step result will be omitted from the response  (default is false)
      cmd:                            # the step type, use cmd to create a terminal step type
        powershell: <arguments> 
        /bin/sh: <arguments>
        python: <arguments>

    # STEP TYPE REQUEST
    - name: Weather
      async: true           # if true, the cmd will be async (default is false)
      hidden: true          # omitt the step result from the response (default is false)
      request:              # the step type, use request to create an http step type
        post: <url>         # the http request method [get, put,post,delete]
        data: <raw-data>    # some data use ${{ tojson()}} if you want to serialize an object
        headers:            # the http request headers (key-value pairs)
            KEY: VALUE    

    # STEP TYPE GENERIC
    - name: Output          # if the step type is not provided, it's just data
      hidden: true          # omitt the step result from the response (default is false)
      result:                
        - ${{ workflow.steps[0].result.stdout }}
        - ${{ workflow.steps[1].result.content }}

    - name: Output2                  
      result:                         
        - ${{ workflow.steps[3].result[0] }}
```


# Run it on docker

```
docker build . -t orchestrator
```

```
docker run -it -p 5000:5000 \
  -v "$(PWD)/workflows:/app/workflows" \
  jsoliveira/orchestrator
```
