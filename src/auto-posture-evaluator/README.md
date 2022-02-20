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


## POT

### Test requirements

Each test has to extend from the `poc.TesterInterface` which implements the following 3 method:

    def declare_tested_service(self) -> str:

    def declare_tested_provider(self) -> str:

    def run_tests(self) -> List["TestReport"]:

Take into account that `TestReport` fields are mandatory for successful reporting