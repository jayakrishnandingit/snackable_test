## Tech stack

- Docker.
- docker-compose.
- python 3.7.
- Flask.
- gunicorn.
- gevent.

## Summary

Completed building a single API that serves all file and segment metadata when given a “fileId” as an input parameter. Furthermore, I have implemented a storage mechanism using MongoDB to store FINISHED files once fetched from APIs. Therefore, subsequent requests for same files will be served from local MongoDB rather than APIs thus reducing HTTP overhead.

## Design

### Gevent

Inorder to reduce the API call overhead, I have implemented the API using *gevent* asynchronous jobs. Gevent allows to spawn I/O jobs on a single thread using I/O loops and green threads. This is almost similar to how the NodeJS event loop works.

Moreover, gevent applies monkey patching to most of the sync libraries so that they behave asynchronously without the need for us to tweak the code. An excellent example, is the *requests* library which makes use of the *urllib* library under the hood which when used in conjunction with gevent is monkey patched to be asynchronous.

### API design

I have designed the API in below stages.
1. Try to retrieve from local storage.
1. If not in local storage, try to fetch the file from paginated endpoint by looking for first 200 pages (configured as MAX_PAGES env variable) ~ 1000 records asynchronously.
2. Once the file is fetched, I try to fetch the metadata using /api/file/details/{snackableFileId} API asynchronously.
3. Then, I try to asynchronously fetch the segments from /api/file/segments/{snackableFileId} API.
4. Finally, the data captured from the 3 APIs are merged to form a single JSON object. This JSON is then stored in DB for posterity and returned to user.

Example response,

```
{
    "fileId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "processingStatus": "FINISHED",
    "fileName": "FILE_NAME",
    "mp3Path": "http://s3.amazonaws.com/snackable-test-audio/mp3Audio/audioFileName.mp3",
    "originalFilepath":
    "http://s3.amazonaws.com/snackable-test-audio/originalFile/audioFileName.mp3",
    "seriesTitle": "Series Title",
    "segments": [
        {
            "fileSegmentId": 2685,
            "fileId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "segmentText": "Full segment text",
            "startTime": 3710,
            "endTime": 4400
        },
        ..
    ]
}
```

In addition to that, if unable to find the file or the file is not in FINISHED status then the API raises a *404 Not Found* or *400 Bad Request* error respectively.

### MongoDB

Initially I thought about using Redis, but then I chose MongoDB because the composed data of a file can be a bit larger and complex. I am not sure if redis can store such data in one key-value pair. Default document size in MongoDB is 16MB.

Moreover, if we plan to serve more queries in future it is better we opt for a DB rather than a key-value store.

MongoDB uses WiredTiger as its storage engine which as far as I read does a pretty good job in low latency query execution.

### Dilemma

Then there is the question, What can be the maximum number of records I may have to check to find a file from the paginated API? I would say the answer to this question probably is, design change!

### Alternative design suggestion

The organic way of doing this will be for the file processing service to push a message when it completes processing a file. Then we can consume that message and store in DB for faster response to the user. This will require an async message queue system like RabbitMQ.

I am open to suggestions. Let us discuss.

## Build API service

```
cd snackable_test

docker-compose build api
```

## Run the API

Before running the API, please modify the DB credentials in `variables.env` file. You can create this file by copying from `sample.env` file for defaults. Credentials in sample.env are dummy and need not work.

```
docker-compose up api

curl http://localhost:9002/api/presentation/files/{snackableFileId}
```

I am using curl as an example, you can try in browser, Postman.

## Environment variables

Copy the sample env file to `variables.env` file and make changes as required.
```
cp sample.env variables.env
```
Variables to look for are,

```
DB_CONNECTION_STRING=mongodb://<username>:<password>@db:27017/snackable?authSource=admin
MONGO_INITDB_ROOT_USERNAME=<username>
MONGO_INITDB_ROOT_PASSWORD=<password>
```
Change this to your preference. This is used to login to mongoDB service. Refer `docker-compose.yml` file to understand the mongo service.

```
PROCESSING_API_HOST=http://interview-api.snackable.ai
```
This env variable stores the API host name to call to fetch different file details. Please note that it *does not* have a *trailing slash (/)*.

```
MAX_PAGES=200
```
Determines the maximum number of pages from the paginated API we will check before declaring file not found. 200 pages = 1000 records with 5 records per page limit.

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