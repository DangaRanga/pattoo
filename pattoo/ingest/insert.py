#!/usr/bin/env python3
"""Pattoo classes that manage various data."""

# Import project libraries
from pattoo.db import db
from pattoo.db.tables import Checksum, Pair, Glue, Data
from pattoo.ingest import exists

from pattoo_shared import log


def timeseries(items):
    """Insert timeseries data.

    Args:
        items: List of IDXTimestampValue objects

    Returns:
        result: Checksum.checksum value

    """
    # Initialize key variables
    rows = []

    # Update the data
    for item in items:
        # Insert data
        value = round(item.value, 10)
        rows.append(
            Data(idx_checksum=item.idx_checksum,
                 timestamp=item.timestamp,
                 value=value)
        )
    if bool(rows) is True:
        with db.db_modify(20012, die=True) as session:
            session.add_all(rows)


def checksum(_checksum, data_type):
    """Create the database Checksum.checksum value.

    Args:
        _checksum: Checksum value
        data_type: Type of data

    Returns:
        None

    """
    # Filter invalid data
    if isinstance(_checksum, str) is True:
        # Insert and get the new checksum value
        row = Checksum(checksum=_checksum.encode(), data_type=data_type)
        with db.db_modify(20001, die=True) as session:
            session.add(row)


def pair(key, value):
    """Create db Pair table entries.

    Args:
        _key: Key-value pair key
        _value: Key-value pair value

    Returns:
        None

    """
    # Insert and get the new idx_datasource value
    row = Pair(key=key.encode(), value=value.encode())
    with db.db_modify(20003, die=True) as session:
        session.add(row)


def pairs(pattoo_db_record):
    """Create db Pair table entries.

    Args:
        pattoo_db_record: PattooDBrecord object

    Returns:
        None

    """
    # Initialize key variables
    rows = []
    _kvs = exists.key_values(pattoo_db_record)

    # Iterate over NamedTuple
    for key, value in _kvs:
        # Skip non-metadata pre-existing pairs
        if exists.pair(key, value) is True:
            continue

        # Insert and get the new idx_datasource value
        row = Pair(key=key.encode(), value=value.encode())
        rows.append(row)

    if bool(rows) is True:
        with db.db_modify(20007, die=True) as session:
            session.add_all(rows)


def glue(idx_checksum, idx_pairs):
    """Create db Pair table entries.

    Args:
        idx_checksum: Checksum.idx_checksum
        idx_pairs: List of Pair.idx_pair values

    Returns:
        None

    """
    # Initialize key variables
    rows = []

    # Iterate over NamedTuple
    for idx_pair in idx_pairs:
        pair_exists = exists.glue(idx_checksum, idx_pair)
        if bool(pair_exists) is False:
            # Insert and get the new idx_datasource value
            row = Glue(idx_pair=idx_pair, idx_checksum=idx_checksum)
            rows.append(row)

    if bool(rows) is True:
        with db.db_modify(20002, die=True) as session:
            session.add_all(rows)
