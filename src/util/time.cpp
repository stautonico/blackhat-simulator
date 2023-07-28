#include <util/time.h>

#include <string>
#include <chrono>
#include <ctime>

Timestamp::Timestamp() {
  // Default constructor sets the timestamp to the current time
  this->m_precision = Precision::ns;
  this->m_ns_timestamp =
      std::chrono::duration_cast<std::chrono::nanoseconds>(
          std::chrono::system_clock::now().time_since_epoch())
          .count();
}

Timestamp Timestamp::from_timestamp(long timestamp,
                                    std::optional<Precision> precision,
                                    bool local_time) {
  Timestamp ts;
  ts.set_timestamp(timestamp, precision, local_time);

  return ts;
}

void Timestamp::set_timestamp(long timestamp,
                              std::optional<Precision> precision,
                              bool local_time) {
  Precision p;
  if (precision == std::nullopt) {
    // Try to guess the precision
    // If the length is 1-11 characters, it's probably seconds
    if (std::to_string(timestamp).length() <= 11) {
      p = Precision::s;
      // If the length is 12-14 characters, it's probably milliseconds
    } else if (std::to_string(timestamp).length() <= 14) {
      p = Precision::ms;
      // If the length is 15-17 characters, it's probably microseconds
    } else if (std::to_string(timestamp).length() <= 17) {
      p = Precision::us;
    } else {
      // Otherwise, it's probably nanoseconds
      p = Precision::ns;
    }
  } else
    p = precision.value();

  long ns_timestamp;

  // Convert the timestamp
  if (p == Precision::s)
    ns_timestamp = timestamp * 1000000000;
  else if (precision == Precision::ms)
    ns_timestamp = timestamp * 1000000;
  else if (precision == Precision::us)
    ns_timestamp = timestamp * 1000;
  else
    ns_timestamp = timestamp;

  // Convert the timestamp to UTC
  if (local_time) {
    // Figure out the timezone offset
    // TODO: Make sure this works on all platforms
    //        time_t t = time(NULL);
    //        struct tm lt = {0};
    //        localtime_r(&t, &lt);

    // Convert the timestamp
    //        ns_timestamp += lt.tm_gmtoff * 1000000000;
    ns_timestamp += timezone * 1000000000;
  }

  this->m_ns_timestamp = ns_timestamp;
  this->m_precision = p;
}

// TODO: Implement "as local time" option
long Timestamp::get_seconds() { return this->m_ns_timestamp / 1000000000; }

long Timestamp::get_milliseconds() { return this->m_ns_timestamp / 1000000; }

long Timestamp::get_microseconds() { return this->m_ns_timestamp / 1000; }

long Timestamp::get_nanoseconds() { return this->m_ns_timestamp; }