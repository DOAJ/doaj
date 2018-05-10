# API Developer Documentation

## Creating API Model objects from Core Model Objects

API Model objects are created by loading the related Core model object
and passing them to an API-specific model object with the appropriate 
public Struct, with "silent_prune" turned on, so any Core model object
data is removed prior to exposure.

For example:

* Load the Suggestion model from the database (e.g. by ID).  This contains things like
notes, other admin data, workflow information, etc.  We don't want to expose that.

* Extract the "data" property (the raw python data structure which backs the Suggestion)

* Pass the data into the OutgoingApplication model.  In this case, prior to constructing
the model object, a data crosswalk from the new archiving_policy data structure to the old
one supported by the API is done on the data.  Then the data is validated against a Struct
with silent_prune turned on:

```python
class OutgoingApplication(OutgoingCommonJournalApplication):
    def __init__(self, raw=None):
        self._add_struct(BASE_APPLICATION_STRUCT)
        super(OutgoingApplication, self).__init__(raw, construct_silent_prune=True, expose_data=True)
```

* silent_prune removes all data that is not specified in the BASE_APPLICATION_STRUCT, leaving behind
a clean object for exposure via the API.

## Modifying API Model Objects

1. Modify the appropriate Struct for your model object.  e.g. BASE_APPLICATION_STRUCT for your
Application model.

2. If your new model properties are already part of the Core model, then you are done.

3. If your new model properties are not part of the Core model, add a data conversion into the
appropriate "from_model" method on the API model.

## How Swagger docs are generated from Structs

Each API endpoint provides an additional function where swagger documentation is retrieved.  For example
"retrieve" on an object type has also "retrieve_swag".

Each model object extends from the SwaggerSupport object, so that it can provide documentation about its
structure to the documentation front-end.

So, for each model type, it is possible to generate the swagger documentation thus (using IncomingApplication 
as an example):

```python
IncomingApplication().struct_to_swag(schema_title='Application schema')
```

This code can be included in the "retrieve_swag" function to add the structure of the object to the documentation
using JSON-schema.  For example:

```python
template = deepcopy(cls.SWAG_TEMPLATE)
template['responses']['200'] = cls.R200
template['responses']['200']['schema'] = IncomingApplication().struct_to_swag(schema_title='Application schema')
```

Additionally, the Swagger spec can be pre-generated if that's more appropriate, and the JSON served from disk. 
`retrieve_swag` in this example could do something like:

```python
return json.loads(util.load_file(os.path.join(app.config['BASE_FILE_PATH'], 'api', 'v1', 'crud_api_application_retrieve_swag.json')))
```