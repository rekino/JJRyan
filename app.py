from flask import Flask, request, jsonify
import sqlite3

import ops

db_name = './db/inspection_booking.db'

app = Flask(__name__)

@app.route('/booking', methods=['GET'])
def get_bookings():
    engineer_id = request.args.get('engineer_id')
    inspection_date = request.args.get('inspection_date')

    if engineer_id is None:
        return 'Please provide the ID of the engineer.', 402
    if engineer_id is None:
        return 'Please provide a date for inspections.', 402

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        res = ops.get_bookings(cursor, engineer_id, inspection_date)

    return jsonify(res), 200


@app.route('/inspections', methods=['GET'])
def get_inspections():
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if from_date is None:
        return 'Please provide the start of the interval.', 402
    if to_date is None:
        return 'Please provide the end of the interval.', 402

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        res = ops.get_inspections(cursor, from_date, to_date)

    return jsonify(res), 200


@app.route('/availability', methods=['GET'])
def get_availability():
    engineer_id = request.args.get('engineer_id')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if engineer_id is None:
        return 'Please provide the engineer ID.', 402
    if from_date is None:
        return 'Please provide the start of the interval.', 402
    if to_date is None:
        return 'Please provide the end of the interval.', 402

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        res = ops.count_availability(cursor, from_date, to_date)

    return jsonify(res), 200


@app.route('/billable', methods=['GET'])
def get_billable():
    engineer_id = request.args.get('engineer_id')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if engineer_id is None:
        return 'Please provide the engineer ID.', 402
    if from_date is None:
        return 'Please provide the start of the interval.', 402
    if to_date is None:
        return 'Please provide the end of the interval.', 402

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        res = ops.count_billable(cursor, from_date, to_date)

    return jsonify(res), 200


@app.route('/utilization', methods=['GET'])
def get_utilization():
    engineer_id = request.args.get('engineer_id')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if engineer_id is None:
        return 'Please provide the engineer ID.', 402
    if from_date is None:
        return 'Please provide the start of the interval.', 402
    if to_date is None:
        return 'Please provide the end of the interval.', 402

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        res = ops.get_utilization(cursor, engineer_id, from_date, to_date)

    return jsonify(res), 200


if __name__ == '__main__':
    app.run(debug=True)
