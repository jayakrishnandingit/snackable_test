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
    strategy = GeventJobs()

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
    return make_response(jsonify(the_file), 200)
