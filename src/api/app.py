import os
import logging

import requests
from flask import Flask, request, jsonify, make_response

from core.logging_setup import setup_logging
setup_logging()
from api.decorators import log_latency_decorator

app = Flask(__name__)
LOGGER = logging.getLogger(__name__)
MAX_PAGES = int(os.environ.get('MAX_PAGES', 200))
PROCESSING_API_HOST = os.environ.get('PROCESSING_API_HOST')


class FileStatus(object):
    PROCESSING = 'PROCESSING'
    FINISHED = 'FINISHED'
    FAILED = 'FAILED'


class APIException(Exception):
    pass


class FileInvalidStatusError(Exception):
    pass


class FileNotFound(Exception):
    pass


class ProcessingAPIAdapter(object):
    def __init__(self):
        self._host = PROCESSING_API_HOST

    def _regulate_headers(self, headers=None):
        if not headers:
            headers = {}
        return headers

    def _get_api_url(self, url):
        return self._host + url

    def _respond_or_raise(self, response, raise_exec=True):
        """
        Method to add more logging on error.
        """
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            http_method = response.request.method if response.request is not None else 'UNKNOWN'
            request_headers = response.request.headers if response.request is not None else ''
            LOGGER.error(
                (
                    f"Exception occurred while calling {http_method} of processing API {response.url}. "
                    f"\nResponse Status Code: {response.status_code}"
                    f"\nRequest Headers: {request_headers}. "
                    f"\nResponse Content: {response.content} "
                    f"\nException: {e}."
                )
            )
            if raise_exec:
                raise e
        return response

    def _get(self, relative_url, headers=None, params=None, raise_on_error=True):
        """
        A wrapper method to GET results from an API.
        """
        if not params:
            params = {}

        if not self._host:
            raise APIException("Cannot call API. _host configuration is missing.")

        headers = self._regulate_headers(headers)
        api_url = self._get_api_url(relative_url)
        LOGGER.info("Calling processing API %s with headers %s and params %s.", api_url, headers, params)
        # gevent would monkey patch requests lib to be async.
        response = requests.get(api_url, headers=headers, params=params, verify=False)
        return self._respond_or_raise(response, raise_exec=raise_on_error)

    def fetch_all(self, limit=5, offset=0):
        relative_url = '/api/file/all'
        return self._get(relative_url, params={'limit': limit, 'offset':offset}).json()


def is_finished(the_file):
    return the_file.get('processingStatus') == FileStatus.FINISHED


def has_invalid_status_jobs(jobs):
    values = [j.value for j in filter(lambda x: x.successful(), jobs)]
    return len([v for v in values if v == -1]) > 0


def all_error_jobs(jobs):
    errors = [0 for j in filter(lambda x: not x.successful(), jobs)]
    return len(errors) == len(jobs)


def file_not_found(jobs):
    values = [False for j in filter(lambda x: x.successful(), jobs) if not j.value]
    errors = [False for j in filter(lambda x: not x.successful(), jobs)]
    return len(values + errors) == len(jobs)


class GeventStrategy(object):
    def __init__(self, processing_api=None):
        if not processing_api:
            self._api = ProcessingAPIAdapter()
        else:
            self._api = processing_api

    def fetch_file_status(self, file_id, limit=5, timeout=5, max_pages=MAX_PAGES):
        """
        Fetch a file status via a paginated API. We limit the calls to MAX_PAGES pages.
        The method will spawn a gevent green thread for each API call.
        1. Return file finished status, if file found with finished status in any of the pages.
        2. Raise exception if,
            1.1 file not found in all the pages.
            1.2 file in an unfinished status.
            1.3 the API could not be reached at all.
        """
        # local import to avoid installing this package if we are employing another strategy.
        import gevent
        def _job(api, offset):
            """
            A gevent green thread job to call paginated processing API for each page.
            """
            with gevent.Timeout(timeout):
                file_list = api.fetch_all(limit, offset)
                the_file = list(filter(lambda r: r.get('fileId') == file_id, file_list))
                if len(the_file) == 0:
                    return 0  # file not found in this page.
                the_file = the_file[0]
                if not is_finished(the_file):
                    return -1  # file found with wrong status.
                return 1  # file finished.

        jobs = [gevent.spawn(_job, self._api, offset) for offset in range(0, max_pages + 1)]
        gevent.joinall(jobs)
        if all_error_jobs(jobs):
            raise APIException(f"Could not reach processing API at all.")
        if has_invalid_status_jobs(jobs):
            raise FileInvalidStatusError(f"File {file_id} in status {the_file.get('processingStatus')}.")
        if file_not_found(jobs):
            raise FileNotFound(f"File {file_id} not found in {max_pages} pages.")
        return FileStatus.FINISHED

@app.route('/api/presentation/files/<file_id>')
@log_latency_decorator
def file_details_api(file_id):
    LOGGER.info(f"File id is {file_id}. Type is {type(file_id)}.")
    strategy = GeventStrategy()
    try:
        status = strategy.fetch_file_status(file_id)
    except (FileInvalidStatusError, APIException) as e:
        return make_response(str(e), 400)
    except FileNotFound as e:
        return make_response(str(e), 404)
    return make_response(status, 200)
