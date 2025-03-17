from flask import Blueprint, jsonify

actuator = Blueprint('actuator', __name__, url_prefix='/actuator')


@actuator.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'UP'}), 200
