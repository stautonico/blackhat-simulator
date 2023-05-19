import time
from typing import Literal, Optional


class Timestamp:
    def __init__(self):
        self._timestamp: float = time.time_ns()
        self._precision: Literal["ns", "us", "ms", "s"] = "ns"

    def get_timestamp_ns(self, local_time=False) -> int:
        """
        Get the timestamp in nanoseconds
        :param local_time: If the timestamp should be converted to the local timezone
        :return: The timestamp in nanoseconds
        """
        if local_time:
            return int(self._timestamp + time.timezone * 1000000000)

        return int(self._timestamp)

    def get_timestamp_us(self, local_time=False) -> int:
        """
        Get the timestamp in microseconds
        :param local_time: If the timestamp should be converted to the local timezone
        :return: The timestamp in microseconds
        """
        if local_time:
            return int(self._timestamp / 1000 + time.timezone * 1000000)

        return int(self._timestamp / 1000)

    def get_timestamp_ms(self, local_time=False) -> int:
        """
        Get the timestamp in milliseconds
        :param local_time: If the timestamp should be converted to the local timezone
        :return: The timestamp in milliseconds
        """
        if local_time:
            return int(self._timestamp / 1000000 + time.timezone * 1000)

        return int(self._timestamp / 1000000)

    def get_timestamp_s(self, local_time=False) -> int:
        """
        Get the timestamp in seconds
        :param local_time: If the timestamp should be converted to the local timezone
        :return: The timestamp in seconds
        """
        if local_time:
            return int(self._timestamp / 1000000000 + time.timezone)

        return int(self._timestamp / 1000000000)

    def set_timestamp(self, timestamp: int, precision: Optional[Literal["ns", "us", "ms", "s"]] = None,
                      local_time=False):
        """
        Manually set the timestamp. The precision of the timestamp can be manually entered, but if it is not, the
        precision will be automatically determined.
        :param timestamp: The timestamp to set (UTC assumed unless local_time is True)
        :param precision: The precision of the timestamp (ns, us, ms, s) (optional)
        :param local_time: If the timestamp is in the local timezone (will be converted to UTC)
        :return:
        """
        if precision is None:
            # If the length is 1-11 characters, it's seconds
            if len(str(timestamp)) <= 11:
                precision = "s"
            # If the length is 12-14 characters, it's milliseconds
            elif len(str(timestamp)) <= 14:
                precision = "ms"
            # If the length is 15-16 characters, it's microseconds
            elif len(str(timestamp)) <= 16:
                precision = "us"
            # If the length is 17-18 characters, it's nanoseconds
            elif len(str(timestamp)) <= 18:
                precision = "ns"

        # Convert the timestamp to nanoseconds
        if precision == "s":
            ns_timestamp = timestamp * 1000000000
        elif precision == "ms":
            ns_timestamp = timestamp * 1000000
        elif precision == "us":
            ns_timestamp = timestamp * 1000
        else:
            ns_timestamp = timestamp

        # Convert the timestamp to UTC
        if local_time:
            ns_timestamp -= time.timezone * 1000000000

        self._timestamp = ns_timestamp

    def set_precision(self, precision: Literal["ns", "us", "ms", "s"]):
        """
        Set the precision of the timestamp. The timestamp object will always store the timestamp in the highest
        precision possible, but this function will set the precision that the comparison operators will use.
        If you try to compare two timestamps with different precisions, the timestamp with the lower precision will be
        used.
        :param precision: The precision to use for comparisons (ns, us, ms, s)
        :return:
        """
        precision = precision.lower()
        if precision not in ["ns", "us", "ms", "s"]:
            raise ValueError("Invalid precision")

        self._precision = precision

    def set_now(self):
        """
        Set the timestamp to the current time. Stores the timestamp in microsecond precision, but the precision
        that was manually set (or if the default was set) will still be used for comparisons.
        :return:
        """
        self._timestamp = time.time_ns()

    def copy(self):
        """
        Make a copy of the timestamp, which is independent of the original timestamp. If the copy is modified, the
        original timestamp will not be modified.
        :return: A copy of the timestamp
        """
        new_timestamp = Timestamp()
        new_timestamp.set_timestamp(self.get_timestamp_ns())
        new_timestamp.set_precision(self._precision)
        return new_timestamp

    def to_datetime(self):
        """
        Convert the timestamp to a datetime object
        :return: A datetime object
        """
        import datetime
        return datetime.datetime.fromtimestamp(self.get_timestamp_s())

    def to_str(self, precision: Optional[Literal["ns", "us", "ms", "s"]] = None):
        """
        Convert the timestamp to a string
        :param precision: The precision to convert the timestamp to (ns, us, ms, s) (optional)
        :return: A string representation of the timestamp
        """
        if precision is None:
            precision = self._precision

        if precision == "ns":
            return str(self.get_timestamp_ns())
        elif precision == "us":
            return str(self.get_timestamp_us())
        elif precision == "ms":
            return str(self.get_timestamp_ms())
        else:
            return str(self.get_timestamp_s())


    # TODO: Implement from_datetime if required
    @staticmethod
    def from_timestamp(timestamp: int, precision: Optional[Literal["ns", "us", "ms", "s"]] = None,
                       local_time=False):
        """
        Create a timestamp from a timestamp
        :param timestamp: The timestamp to create the timestamp from
        :param precision: The precision of the timestamp (ns, us, ms, s) (optional)
        :param local_time: If the timestamp is in the local timezone (will be converted to UTC)
        :return: A timestamp object
        """
        new_timestamp = Timestamp()
        new_timestamp.set_timestamp(timestamp, precision, local_time)
        return new_timestamp



    def _get_value_to_compare(self, other):
        # Find the least precise timestamp (between the two timestamps)
        if self._precision == "ns" or other._precision == "ns":
            least_precise = "ns"
        elif self._precision == "us" or other._precision == "us":
            least_precise = "us"
        elif self._precision == "ms" or other._precision == "ms":
            least_precise = "ms"
        else:
            least_precise = "s"

        # Get the value of the timestamp to compare
        function = f"get_timestamp_{least_precise}"
        return getattr(self, function)(), getattr(other, function)()

    def _lt_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp < other_timestamp

    def _le_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp <= other_timestamp

    def _gt_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp > other_timestamp

    def _ge_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp >= other_timestamp

    def _eq_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp == other_timestamp

    def _ne_(self, other):
        self_timestamp, other_timestamp = self._get_value_to_compare(other)
        return self_timestamp != other_timestamp

    def __str__(self):
        return f"Timestamp({self.get_timestamp_ns()}ns)"

    def __repr__(self):
        return self.__str__()
