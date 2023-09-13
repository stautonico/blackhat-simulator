#pragma once

// Forward declaration
namespace Blackhat {
class Process;
}
// #include <blackhat/process.h>

#include <vendor/duktape/duktape.h>

#include <string>
#include <vector>

namespace Blackhat {


class Interpreter {
public:
  static thread_local Interpreter *current; // So that the builtins can access
                                            // the interpreter (duktape only
                                            // static functions)

  Interpreter(std::string code, Blackhat::Process *process);

  int run(const std::vector<std::string> &args);

private:
  Process *m_process;
  duk_context *m_ctx;

  std::vector<std::string> m_loaded_modules;

  std::string m_code;

  void _init_builtins();

  // Built-in functions
  static duk_ret_t _print(duk_context *ctx);
  static duk_ret_t _input(duk_context *ctx);
  static duk_ret_t _tmp_exec(duk_context *ctx);
  static duk_ret_t _require(duk_context *ctx);
  static duk_ret_t _read_file(duk_context *ctx);
  static duk_ret_t _internal_get_env(duk_context *ctx);
  static duk_ret_t _internal_set_env(duk_context *ctx);
};

} // namespace Blackhat
