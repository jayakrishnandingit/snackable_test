import os
import logging

import requests

from api.exceptions import APIException

LOGGER = logging.getLogger(__name__)
PROCESSING_API_HOST = os.environ.get('PROCESSING_API_HOST')


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
        return self._get(relative_url, params={'limit': limit, 'offset': offset}).json()

    def fetch_details(self, file_id):
        relative_url = f'/api/file/details/{file_id}'
        return self._get(relative_url).json()
