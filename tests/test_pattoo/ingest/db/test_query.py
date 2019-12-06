#!/usr/bin/env python3
"""Test pattoo configuration."""

import os
import unittest
import sys
import time
from random import random

# Try to create a working PYTHONPATH
EXEC_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(
    os.path.abspath(os.path.join(
            os.path.abspath(os.path.join(
                os.path.abspath(os.path.join(
                        EXEC_DIR,
                        os.pardir)), os.pardir)), os.pardir)), os.pardir))

if EXEC_DIR.endswith(
        '/pattoo/tests/test_pattoo/ingest/db') is True:
    # We need to prepend the path in case PattooShared has been installed
    # elsewhere on the system using PIP. This could corrupt expected results
    sys.path.insert(0, ROOT_DIR)
else:
    print('''\
This script is not installed in the "pattoo/tests/test_pattoo/ingest/db" \
directory. Please fix.''')
    sys.exit(2)

from pattoo_shared import data
from pattoo_shared.constants import DATA_FLOAT, PattooDBrecord
from tests.libraries.configuration import UnittestConfig
from pattoo.constants import ChecksumLookup
from pattoo.ingest.db import query, insert, exists
from pattoo.ingest import get


class TestBasicFunctioins(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################

    def test_idx_datapoints(self):
        """Testing method / function idx_datapoints."""
        # Initialize key variables
        idx_datapoints = []
        checksums = []
        polling_interval = 1

        # Populate database
        for _ in range(0, 10):
            time.sleep(0.05)

            # Add the checksum to the database
            checksum = data.hashstring(str(random()))
            checksums.append(checksum)
            insert.checksum(checksum, DATA_FLOAT, polling_interval)
            idx_datapoints.append(exists.checksum(checksum))

        # Test
        result = query.idx_datapoints(checksums)
        self.assertEqual(len(result), len(checksums))
        for idx_datapoint in result:
            self.assertTrue(idx_datapoint in idx_datapoints)

    def test_checksums(self):
        """Testing method / function checksums."""
        # Initialize key variables
        expected = {}
        polling_interval = 1

        # Populate database with key-value pairs
        source = data.hashstring(str(random()))
        for data_index in range(0, 10):
            time.sleep(0.05)

            # Add the checksum to the database
            checksum = data.hashstring(str(random()))
            insert.checksum(checksum, DATA_FLOAT, polling_interval)
            idx_datapoint = exists.checksum(checksum)

            # Define what we expect from the test function
            expected[checksum] = ChecksumLookup(
                idx_datapoint=idx_datapoint,
                polling_interval=polling_interval,
                last_timestamp=1)

            # Add key-pairs to the database
            record = PattooDBrecord(
                pattoo_checksum=checksum,
                pattoo_key='key',
                pattoo_polling_interval=polling_interval,
                pattoo_source=source,
                pattoo_timestamp=int(time.time() * 1000),
                pattoo_data_type=DATA_FLOAT,
                pattoo_value=(data_index * 10),
                pattoo_metadata=[])
            pairs = get.key_value_pairs(record)
            insert.pairs(pairs)
            idx_pairs = query.pairs(pairs)

            # Create glue entry
            insert.glue(idx_datapoint, idx_pairs)

        #######################################################################
        # This is added to verify that we only get a subset of results
        #######################################################################

        fake_source = data.hashstring(str(random()))
        for data_index in range(0, 17):
            time.sleep(0.05)

            # Add the checksum to the database
            checksum = data.hashstring(str(random()))
            insert.checksum(checksum, DATA_FLOAT, polling_interval)
            idx_datapoint = exists.checksum(checksum)

            # Add key-pairs to the database
            record = PattooDBrecord(
                pattoo_checksum=checksum,
                pattoo_key='key',
                pattoo_polling_interval=polling_interval,
                pattoo_source=fake_source,
                pattoo_timestamp=int(time.time() * 1000),
                pattoo_data_type=DATA_FLOAT,
                pattoo_value=(data_index * 10),
                pattoo_metadata=[])
            pairs = get.key_value_pairs(record)
            insert.pairs(pairs)
            idx_pairs = query.pairs(pairs)

            # Create glue entry
            insert.glue(idx_datapoint, idx_pairs)

        # Test
        result = query.checksums(source)
        self.assertTrue(bool(result))
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), len(expected))
        for key, value in result.items():
            self.assertEqual(
                value.idx_datapoint,
                expected[key].idx_datapoint)
            self.assertEqual(
                value.polling_interval,
                expected[key].polling_interval)
            self.assertEqual(
                value.last_timestamp,
                expected[key].last_timestamp)

    def test_glue(self):
        """Testing method / function glue."""
        # Initialize key variables
        checksum = data.hashstring(str(random()))
        polling_interval = 1
        keypairs = []
        idx_pairs = []
        for _ in range(0, 10):
            time.sleep(0.05)
            key = data.hashstring(str(random()))
            value = data.hashstring(str(random()))
            keypairs.append((key, value))

        # Insert values in tables
        insert.pairs(keypairs)
        insert.checksum(checksum, DATA_FLOAT, polling_interval)
        idx_datapoint = exists.checksum(checksum)

        # Test
        for key, value in keypairs:
            idx_pairs.append(exists.pair(key, value))
        insert.glue(idx_datapoint, idx_pairs)

        result = query.glue(idx_datapoint)
        self.assertEqual(len(result), len(idx_pairs))
        for idx_pair in idx_pairs:
            self.assertTrue(idx_pair in result)

    def test_pairs(self):
        """Testing method / function pairs."""
        # Initialize key variables
        keypairs = []
        idx_pairs = []
        for _ in range(0, 10):
            time.sleep(0.05)
            key = data.hashstring(str(random()))
            value = data.hashstring(str(random()))
            keypairs.append((key, value))

        # Insert values in tables
        insert.pairs(keypairs)

        # Test
        for key, value in keypairs:
            idx_pairs.append(exists.pair(key, value))

        result = query.pairs(keypairs)
        self.assertEqual(len(result), len(idx_pairs))
        for idx_pair in idx_pairs:
            self.assertTrue(idx_pair in result)


if __name__ == '__main__':
    # Make sure the environment is OK to run unittests
    UnittestConfig().create()

    # Do the unit test
    unittest.main()