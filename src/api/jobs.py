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
            LOGGER.info(f"File {self.file_id} found at page {self.offset + 1} with status {self.status(the_file[0])}.")
            return the_file[0]

    def filter_by_id(self, file_list):
        return list(filter(lambda r: r.get('fileId') == self.file_id, file_list))

    def status(self, the_file):
        return the_file.get('processingStatus')


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


class FetchFileSegmentsJob(object):
    """
    A gevent green thread job to get a file segments from API.
    """
    def __init__(self, file_id, api, timeout=5):
        self.file_id = file_id
        self.api = api
        self.timeout = timeout

    def __call__(self):
        import gevent

        with gevent.Timeout(self.timeout):
            return self.api.fetch_segments(self.file_id)


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

    def success_filter(self, job):
        return job.successful()

    def is_finished_filter(self, job):
        return self.success_filter(job) and job.value is not None and self.is_finished(job.value)

    def get_data(self, jobs, filter_fn=None):
        """
        Return the data of successfully run jobs.
        """
        if not filter_fn:
            filter_fn = self.success_filter

        values = [j.value for j in filter(filter_fn, jobs)]
        return values

    def fetch_file(self, file_id, limit=5, timeout=5, max_pages=MAX_PAGES):
        """
        Fetch a file status via a paginated API. We limit the calls to MAX_PAGES pages.
        The method will spawn a gevent green thread for each API call.
        """
        # local import to avoid installing this package if we are employing another strategy.
        import gevent

        jobs = [gevent.spawn(FetchFilesJob(file_id, self._api, limit, offset, timeout)) for offset in range(0, max_pages + 1)]
        gevent.joinall(jobs)

        if self.is_all_error(jobs):
            raise APIException("Could not reach API at the moment.")
        if self.is_file_not_found(jobs):
            raise FileNotFound(f"File {file_id} not found in {max_pages} pages.")

        # I see multiple pages return same file data.
        finished_files = self.get_data(jobs, filter_fn=self.is_finished_filter)
        if len(finished_files) == 0:
            raise FileInvalidStatusError(f"File {file_id} is not in {FileStatus.FINISHED} status.")
        return finished_files[0]

    def fetch_file_details(self, file_id, timeout=5):
        """
        Fetch metadata of a file from an API.
        The method will spawn a gevent green thread for the API call.
        """
        import gevent

        job = gevent.spawn(FetchFileDetailsJob(file_id, self._api, timeout))
        gevent.joinall([job])
        if self.is_all_error([job]):
            raise APIException("Could not reach processing API at all.")
        return self.get_data([job])[0]

    def fetch_file_segments(self, file_id, timeout=5):
        """
        Fetch extracted audio segment details of a file from an API.
        The method will spawn a gevent green thread for the API call.
        """
        import gevent

        job = gevent.spawn(FetchFileSegmentsJob(file_id, self._api, timeout))
        gevent.joinall([job])
        if self.is_all_error([job]):
            raise APIException("Could not reach processing API at all.")
        return self.get_data([job])[0]
