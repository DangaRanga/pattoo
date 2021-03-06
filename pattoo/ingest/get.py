#!/usr/bin/env python3
"""Verifies the existence of various database table primary key values."""

# Import project libraries
from pattoo.db.table import pair


def pairs(pattoo_db_record):
    """Create db Pair table entries.

    Args:
        pattoo_db_record: PattooDBrecord object

    Returns:
        result: List of Pair.idx_pair database index values

    """
    # Initialize key variables
    result = []

    # Get key-values
    _pairs = key_value_pairs(pattoo_db_record)

    # Get list of pairs in the database
    pair.insert_rows(_pairs)
    result = pair.idx_pairs(_pairs)

    # Return
    return result


def key_value_pairs(pattoo_db_records):
    """Create a list of key-value pairs.

    Args:
        pattoo_db_records: List of PattooDBrecord objects

    Returns:
        rows: List of (key, value) tuples

    """
    # Initialize key variables
    rows = []
    pattoo_agent_pair_table_keys = ['pattoo_metadata', 'pattoo_key']

    if isinstance(pattoo_db_records, list) is False:
        pattoo_db_records = [pattoo_db_records]

    for pattoo_db_record in pattoo_db_records:
        # Get the agent program name
        pap = pattoo_db_record.pattoo_agent_program

        # Iterate over NamedTuple
        for key, value in sorted(pattoo_db_record._asdict().items()):

            # Ignore keys that don't belong in the Pair table
            if key.startswith('pattoo') is True:
                if key not in pattoo_agent_pair_table_keys:
                    continue

            if key == 'pattoo_metadata':
                # Process the metadata key-values
                rows.extend([(make_key(pap, __k), __v) for __k, __v in value])
            else:
                # Process pattoo_key's key
                rows.append((str(key), make_key(pap, value)))

    return sorted(rows)


def make_key(pattoo_agent_program, key):
    """Prepend the Agent program name to the key for uniqueness.

    Args:
        pattoo_agent_program: Program name
        key: Key

    Returns:
        result: Result

    """
    # Return
    result = '{}_{}'.format(pattoo_agent_program, key)
    return result
