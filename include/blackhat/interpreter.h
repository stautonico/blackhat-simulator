#pragma once

#include <vendor/duktape/duktape.h>

#include <string>
#include <vector>

namespace Blackhat {

class Interpreter {
public:
  Interpreter(std::string code);

  int run(const std::vector<std::string> &args);

private:
  duk_context *m_ctx;

  std::vector<std::string> m_loaded_modules;

  std::string m_code;

  void _init_builtins();

  // Built-in functions
  static duk_ret_t _print(duk_context *ctx);
  static duk_ret_t _input(duk_context *ctx);
  static duk_ret_t _tmp_exec(duk_context *ctx);
};

} // namespace Blackhat
