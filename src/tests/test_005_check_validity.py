#!/usr/bin/env python3
# coding: utf-8

import datetime
import pytest

from .context import check_validity
from check_validity import (
    convert_date_to_datetime,
    convert_datetime_to_date,
    convert_date_to_str,
    convert_datetime_to_epoch,
    convert_epoch_to_datetime,
    time_delta,
)


class TestTimeConverters:
    def test_date_datetime_converter(self):
        today = datetime.date.today()
        today_dt = convert_date_to_datetime(today)

        today_date = convert_datetime_to_date(today_dt)
        assert (today.year, today.month, today.day) == (
            today_date.year,
            today_date.month,
            today_date.day,
        )
        assert (today_date.hour, today_date.minute, today_date.second) == (0, 0, 0)
        today_date_str = convert_date_to_str(today_date)
        today_str = convert_date_to_str(today)
        assert today_date_str == today_str

    def test_epoch_datetime_converter(self):
        now = datetime.datetime.now()
        epoch_now = convert_datetime_to_epoch(now)
        datetime_now = convert_epoch_to_datetime(epoch_now)
        assert datetime_now == now


class TestSimpleTimeDeltaOperation:
    @pytest.mark.parametrize(
        "input",
        [
            ("+", 100),
            ("-", 100),
            ("+", 3),
            ("-", 3),
            ("+", 2),
            ("-", 2),
            ("+", 1),
            ("-", 1),
            ("+", 0),
            ("-", 0),
        ],
    )
    def test_time_delta_operation_expected(self, input):
        today_dt = datetime.datetime.now()
        input_op, input_nb = input
        result = time_delta(input_op, input_nb)
        if input_op == "+":
            assert result.year == today_dt.year + input_nb, result
        else:
            assert result.year == today_dt.year - input_nb, result

    # def test_time_delta_expected(self, input_expected):
    #     input_op, input_nb, expected = input_expected
    #     result = time_delta(input_op, input_nb)
    #     assert result == expected, result
