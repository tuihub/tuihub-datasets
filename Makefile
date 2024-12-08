BUILD_NUMBER?=0

.PHONY: init
# init
init:
	pip install -r requirements.txt

build-pages: init
	echo "{ \"buildNumber\": \"${BUILD_NUMBER}\" }" > docs/build.json
	cp README.md docs/README.md
	cd src/build_docs && python main.py

.PHONY: check
# check
check:
	ruff check

.PHONY: format
# format
format:
	ruff format

# show help
help:
	@echo ''
	@echo 'Usage:'
	@echo ' make [target]'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
	helpMessage = match(lastLine, /^# (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 2, RLENGTH); \
			printf "\033[36m%-22s\033[0m %s\n", helpCommand,helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help