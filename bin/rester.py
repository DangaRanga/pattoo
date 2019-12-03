#!/usr/bin/env python3
"""Pattoo agent data cache ingester.

Used to add data to backend database

"""

# Standard libraries
import sys
import os
import numpy as np
from pprint import pprint
import time

# Try to create a working PYTHONPATH
_BIN_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ROOT_DIRECTORY = os.path.abspath(os.path.join(_BIN_DIRECTORY, os.pardir))
if _BIN_DIRECTORY.endswith('/pattoo/bin') is True:
    sys.path.append(_ROOT_DIRECTORY)
else:
    print(
        'This script is not installed in the "pattoo/bin" directory. '
        'Please fix.')
    sys.exit(2)

# Pattoo libraries
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

# pattoo imports
from pattoo_shared.constants import (
    DATA_INT, DATA_FLOAT, DATA_COUNT64, DATA_COUNT)
from pattoo import data
from pattoo import uri
from pattoo.db import db
from pattoo.db.tables import Data, DataPoint
from pattoo_shared import times


def main():
    """Ingest data."""
    # Initialize key variables
    idx_datapoint = 3
    found = False
    (ts_start, ts_stop) = uri.chart_timestamp_args()

    try:
        # Deal with that as well
        with db.db_query(20128) as session:
            metadata = session.query(
                DataPoint.data_type, DataPoint.polling_interval).filter(
                    DataPoint.idx_datapoint == idx_datapoint).one()
            found = True
    except MultipleResultsFound as _:
        pass
    except NoResultFound as _:
        pass

    # Get the _result
    if found is True:
        query(idx_datapoint, ts_start, ts_stop, metadata)


def query(idx_datapoint, ts_start, ts_stop, metadata):
    """Ingest data."""
    # Initialize key variables
    data_type = metadata.data_type
    polling_interval = metadata.polling_interval
    places = 10
    result = []

    # Make sure we have entries for entire time range
    (norm_ts_stop, _) = times.normalized_timestamp(
        polling_interval, timestamp=ts_stop)
    (norm_ts_start, _) = times.normalized_timestamp(
        polling_interval, timestamp=ts_start)
    nones = {_key: None for _key in range(
        norm_ts_start, norm_ts_stop, polling_interval)}

    # Create list of timestamps and values
    timestamps = []
    values = []
    for timestamp, value in sorted(nones.items()):
        timestamps.append(timestamp)
        values.append(value)

    # Get data from database
    with db.db_query(20127) as session:
        rows = session.query(Data.timestamp, Data.value).filter(and_(
            Data.timestamp < ts_stop, Data.timestamp > ts_start,
            Data.idx_datapoint == idx_datapoint)).order_by(
                Data.timestamp).all()

    if data_type in [DATA_INT, DATA_FLOAT]:
        # Process non-counter values
        for row in rows:
            # Get timestamp to the nearest polling_interval bounary
            (timestamp, _) = times.normalized_timestamp(
                polling_interval, timestamp=row.timestamp)
            rounded_value = round(float(row.value), places)
            values.append({'timestamp': timestamp, 'value': rounded_value})

    elif data_type in [DATA_COUNT64, DATA_COUNT] and len(rows) > 1:
        # Process counter values by calculating the difference between
        # successive values
        array = np.asarray(rows)
        db_timestamps = array[:, 0].tolist()
        db_values = array[:, 1].tolist()

        # Populate seed value list with values from DB
        for db_index, timestamp in db_timestamps:
            index = timestamps.index(timestamp)
            values[index] = db_values[db_index]

        # Remove first timestamp value as it isn't necessary
        # after deltas are created
        timestamps = timestamps[1:]

        # Create an array for ease of readability.
        # Convert to None values to nans to make deltas without errors
        values_array = np.array(values).astype(np.float)

        '''
        Sometimes we'll get unsigned counter values that roll over to zero.
        This will result in the delta being negative. We need a way to detect
        this and make the delta value be:

        value.current + integer.type.max - value.previous

        '''
        if data_type == DATA_COUNT:
            deltas = np.diff(values_array.astype(np.int32))
        else:
            deltas = np.diff(values_array.astype(np.int64))
        for key, delta in enumerate(deltas):
            # Get timestamp to the nearest polling_interval bounary
            (timestamp, _) = times.normalized_timestamp(
                polling_interval, timestamp=timestamps[key])

            # Calculate the value as a transaction per second value
            rounded_delta = round((delta / polling_interval) * 1000, places)
            result.append({'timestamp': timestamp, 'value': rounded_delta})
            # print(timestamp, result[timestamp])

    pprint(result)
    print('\nRecords:', len(values), '\n')


if __name__ == '__main__':
    main()
