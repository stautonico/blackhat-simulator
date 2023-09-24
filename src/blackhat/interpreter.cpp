#include <blackhat/computer.h>
#include <blackhat/global_computer.h>
#include <blackhat/interpreter.h>
#include <blackhat/process.h>
#include <util/string.h>

#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>

Blackhat::Interpreter::Interpreter(std::string code, Process *process)
    : m_process(process) {
  m_vm = new pkpy::VM(false);
  m_code = std::move(code);
}

void Blackhat::Interpreter::_init_builtins() {
  m_vm->bind(m_vm->_main, "print(msg: str, newline:bool=true) -> None",
             [](VM *vm, ArgsView args) {
               auto msg = CAST(const char *, args[0]);
               auto newline = CAST(bool, args[1]);
//               this->_print(msg, newline);

               return vm->None;
             });
  // TODO: Redo for pocketpy
  //  duk_push_c_function(m_ctx, _print, DUK_VARARGS);
  //  duk_put_global_string(m_ctx, "print");
  //  duk_push_c_function(m_ctx, _input, 1);
  //  duk_put_global_string(m_ctx, "input");
  //  duk_push_c_function(m_ctx, _tmp_exec, DUK_VARARGS);
  //  duk_put_global_string(m_ctx, "exec");
  //  duk_push_c_function(m_ctx, _require, 1);
  //  duk_put_global_string(m_ctx, "require");
  //  duk_push_c_function(m_ctx, _read_file, 1);
  //  duk_put_global_string(m_ctx, "read");
  //  duk_push_c_function(m_ctx, _internal_get_env, 1);
  //  duk_put_global_string(m_ctx, "_internal_get_env");
  //  duk_push_c_function(m_ctx, _internal_set_env, 2);
  //  duk_put_global_string(m_ctx, "_internal_set_env");
  //  duk_push_c_function(m_ctx, _internal_readdir, 1);
  //  duk_put_global_string(m_ctx, "_internal_readdir");
}

int Blackhat::Interpreter::run(const std::vector<std::string> &args) {
  _init_builtins();

  // Evaluate the code
  //  duk_eval_string_noresult(m_ctx, m_code.c_str());
  //
  //  // Get the main function (should exist in all scripts)
  //  duk_get_global_string(m_ctx, "main");
  //
  //  // Push the arguments to the stack (as an array)
  //  duk_idx_t arr_idx = duk_push_array(m_ctx);
  //  for (int i = 0; i < args.size(); i++) {
  //    duk_push_string(m_ctx, args[i].c_str());
  //    duk_put_prop_index(m_ctx, arr_idx, i);
  //  }
  //
  //  // Call the main function with the arguments (1 argument, the array)
  //  duk_call(m_ctx, 1);
  //
  //  // Pop the return code from main
  //  int ret_code = duk_get_int(m_ctx, -1);
  //
  //  duk_destroy_heap(m_ctx);

  //  return ret_code;
  return 0;
}

// Built-in functions
void Blackhat::Interpreter::_print(std::string str, bool newline) {
  if (newline) {
    std::cout << str << std::endl;
  } else {
    std::cout << str;
  }
}

// duk_ret_t Blackhat::Interpreter::_print(duk_context *ctx) {
//   int n = duk_get_top(ctx);
//
//   duk_bool_t newline;
//
//   if (n == 0) {
//     return 0;
//   } else if (n == 1) {
//     newline = true;
//   } else {
//     newline = duk_get_boolean(ctx, 1);
//   }
//
//   auto str = duk_to_string(ctx, 0);
//
//   if (newline) {
//     std::cout << str << std::endl;
//   } else {
//     std::cout << str;
//   }
//
//   return 0;
// }

// duk_ret_t Blackhat::Interpreter::_input(duk_context *ctx) {
//   std::string prompt = duk_to_string(ctx, 0);
//   std::string input;
//   std::cout << prompt;
//   std::getline(std::cin, input);
//   duk_push_string(ctx, input.c_str());
//   return 1;
// }
//
// duk_ret_t Blackhat::Interpreter::_tmp_exec(duk_context *ctx) {
//   // Count the number of args
//   int nargs = duk_get_top(ctx);
//
//   // First args should be the path to the file
//   std::string cli = duk_to_string(ctx, 0);
//
//   auto args = split(cli, ' ');
//
//   std::string path = args[0];
//   // pop off the path
//   args.erase(args.begin());
//
//   g_computer.temporary_exec(path, args);
//
//   return 0;
// }
//
// duk_ret_t Blackhat::Interpreter::_require(duk_context *ctx) {
//   std::string module = duk_to_string(ctx, 0);
//   // Try to read the file from /lib/<module>.js
//   // If it doesn't exist, try to read it from /lib/<module>/<module>.js
//   // If it STILL doesn't exist, just throw an error
//
//   // TODO: Don't hardcode the .so extension
//   auto file = g_computer.temporary_read("/lib/" + module + ".so");
//   if (file.empty()) {
//     // If the module has a slash in the name, grab the last element
//     auto components = split(module, '/');
//     file = g_computer.temporary_read("/lib/" + module + ".so");
//     std::cout << "/lib/" + module + ".so" << std::endl;
//     if (file.empty()) {
//       duk_error(ctx, DUK_ERR_ERROR, "Module '%s' not found", module.c_str());
//     }
//   }
//
//   // Evaluate the code
//   duk_eval_string_noresult(ctx, file.c_str());
//
//   return 0;
// }
//
// duk_ret_t Blackhat::Interpreter::_read_file(duk_context *ctx) {
//   std::string path = duk_to_string(ctx, 0);
//   std::string file = g_computer.temporary_read(path);
//   duk_push_string(ctx, file.c_str());
//   return 1;
// }
//
// duk_ret_t Blackhat::Interpreter::_internal_get_env(duk_context *ctx) {
//   std::string key = duk_to_string(ctx, 0);
//
//   auto result = Interpreter::current->m_process->get_env(key);
//
//   duk_push_string(ctx, result.c_str());
//
//   return 1;
// }
//
// duk_ret_t Blackhat::Interpreter::_internal_set_env(duk_context *ctx) {
//   std::string key = duk_to_string(ctx, 0);
//   std::string value = duk_to_string(ctx, 1);
//
//   Interpreter::current->m_process->set_env(key, value);
//   return 0;
// }
//
// duk_ret_t Blackhat::Interpreter::_internal_readdir(duk_context *ctx) {
//   std::string path = duk_to_string(ctx, 0);
//
//   auto names = g_computer.temporary_readdir(path);
//
//   duk_idx_t arr_idx = duk_push_array(ctx);
//   for (int i = 0; i < names.size(); i++) {
//     duk_push_string(ctx, names[i].c_str());
//     duk_put_prop_index(ctx, arr_idx, i);
//   }
//
//   return 1;
// }