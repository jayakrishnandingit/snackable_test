import os
import logging

from flask import Flask, jsonify, make_response

from core.logging_setup import setup_logging
setup_logging()
from api.decorators import log_latency_decorator
from api.exceptions import APIException, FileInvalidStatusError, FileNotFound
from api.jobs import GeventJobs

app = Flask(__name__)
LOGGER = logging.getLogger(__name__)


@app.route('/api/presentation/files/<file_id>')
@log_latency_decorator
def file_details_api(file_id):
    """
    REST API endpoint to serve all file and segment metadata
    when given a file_id as an input parameter. The API throws
    a 400 Bad Request if the file is not in the FINISHED status.

    The API makes use of gevent as a strategy to call the 3rd party APIs
    for concurrent execution.

    @return: JSON
    Success - 200 OK.
    ========
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

    Error - 400 Bad request, 404 Not Found.
    ======
    {"error": "The message about the error."}
    """
    strategy = GeventJobs()

    # fetch the file and details from processing API.
    LOGGER.info(f"Fetching file {file_id} from APIs.")
    try:
        the_file = strategy.fetch_file(file_id)
    except (FileInvalidStatusError, APIException) as e:
        return make_response(jsonify({'error': str(e)}), 400)
    except FileNotFound as e:
        return make_response(jsonify({'error': str(e)}), 404)

    try:
        the_file.update(strategy.fetch_file_details(file_id))
    except APIException as e:
        return make_response(jsonify({'error': str(e)}), 400)

    try:
        the_file.update({'segments': strategy.fetch_file_segments(file_id)})
    except APIException as e:
        return make_response(jsonify({'error': str(e)}), 400)

    return make_response(jsonify(the_file), 201)
