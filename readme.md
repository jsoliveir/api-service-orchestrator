# What is this repository

This repository is a simple API orchestrator written in python.

The orchestrator is configured thru yaml files and each configuration is called a workflow.

A Workflow is triggered thru an HTTP request to a given/configured `path` and the results captured by each step will be returned to the requester.

# How it works

## 1) The Workflow configuration

The configuration allows to write python code within curly braces `${{ ... }}`

You can access all properties defined in the workflow thru the ${{ workflow }} property.

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

If you need to make data transformations there is some available functions like `fromjson`, `tojson` or `fromxml`,`toxml` that can be invoked thry the curly braces
eg.: `${{ toxml(workflow) }}` 

Check the list of available functions down below


## Documentation

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
        /bin/python: <arguments>

    # STEP TYPE REQUEST
    - name: Weather
      async: true                    # if true, the cmd will be async (default is false)
      hidden: true                   # if true, the step result will be omitted from the response  (default is false)
      request:                       # the step type, use request to create an http step type
        post: <url>                  # the http request method [get, put,post,delete]
        data: <raw-data>             # some data use ${{ tojson()}} if you want to serialize an object
        headers:                     # the http request headers (key-value pairs)
            KEY: VALUE            

    # STEP TYPE GENERIC
    - name: Output                   # if the step type is not provided, it can be just like a simple wrapper (useful for data transformation)
      hidden: true                   # if true, the step result will be omitted from the response  (default is false)
      result:                         
        - ${{ workflow.steps[0].result.stdout }}
        - ${{ workflow.steps[1].result.content }}

    - name: Output2                  
      result:                         
        - ${{ workflow.steps[3].result[0] }}
```

## 2) Invoking the workflow request

Once the configuration is done a web server will be listening for incoming requests to `workflow.http.path` then the steps specified in the workflow will be run sequentially and the overall results will be returned to the requester.

![](docs/result.jpg)


# Avalable functions in the ${{ }} context

### *variables*

* `workflow` :  the current workflow configuration parsed as object

* `env` :  environment variables

* `http` :  the http request object 

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


### *functions*

* `serializable()` :      converts an object to dictionary to be serializable

* `fromjson()` :          deserializes a json string to object

* `tojson()`:             serializes an object to json 

* `fromxml()` :           serializes an object to xml 

* `toxml()`               deserializes a xml string to object

* `object()`            converts a dictionary to object

