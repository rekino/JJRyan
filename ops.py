import numpy as np
import datetime
from datetime import time
from itertools import product


def iter_slots():
    for i, j in product(range(8), range(2)):
        yield '09' if i == 0 else str(9 + i), '00' if j == 0 else '30'


def availability_column_from_iter(slot):
    return f'H{slot[0]}M{slot[1]}'


def time_from_iter(slot):
    return time(int(slot[0]), int(slot[1]))


def interval_to_vec(start: str, end: str):
    start_time = time_from_iter(start.split(':'))
    end_time = time_from_iter(end.split(':'))

    slots_time = list(map(time_from_iter, iter_slots())) + [time(17, 0)]

    vec = np.zeros(16)
    for i, (slot_start, slot_end) in enumerate(zip(slots_time[:-1], slots_time[1:])):
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
    query = f'''
            SELECT id, {','.join(columns)}
            FROM EngineerAvailability
            WHERE engineer_id = ? AND timestamp < ?
            ORDER BY timestamp ASC
            LIMIT 1
        '''

    cursor.execute(query, (engineer_id, inspection_date))
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