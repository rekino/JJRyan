import sqlite3
import json
import os

import ops


def create_sqlite_database(filename):
    try:
        conn = sqlite3.connect(filename)
        print(f"SQLite version: {sqlite3.sqlite_version}")
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def create_tables(filename):
    sql_statements = [
        """
        CREATE TABLE IF NOT EXISTS EngineerAvailability (
            id INTEGER PRIMARY KEY,
            engineer_id TEXT NOT NULL,
            H09M00 BOOL,
            H09M30 BOOL,
            H10M00 BOOL,
            H10M30 BOOL,
            H11M00 BOOL,
            H11M30 BOOL,
            H12M00 BOOL,
            H12M30 BOOL,
            H13M00 BOOL,
            H13M30 BOOL,
            H14M00 BOOL,
            H14M30 BOOL,
            H15M00 BOOL,
            H15M30 BOOL,
            H16M00 BOOL,
            H16M30 BOOL,
            timestamp TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS BookedInspection (
            id INTEGER PRIMARY KEY,
            inspection_id INTEGER,
            engineer_id INTEGER,
            inspection_date TEXT,
            booked_start_time TEXT,
            booked_end_time TEXT,
            FOREIGN KEY (engineer_id) REFERENCES EngineerAvailability(id)
        );
        """,
        """
        CREATE VIEW BookedInspectionView AS
        SELECT i.id, i.inspection_id, e.engineer_id, i.inspection_date,
            i.booked_start_time, i.booked_end_time
        FROM BookedInspection i
        INNER JOIN EngineerAvailability e ON e.id = i.engineer_id;
        """
    ]

    try:
        with sqlite3.connect(filename) as conn:
            cursor = conn.cursor()
            for statement in sql_statements:
                cursor.execute(statement)
            conn.commit()
    except sqlite3.Error as e:
        print('create_tables:', e)


def insert_engineer_data(cursor, engineer_data):
    data = (
        None,
        engineer_data['engineer_id'],
        *engineer_data['available_slots'],
        engineer_data['updated_timestamp']
    )

    cursor.execute('''
        INSERT INTO EngineerAvailability
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)


def insert_inspection_data(cursor, inspection_data):
    availability_row_id, availability_vec = ops.get_availability(
        cursor, inspection_data['engineer_id'],
        inspection_data['inspection_date']
    )
    inspection_vec = ops.interval_to_vec(
        inspection_data['booked_start_time'],
        inspection_data['booked_end_time']
        )

    agreed = availability_vec @ inspection_vec
    total = inspection_vec.sum()

    if agreed < total:
        raise Exception('The engineer is not available for inspection.')

    data = (
        None,
        inspection_data['inspection_id'],
        availability_row_id,
        inspection_data['inspection_date'],
        inspection_data['booked_start_time'],
        inspection_data['booked_end_time']
    )

    cursor.execute('''
        INSERT INTO BookedInspection
        VALUES (?, ?, ?, ?, ?, ?)
    ''', data)


def read_json_then(folder_path, side_effect):
    json_files = [
        file for file in os.listdir(folder_path) if file.endswith('.json')
    ]

    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        with open(file_path, 'r') as file:
            data = json.load(file)
        try:
            side_effect(cursor, data)
        except Exception as e:
            print(json_file, e)


if __name__ == '__main__':
    db_name = './db/inspection_booking.db'

    create_sqlite_database(db_name)
    create_tables(db_name)

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    availability_folder_path = './data/engineer_availability'
    inspection_folder_path = './data/inspections'

    read_json_then(availability_folder_path, insert_engineer_data)
    read_json_then(inspection_folder_path, insert_inspection_data)

    conn.commit()
    conn.close()
