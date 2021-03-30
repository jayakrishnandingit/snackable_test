import os
import logging
import unittest
from unittest.mock import patch

from core.logging_setup import setup_logging
setup_logging()
from api.app import app
from api.exceptions import APIException

LOGGER = logging.getLogger(__name__)
DB_CONNECTION_STRING = os.environ.get('DB_CONNECTION_STRING')
FILES = [
    {
        "fileId": "08448513-b980-4267-abeb-2445b4069a0c",
        "processingStatus": "FINISHED"
    },
    {
        "fileId": "11753d4c-f1cd-4696-a6f9-ac1d41929322",
        "processingStatus": "FINISHED"
    },
    {
        "fileId": "33e6c735-21bc-422b-a0dc-12a1a4e479bd",
        "processingStatus": "FAILED"
    },
    {
        "fileId": "3cd97393-b441-4d7c-a58f-ec40fa2fee50",
        "processingStatus": "PROCESSING"
    },
    {
        "fileId": "4a551eec-7dac-46d2-8f17-b6972b864b34",
        "processingStatus": "FINISHED"
    }
]

FILE_DETAILS = {
    "4a551eec-7dac-46d2-8f17-b6972b864b34": {
        "fileName": "1a4bae87-1eec-46de-9efb-657be6eaa8fa",
        "fileLength": 2870700,
        "mp3Path": "https://s3.amazonaws.com/snackable-test-audio/mp3Audio/1a4bae87-1eec-46de-9efb-657be6eaa8fa_constant_bitrate.mp3",
        "originalFilePath": "https://s3.amazonaws.com/snackable-test-crawler-audio/1a4bae87-1eec-46de-9efb-657be6eaa8fa.mp3",
        "seriesTitle": "Royally Obsessed"
    }
}

SEGMENTS = {
    "4a551eec-7dac-46d2-8f17-b6972b864b34": [
        {
            "fileSegmentId": 1342,
            "fileId": "4a551eec-7dac-46d2-8f17-b6972b864b34",
            "segmentText": "Hey please rise for their majesties of royalty obsessed the podcast for all things modern. Welcome back to royalty obsessed.",
            "startTime": 1730,
            "endTime": 16080
        }
    ]
}


class FileDetailsAPITestCase(unittest.TestCase):
    @patch('api.jobs.ProcessingAPIAdapter')
    def test_processing_file_is_bad_request(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/3cd97393-b441-4d7c-a58f-ec40fa2fee50')
            self.assertEqual(rv.status_code, 400)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_failed_file_is_bad_request(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/33e6c735-21bc-422b-a0dc-12a1a4e479bd')
            self.assertEqual(rv.status_code, 400)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_invalid_file_id_is_not_found(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/abcd1234')
            self.assertEqual(rv.status_code, 404)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_external_paginated_api_error_is_bad_request(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.side_effect = APIException
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/4a551eec-7dac-46d2-8f17-b6972b864b34')
            self.assertEqual(rv.status_code, 400)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_external_metadata_api_error_is_bad_request(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        mock_instance.fetch_details.side_effect = APIException
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/4a551eec-7dac-46d2-8f17-b6972b864b34')
            self.assertEqual(rv.status_code, 400)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_external_segements_api_error_is_bad_request(self, MockAPIClass):
        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        mock_instance.fetch_details.return_value = FILE_DETAILS['4a551eec-7dac-46d2-8f17-b6972b864b34']
        mock_instance.fetch_segments.side_effect = APIException
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/4a551eec-7dac-46d2-8f17-b6972b864b34')
            self.assertEqual(rv.status_code, 400)

    @patch('api.jobs.ProcessingAPIAdapter')
    def test_external_api_timeout_is_bad_request(self, MockAPIClass):
        import gevent

        mock_instance = MockAPIClass.return_value
        mock_instance.fetch_all.return_value = FILES
        mock_instance.fetch_details.side_effect = gevent.Timeout
        with app.test_client() as c:
            rv = c.get('/api/presentation/files/4a551eec-7dac-46d2-8f17-b6972b864b34')
            self.assertEqual(rv.status_code, 400)
