import os
import logging

from api.external_api import ProcessingAPIAdapter
from api.exceptions import APIException, FileNotFound, FileInvalidStatusError
from api.utils import FileStatus

LOGGER = logging.getLogger(__name__)
MAX_PAGES = int(os.environ.get('MAX_PAGES', 200))


class FetchFilesJob(object):
    """
    A gevent green thread job to call paginated processing API for each page.
    """
    def __init__(self, file_id, api, limit=5, offset=0, timeout=5):
        self.file_id = file_id
        self.api = api
        self.limit = limit
        self.offset = offset
        self.timeout = timeout

    def __call__(self):
        import gevent

        with gevent.Timeout(self.timeout):
            file_list = self.api.fetch_all(self.limit, self.offset)
            the_file = self.filter_by_id(file_list)
            if len(the_file) == 0:
                return None
            LOGGER.info(f"File {self.file_id} found at page {self.offset + 1}.")
            return the_file[0]

    def filter_by_id(self, file_list):
        return list(filter(lambda r: r.get('fileId') == self.file_id, file_list))


class FetchFileDetailsJob(object):
    """
    A gevent green thread job to get a file details from API.
    """
    def __init__(self, file_id, api, timeout=5):
        self.file_id = file_id
        self.api = api
        self.timeout = timeout

    def __call__(self):
        import gevent

        with gevent.Timeout(self.timeout):
            return self.api.fetch_details(self.file_id)


class GeventJobs(object):
    def __init__(self, processing_api=None):
        if not processing_api:
            self._api = ProcessingAPIAdapter()
        else:
            self._api = processing_api

    def is_finished(self, the_file):
        return the_file.get('processingStatus') == FileStatus.FINISHED

    def is_all_error(self, jobs):
        """
        All jobs raised exception. Either timeout or requests exceptions.
        """
        errors = [j.exception for j in filter(lambda x: not x.successful(), jobs)]
        return len(errors) == len(jobs)

    def is_file_not_found(self, jobs):
        """
        Some jobs raised exception and others returned None (i.e, file not found in the page).
        """
        values = [None for j in filter(lambda x: x.successful() and x.value is None, jobs)]
        errors = [None for j in filter(lambda x: not x.successful(), jobs)]
        return len(values + errors) == len(jobs)

    def get_file(self, jobs):
        values = [j.value for j in filter(lambda x: x.successful() and x.value is not None, jobs)]
        return values[0]

    def fetch_file(self, file_id, limit=5, timeout=5, max_pages=MAX_PAGES):
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

        jobs = [gevent.spawn(FetchFilesJob(file_id, self._api, limit, offset, timeout)) for offset in range(0, max_pages + 1)]
        gevent.joinall(jobs)
        if self.is_all_error(jobs):
            raise APIException("Could not reach API at the moment.")
        if self.is_file_not_found(jobs):
            raise FileNotFound(f"File {file_id} not found in {max_pages} pages.")
        the_file = self.get_file(jobs)
        if not self.is_finished(the_file):
            raise FileInvalidStatusError(f"File {file_id} is not in {FileStatus.FINISHED} status.")
        return the_file

    def fetch_file_details(self, file_id, timeout=5):
        import gevent

        job = gevent.spawn(FetchFileDetailsJob(file_id, self._api, timeout))
        gevent.join(job)
        if self.is_all_error([job]):
            raise APIException("Could not reach processing API at all.")
        return job.value
