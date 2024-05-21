import unittest
from datetime import time
import numpy as np
from unittest.mock import MagicMock

import ops
import init


class Tests(unittest.TestCase):
    def test_ops_iter_slots(self):
        slots = list(ops.iter_slots())

        self.assertEqual(slots[0][0], '09')
        self.assertEqual(slots[0][1], '00')

        self.assertEqual(slots[-1][0], '16')
        self.assertEqual(slots[-1][1], '30')

    def test_ops_availability_column_from_iter(self):
        columns = list(
            map(ops.availability_column_from_iter, ops.iter_slots())
        )

        self.assertEqual(columns[0], 'H09M00')

        self.assertEqual(columns[-1], 'H16M30')

    def test_ops_time_from_iter(self):
        slots_time = list(map(ops.time_from_iter, ops.iter_slots()))

        self.assertEqual(slots_time[0], time(9, 0))

        self.assertEqual(slots_time[-1], time(16, 30))

    def test_ops_interval_to_vec(self):
        vec = ops.interval_to_vec('09:00', '17:00')

        self.assertTrue(np.all(vec == np.ones(16)))

        vec = ops.interval_to_vec('09:00', '09:29')

        self.assertTrue(vec[0] == 1)
        self.assertTrue(np.all(vec[1:] == np.zeros(15)))

    def test_ops_get_availability(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = [10] + 16 * [1]
        cursor.fetchall.return_value = [
        ]

        res = ops.get_availability(cursor, 'E1', '2024-05-17')

        self.assertTrue(res[0] == 10)
        self.assertTrue(np.all(res[1] == np.ones(16)))

        cursor.fetchone.return_value = [10, 1] + 15 * [0]
        cursor.fetchall.return_value = [
            {
                'booked_start_time': '09:10',
                'booked_end_time': '09:29',
            }
        ]

        res = ops.get_availability(cursor, 'E1', '2024-05-17')

        self.assertTrue(res[0] == 10)
        self.assertTrue(np.all(res[1] == np.zeros(16)))

        cursor.fetchone.return_value = [10] + 16 * [1]
        cursor.fetchall.return_value = [
            {
                'booked_start_time': '09:10',
                'booked_end_time': '09:45',
            },
            {
                'booked_start_time': '11:10',
                'booked_end_time': '12:30',
            }
        ]

        res = ops.get_availability(cursor, 'E1', '2024-05-17')
        target = np.array([0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertTrue(res[0] == 10)
        self.assertTrue(np.all(res[1] == target))

    def test_insert_engineer_data(self):
        data = {
            "engineer_id": "E123",
            "available_day": "Thursday",
            "available_slots": "1100110011001100",
            "updated_timestamp": "2024-05-16 10:30:00"
        }

        cursor = MagicMock()
        init.insert_engineer_data(cursor, data)

    def test_insert_inspection_data(self):
        data = {
            "inspection_id": "I123",
            "engineer_id": "E123",
            "inspection_date": "2024-05-17",
            "booked_start_time": "10:00",
            "booked_end_time": "11:30"
        }

        cursor = MagicMock()
        cursor.fetchone.return_value = [10] + 16 * [1]
        cursor.fetchall.return_value = []
        init.insert_inspection_data(cursor, data)

        cursor.fetchone.return_value = [10] + 16 * [1]
        cursor.fetchall.return_value = [
            {
                'booked_start_time': '10:10',
                'booked_end_time': '10:50',
            }
        ]

        with self.assertRaises(Exception):
            init.insert_inspection_data(cursor, data)


if __name__ == "__main__":
    unittest.main()
