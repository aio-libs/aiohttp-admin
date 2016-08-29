# Some simple testing tasks (sorry, UNIX only).

FLAGS=


flake:
	pyflakes aiohttpdemo_polls
	pep8 aiohttpdemo_polls setup.py

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

run:
	python -m aiohttpdemo_polls

fake_data:
	python ./aiohttpdemo_polls/generate_data.py

docker_start_pg:
	docker-compose -f ../../docker-compose.yml up -d postgres

docker_stop_pg:
	docker-compose -f ../../docker-compose.yml stop postgres

.PHONY: flake clean
