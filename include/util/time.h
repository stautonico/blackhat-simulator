#pragma once

#include <optional>

enum class Precision {
  ns, // Nanoseconds
  us, // Microseconds
  ms, // Milliseconds
  s   // Second
};

class Timestamp {
public:
  Timestamp();

  static Timestamp from_timestamp(long timestamp,
                                  std::optional<Precision> precision,
                                  bool local_time);

  void set_timestamp(long timestamp, std::optional<Precision> precision,
                     bool local_time);

  long get_seconds();
  long get_milliseconds();
  long get_microseconds();
  long get_nanoseconds();

private:
  long m_ns_timestamp;
  Precision m_precision;
};