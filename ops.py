import numpy as np
from datetime import datetime, time
from itertools import product
from collections import defaultdict


week_days = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6
}


def count_specific_day_of_week(start_date, end_date, target_day):
    total_days = (end_date - start_date).days
    num_occurrences = total_days // 7

    target_day_index = (target_day - 1) % 7

    if start_date.weekday() == target_day_index:
        num_occurrences += 1

    return num_occurrences


def iter_slots():
    for i, j in product(range(8), range(2)):
        yield '09' if i == 0 else str(9 + i), '00' if j == 0 else '30'


def availability_column_from_iter(slot):
    return f'H{slot[0]}M{slot[1]}'


def time_from_iter(slot):
    return time(int(slot[0]), int(slot[1]))


def get_day_of_week(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = date_obj.strftime('%A')

        return day_of_week

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."


def interval_to_vec(start: str, end: str):
    start_time = time_from_iter(start.split(':'))
    end_time = time_from_iter(end.split(':'))

    slots_time = list(map(time_from_iter, iter_slots())) + [time(17, 0)]

    vec = np.zeros(16)
    for i, (slot_start, slot_end) in enumerate(
        zip(slots_time[:-1], slots_time[1:])
        ):
        if start_time <= slot_end and slot_start <= end_time:
            vec[i] = 1
    return vec


def get_bookings(cursor, engineer_id, inspection_date):
    query = '''
            SELECT *
            FROM BookedInspectionView
            WHERE engineer_id = ? AND inspection_date = ?
        '''

    cursor.execute(query, (engineer_id, inspection_date))

    return cursor.fetchall()


def get_availability(cursor, engineer_id, inspection_date):
    columns = list(map(availability_column_from_iter, iter_slots()))
    inspection_day = get_day_of_week(inspection_date)
    query = f'''
            SELECT id, {','.join(columns)}
            FROM EngineerAvailability
            WHERE engineer_id = ? AND day_of_week = ? AND timestamp < ?
            ORDER BY timestamp ASC
            LIMIT 1
        '''

    cursor.execute(query, (engineer_id, inspection_day, inspection_date))
    engineer_row = cursor.fetchone()

    if engineer_row is None:
        return -1, np.zeros(16)

    engineer_row_id = engineer_row[0]
    engineer_vec = np.array(engineer_row[1:])

    booked_vec = np.zeros(16)
    for row in get_bookings(cursor, engineer_id, inspection_date):
        inspection_vec = interval_to_vec(
            row['booked_start_time'], row['booked_end_time']
        )
        booked_vec += inspection_vec

    return engineer_row_id, engineer_vec - booked_vec


def get_inspections(cursor, from_date, to_date):
    query = '''SELECT * from BookedInspectionView
            WHERE inspection_date BETWEEN ? and ?
            '''
    cursor.execute(query, (from_date, to_date))
    return cursor.fetchall()


def count_availability(cursor, engineer_id, from_date, to_date):
    from_obj = datetime.strptime(from_date, '%Y-%m-%d')
    to_obj = datetime.strptime(to_date, '%Y-%m-%d')

    query = '''
            SELECT *
            FROM EngineerAvailability
            WHERE engineer_id = ? AND timestamp < ?
            GROUP BY day_of_week
            ORDER BY timestamp
        '''
    cursor.execute(query, (engineer_id, from_date))
    availability = cursor.fetchall()

    total = defaultdict(lambda: 0)
    perv_availability = defaultdict(lambda: 0)
    for row in availability:
        count = count_specific_day_of_week(from_obj, to_obj, week_days[row[2]])
        slots_available = np.array(row[3:19]).sum()
        total[row[2]] = slots_available * count
        perv_availability[row[2]] = slots_available

    query = '''
            SELECT *
            FROM EngineerAvailability
            WHERE engineer_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
    cursor.execute(query, (engineer_id, from_date, to_date))
    availability = cursor.fetchall()

    for row in availability:
        date_obj = datetime.strptime(row[19], '%Y-%m-%d %H:%M:%S')
        count = count_specific_day_of_week(date_obj, to_obj, week_days[row[2]])
        slots_available = np.array(row[3:19]).sum()
        total[row[2]] += (slots_available - perv_availability[row[2]]) * count
        perv_availability[row[2]] = slots_available

    return total


def count_billable(cursor, engineer_id, from_date, to_date):
    query = '''
            SELECT *
            FROM BookedInspectionView
            WHERE engineer_id = ? AND inspection_date BETWEEN ? AND ?
        '''
    cursor.execute(query, (engineer_id, from_date, to_date))
    inspections = cursor.fetchall()

    total = 0
    for row in inspections:
        total += interval_to_vec(row[4], row[5]).sum()

    return total


def get_utilization(cursor, engineer_id, from_date, to_date):
    availability = count_availability(cursor, engineer_id, from_date, to_date)
    availability = sum(availability.values())
    billable = count_billable(cursor, engineer_id, from_date, to_date)

    return billable / availability


if __name__ == '__main__':
    import sqlite3

    db_name = './db/inspection_booking.db'

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        print(get_utilization(cursor, 'E123', '2023-04-20', '2025-04-29'))
