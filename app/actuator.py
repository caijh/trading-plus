from flask import jsonify

from main import actuator


@actuator.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'UP'}), 200
