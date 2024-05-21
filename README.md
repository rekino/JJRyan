# JJRyan Challenge

This repository contains the code solution of the challenge for the role of Data Engineer/Scientist at JJRyan. The solution uses an SQLite file as an database and the API is developed using Flask. To use, build and run the docker file in the repo. To make the database permanent or add new JSON data simply mount a folder on your hard-drive on the docker container and everything should be good to go.

## Data Engineering Goals:
### Data Extraction and Transformation:
Since there were no JSON files attached to the email, I figured that I can come up with my own scheme. There is a folder called 'data' that contains the JSON filed. Each Inspection and Availability item has its own JSON file. For example:

```
{
  "engineer_id": "E123",
  "available_slots": "1110110011001100",
  "updated_timestamp": "2024-05-16 10:30:00"
}
```
is a JSON file that contains one availability item.

The database consistes of two tables, `EngineerAvailability` and `BookedInspection`. The `EngineerAvailability` table saves the availability items as is to the database with the one exception that splits the bits of the availability_slots string into their own columns. The `BookedInspection` table houses the inspection details and is related to the `EngineerAvailability` through `EngineerAvailability.id` and `BookedInspection.engineer_id`. The following diagram shows the database design.

```
  +----------------------+          +-------------------+
  | EngineerAvailability |          | Inspection        |
  +----------------------+ 1        +-------------------+
  | id                   |<---      | id                |
  | engineer_id          |    |   n | inspection_id     |
  | H09M00               |     ---->| engineer_id       |
  | H09M30               |          | inspection_date   |
  | ...                  |          | booked_start_time |
  | H16M30               |          | booked_end_time   |
  | updated_timestamp    |          +-------------------+
  +----------------------+          

```
The rational behind chosing the `EngineerAvailability.id` as the foreign key is to allow for historical data to accumulate in the table. In other words, if the availability of an engineer changes, the timestamp will determine the latest change while keeping the historical data intact. The reason for keeping the availability time as a binary vector is that doing so would simplify the use of linear algebra operations that can come quite in handy when dealing with the particular setting of the challenge.

### API Development:
I came up with two simple GET endpoints for the challenge. One is the `/booking` route that gets an `engineer_id` and a date `inspection_date` and returns all the inspections that are booked for the engineer on that date. The second endpoints is `/inspections` which takes a starting date and an end date and returns all of the inspections in that time interval.

### Considerations:
The historical data would remain in the database and the solution can reconstruct the database from JSON files in a way that is independent of the order of the files. The `insert_inspection_data` function in the `init.py` file will make sure that the database would not end up in an inconsistent state by first checking that the inspection is being assigned to an engineer that is indeed free considering all the inspections that the engineer has commited to.

## Examination Work and Deliverables
### Backend Development:
The challenge is done in Python with the help of Flask and Numpy libraries. The database is chosen to be SQLite so there is no need for cloud-housted databases.
### Containerization:
A Dockerfile is provided.

## Supporting Information
The challenge specifies an `available_day` as well as part of the engineer schedule. However, I have decided to remove it since its solution is similar to the situation of time slots. In other words, by increasing and decreasing the period of time slots any interval of time could be turned into the vectors that are used in the solution. Similarly, I do not repeat the solution for keeping the historical data for later analytics on the `Inspection` table since this as well is completely analogous to the `EngineerAvailability` case and a timestamp column should be all that is needed to implement it.

## Update 5/21/2024
It was decided that some endpoints get added to the application and add degrees of freedom in engineeres availability throughout the week. 

Adding degrees of freedom with regrads to engineering availability is simply more of the same solution; a column gets added to the engineers availability that stores the corresponding day of the week and let `engineer_id` and `day_of_week` act similar to a composite unique key.

The solution for computing utilization of an engineer is a little unintuitive. The main issue is dealing with the irregularities that are introduced due to the introduction of the `day_of_week` column. The idea is to compute a heuristic value for the total availability of an engineer between two dates based on the initial availability of the engineer, and then add a correction to the value which makes it accurate as we process all of the availability vectors that are filtered by the query.

Suppose that the availability of engineers in each day of the week at the start of the interval is known and call it `a`. It can be deduced that, if the availability does not change by the end of the interval, then the total availability of the enginner would be `a[day, 0] * c[day, start, end]` in which `c[day, start, end]` counts how many of that day happens in the interval. However, it is possible that the availability changes. To correct the hueristic, we will find the closest update to the start of the interval and fix the value by `e = (a[day, 1] - a[day, 0]) * c[day, timestamp, end]`. It can be seen that `a[day, 0] * c[day, start, end] + e = a[day, 1] * c[day, timestamp, end] + a[day, 0 ] * c[day,start, timestamp]`. By induction, it should be that after processing every row the computed value is exact.