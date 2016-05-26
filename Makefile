# Some simple testing tasks (sorry, UNIX only).

FLAGS=


flake:
	flake8 aiohttp_admin tests demos setup.py

test: flake
	py.test -s $(FLAGS) ./tests/

vtest:
	py.test -s -v $(FLAGS) ./tests/

cov cover coverage: flake
	py.test -s -v  --cov-report term --cov-report html --cov aiohttp_admin ./tests
	@echo "open file://`pwd`/htmlcov/index.html"

ci: flake
	py.test --dp -s -v  --cov-report term --cov aiohttp_admin ./tests

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf htmlcov
	rm -rf dist

docker_clean:
	-@docker rmi $$(docker images -q --filter "dangling=true")
	-@docker rm $$(docker ps -q -f status=exited)
	-@docker volume ls -qf dangling=true | xargs -r docker volume rm

docker_start_pg:
	docker-compose -f docker-compose.yml up -d postgres

docker_stop_pg:
	docker-compose -f docker-compose.yml stop postgres

doc:
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"

.PHONY: all flake test vtest cov clean doc ci
