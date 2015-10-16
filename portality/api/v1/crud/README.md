# CRUD API

## Applications

### Create an Application

Send:

    POST /applications?api_key=<api_key>
    Content-Type: application/json
    
    [Incoming Application]

On Error:

    HTTP 1.1  400 Bad Request
    Content-Type: application/json
    
    {
        "error" : "<human readable error message>"
    }

On Success:

    HTTP 1.1  201 Created
    Content-Type: application/json
    Location: <url for api endpoint for created application>
    
    {
        "status" : "created",
        "id" : "<unique identifier for the application>",
        "location" : "<url for api endpoint for newly created application>"
    }

### Retrieve an Application

Send:

    GET /application/<application_id>?api_key=<api_key>

On Success:

    HTTP 1.1  200 OK
    Content-Type: application/json
    
    [Outgoing Application]


### Update an Application

Send:

    PUT /application/<application_id>?api_key=<api_key>
    Content-Type: application/json
    
    [Incoming Application]

On Error:

    HTTP 1.1  400 Bad Request
    Content-Type: application/json
    
    {
        "error" : "<human readable error message>"
    }

On Success:

    HTTP 1.1  204 No Content

### Delete an Application

Send:

    DELETE /application/<application_id>?api_key=<api_key>

On Success:

    HTTP 1.1  204 No Content

### Incoming Application Model


### Outgoing Application Model
