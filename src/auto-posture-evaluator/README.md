# Auto posture evaluator

## Generating models
### Requirements
 * [protodep](https://github.com/stormcat24/protodep)
 * [python-betterproto](https://github.com/danielgtaylor/python-betterproto)

### Action
 1. Run `protodep up` to pull the required `.proto` files
 2. Go to `model` directory by `cd ./model`
 3. Run `protoc -I . --python_betterproto_out=.  com/coralogix/xdr/ingestion/v1/*`

The last command will generate the gRPC client and the models to be used. (Sadly it generates some empty `__init__.py` files, feel free to ignore/remove them)