#pragma once

#include <optional>

#include <nlohmann/json.hpp>
using json = nlohmann::json;

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

  json serialize();

private:
  long m_ns_timestamp;
  Precision m_precision;
};