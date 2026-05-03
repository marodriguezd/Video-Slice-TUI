"""Tests for splitter range generation utilities."""

import pytest

from logic import build_ranges_by_interval, build_ranges_by_count


class TestBuildRangesByInterval:
    def test_exact_division(self):
        ranges = build_ranges_by_interval(180.0, 60.0)
        assert len(ranges) == 3
        assert (ranges[0].start, ranges[0].end) == (0.0, 60.0)
        assert (ranges[1].start, ranges[1].end) == (60.0, 120.0)
        assert (ranges[2].start, ranges[2].end) == (120.0, 180.0)

    def test_last_chunk_shorter(self):
        ranges = build_ranges_by_interval(25.0, 10.0)
        assert len(ranges) == 3
        assert (ranges[0].start, ranges[0].end) == (0.0, 10.0)
        assert (ranges[1].start, ranges[1].end) == (10.0, 20.0)
        assert (ranges[2].start, ranges[2].end) == (20.0, 25.0)

    def test_invalid_chunk_duration(self):
        with pytest.raises(ValueError):
            build_ranges_by_interval(100.0, 0.0)


class TestBuildRangesByCount:
    def test_exact_division(self):
        ranges = build_ranges_by_count(180.0, 3)
        assert len(ranges) == 3
        assert ranges[0].duration() == 60.0
        assert ranges[1].duration() == 60.0
        assert ranges[2].duration() == 60.0

    def test_non_exact_division(self):
        ranges = build_ranges_by_count(100.0, 3)
        assert len(ranges) == 3
        assert ranges[0].start == 0.0
        assert ranges[-1].end == 100.0
        assert ranges[0].end == pytest.approx(100.0 / 3.0)
        assert ranges[1].end == pytest.approx(2 * (100.0 / 3.0))

    def test_invalid_total_chunks(self):
        with pytest.raises(ValueError):
            build_ranges_by_count(100.0, 0)
