.PHONY = all protodep generate

all: proto_update generate clean_up

proto_update:
	mkdir -p temp
	@protodep up --force

generate:
	@protoc -I ./temp --python_betterproto_out=temp  temp/com/coralogix/xdr/ingestion/v1/*

clean_up:
	@echo "Moving files to the proper places"
	@mv ./temp/com/coralogix/xdr/ingestion/v1/__init__.py ./model/__init__.py
	@rm -rf ./temp
