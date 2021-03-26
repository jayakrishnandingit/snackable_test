## Tech stack

- Docker.
- docker-compose.
- python 3.7.
- Flask.
- gunicorn.
- gevent.

## Summary

I could only complete the very first assignment of building a single API that serves all file and segment metadata when given a “fileId” as an
input parameter.

## Design

Inorder to reduce the API call overhead, I have implemented the API using *gevent* concurrency. Gevent allows to spawn I/O jobs on a single thread using I/O loops and green threads. This is almost similar to how the Javascript event loop works.

Moreover, gevent applies monkey patching to most of the sync libraries so that they behave asynchronously without the need for us to tweak the code. An excellent example, is the *requests* library which makes use of the *urllib* library under the hood which when used in conjunction with gevent is monkey patched to be asynchronous.

Talking about the API implementation, I have designed the API in 3 stages.
1. It tries to fetch the file from paginated endpoint by looking for first 200 pages (configured as MAX_PAGES env variable) ~ 1000 records.
2. Once the file is fetched, I try to fetch the metadata using /api/file/details/{snackableFileId} API.
3. At last, I try to fetch the segments from /api/file/segments/{snackableFileId} API.

Furthermore, if unable to find the file or the file is not in FINISHED status then the API raises a *404 Not Found* or *400 Bad Request* error respectively.

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