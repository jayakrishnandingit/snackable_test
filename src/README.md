## Tech stack

- Docker.
- docker-compose.
- python 3.7.
- Flask.
- gunicorn.
- gevent.

## Build API service

```
cd snackable_test

docker-compose build api
```

## Run the API

Before running the API, please take a look at the docker-compose.yml file to make sure that you have tweaked the env variables and ports. Default values should be good, but feel free to change them as per your preference.

### Environment variables

```
FLASK_ENV=development
```
FLASK_ENV is a config used by flask framework to determine debugging level. I have not tested with other values for this variable.

```
PROCESSING_API_HOST=http://interview-api.snackable.ai
```
This env variable stores the API host name to call to fetch different file details. Please note that it *does not* have a *trailing slash (/)*.

```
MAX_PAGES=200
```
Determines the maximum number of pages from the paginated API we will check before declaring file not found. 200 pages = 1000 records with 5 records per page limit.

### Run

```
docker-compose up api
```

## Running tests

I have added **flake8** package to do a basic code sanity check.

```
docker-compose run --rm api flake8 .
```

I have written **unittests** to make sure that the presentation API functions as expected under different scenarios. You can run the tests as below,

```
docker-compose run --rm api python -m unittest
```

Moreover, I have added **GitHub workflow actions** to run these tests whenever a new change is pushed to `main` branch and/or when a Pull Request is raised against it.