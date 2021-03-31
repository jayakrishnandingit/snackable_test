venv:
	python3 -m venv ./ENV;\
	. ENV/bin/activate;\
	pip install --upgrade pip;

pip:
	. ENV/bin/activate;\
	cd ./src;\
	pip install -r api/requirements.txt;

run-api:
	. ENV/bin/activate;\
	cd ./src;\
	gunicorn -k gevent -w 2 api.app:app -b 0.0.0.0:9002 -t 300;
