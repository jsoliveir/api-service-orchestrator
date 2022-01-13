# **What is the orchestrator**

It's a simple Rest API / Orchestrator.

The orchestrator runs workflows written in yaml. 

Each workflow serves a distinct HTTP endpoint. If an incoming request matches with the `path` + `verb` , the workflow will run the steps sequentially. 
The data structure returned by the workflow, is the result of the data collected/produced by the steps. 

![](docs/result.jpg)

# The Workflow configuration

The configuration is a yaml structure that must be placed in the `workflows/` directory

A workflow file looks like the following example:

[examples/weather.yml](examples/weather.yml)

```yaml
workflow:
  name: weather
  http:
    path: /weather
    verbs: [ 'get' ]

  steps:
    - name: Get Weather
      request:
        get: https://wttr.in/Lisbon?format=3

    - name:  Datetime + Weather
      result: 
        - ${{ datetime.now() }}
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


# **List of builtin functions and variables**

## **variables**

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


## **functions**

* `str()` :               converts an object to string

* `repr()` :              converts an object to its string representation

* `dict()` :              converts an object to a dictionary

* `serializable()` :      ensures an object to be serializable

* `fromjson()` :          deserializes a json string to object

* `tojson()`:             serializes an object to json 

* `fromxml()` :           serializes an object to xml 

* `toxml()`               deserializes a xml string to object

* `object()`            converts a dictionary to object


# **Workflow Structure**

```yaml
workflow:
  name:  /directories           # just a name
  http:
    path: ${{ workflow.name }}  # url path that triggers the workflow (eg.: /get/data )
    verbs:                      # http verb/method of the workflow
      - 'put' 
      - 'get' 
      - 'post' 
      - 'delete' 

  steps:

    - name: Get Directories List         
      hidden: true
      cmd: 
        powershell: -NoProfile -Command "Get-ChildItem -Directory c:\ | ConvertTo-Json"
      result:
        OK: ${{ True if not workflow.steps[0].result.stderr else False }}
        STDOUT: ${{ workflow.steps[0].result.stdout }}

    - name: Post the directories
      async: true         
      hidden: true
      request:             
        post: http://api.pt/directories
        data: ${{ workflow.steps[0].result.STDOUT }}
        headers:
          Content-Type: application/json 
      result:
        OK: ${{ True if not workflow.steps[1].result.status_code == 200 else False }}
        CODE: ${{ workflow.steps[1].result.status_code }}

    - name: Log To SQL
      hidden: true 
      cstring: server=sql.internbank.no,1433; Trusted_Connection=yes
      sql: 
        - INSERT INTO STATUS VALUES('${{ workflow.steps[1].result.CODE }}')
      result:
        OK: ${{ True if workflow.steps[2].result else False }}
          
    - name: Output Status 
      result:                
        - Powershell Status = ${{ 'OK' if workflow.steps[0].result else 'FAIL' }}
        - Request Status = ${{ 'OK' if workflow.steps[0].result else 'FAIL' }}
        - Logs Status = ${{ 'OK' if workflow.steps[0].result else 'FAIL' }}
```

# The Steps:

## Basic Step

```yaml
    - name: <string>           # the step name
      async: <bool>            # if true, the cmd will be async  (default is false)
      hidden: true             # omitt the step result from the response (default is false)
      result: <string, object> # the output of the step 
     
```

 ## Command Step
```yaml
  - name: <string>                  # the step name
    async: <bool>                   # if true, the cmd will be async  (default is false)
    hidden: <bool>                  # if true, the step result will be omitted from the response  (default is false)
    cmd:   
      <any-binary-path>: <arguments>
    result:  <string | object>      # if set the step result will be overriden (default original step result structure)
```

Original step result structure

  ```yaml
    result: 
      code: <int>
      stdout: <string>
      stderr: <string>
  ```
  
  ## Http Request Step

```yaml
- name: <string>                # the step name
  async: <bool>                 # if true, the cmd will be async (default is false)
  hidden: <bool>                # omitt the step result from the response (default is false)
  request:                      # the step type, use request to create an http step type
    post: <string>              # the http request method [get, put,post,delete] and the url
    data: <string>              # the request body, use the plugin ${{ tojson(obj)}} if you want to serialize an object to json
    headers:                    # the http request headers (key-value pairs)
      Content-Type: <string>    
    result:  <string | object>  # if set, the step result will be overriden (default original step result structure)
  ```


The step result structure inherited from the python `requests` module

```yaml
  result: 
    header: <dictionary>      # response headers
    content: <bytes[]>        # raw resonse content (use str() to make it serializable)
    text: <string>            # text resonse content 
    status_code: <int>        # response status code
    json: <function>          # convert the json response to object
    ...
```

More information here of the returned structure here: 

https://docs.python-requests.org/en/master/user/quickstart/  


## SQL Step

```yaml
    - name: <string>        
      driver: <string>            #optional driver according go the database engine (default is MSSQL)
      hidden: <bool>              # omitt the step result from the response (default is false)
      cstring: <string>           # connection string
      sql: |
        SELECT STATUS='OK', DATE=NOW()
        UNION 
        SELECT STATUS='NOT-OK', DATE=NOW()
      result:  <string | object>  # if set, the step result will be overriden (default original step result structure)
```

The step result is an array of objects based on query output 

```yaml
  result: 
      - STATUS: 'OK'
        DATE: 2021-01-01 00:00:00
      - STATUS: 'NOT-OK'
        DATE: 2021-01-02 00:00:00
```

# The Async Steps

When running async steps like in the following example, the orchestrator will not wait for the steps results to give the response.

So the object `workflow.steps[:].result` will be responded as `null`

```yaml
  ...
  steps:
    - name: Sleep 10
      async: true
      cmd:
        powershell: -NoProfile -Command "Start-Sleep 10;" 

    - name: Sleep 20
      async: true
      cmd:
        powershell: -NoProfile -Command "Start-Sleep 20" 
  ...
```

However, if a sync step is present, the async operations will be awaited and the workflow will only continue after all the steps get completed.

```yaml
  ...
  steps:
    - name: Sleep 10
      async: true
      cmd:
        powershell: -NoProfile -Command "Start-Sleep 10;" 

    - name: Sleep 20
      async: true
      cmd:
        powershell: -NoProfile -Command "Start-Sleep 20;" 
    
    - name: Wait for async steps before continue
      async: false          # optional 
      result: All finished  # optional
     
    ...

```

# Run it on docker

```powershell
docker build . -t orchestrator
```

```powershell
docker run -it -p 5000:5000 -v "$(PWD)/examples:/app/workflows"  jsoliveira/orchestrator
```
