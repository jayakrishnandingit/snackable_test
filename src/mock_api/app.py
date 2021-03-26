import logging
from flask import Flask, request, jsonify

from core.logging_setup import setup_logging
setup_logging()
app = Flask(__name__)
LOGGER = logging.getLogger(__name__)
FILES = [
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "processingStatus": "FINISHED",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "FAILED",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "FAILED",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "PROCESSING",
    },
    {
        "fileId": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff",
        "processingStatus": "FAILED",
    }
]

@app.route('/api/file/all')
def all():
    try:
        limit = int(request.args.get('limit', 5))
    except (TypeError, ValueError) as e:
        limit = 5
    try:
        offset = int(request.args.get('offset', 0))
    except (TypeError, ValueError) as e:
        offset = 0
    return jsonify(FILES[offset*limit:(offset + 1)*limit])
