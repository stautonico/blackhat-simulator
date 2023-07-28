#include <blackhat/interpreter.h>

#include <iostream>
#include <stdexcept>
#include <utility>

static void my_fatal_handler(void *udata, const char *msg) {
  // TODO: Improve this
  (void)udata; /* ignored in this case, silence warning */
  fprintf(stderr, "*** FATAL ERROR: %s\n", (msg ? msg : "no message"));
  fflush(stderr);
  abort();
}

Blackhat::Interpreter::Interpreter(std::string code) {

  if (!m_ctx) {
    throw std::runtime_error("Failed to create Duktape heap");
  }

  m_code = std::move(code);

  void *my_udata = (void *)0xdeadbeef; // Idk what this is for

  m_ctx = duk_create_heap(NULL, NULL, NULL, my_udata, my_fatal_handler);
}
void Blackhat::Interpreter::_init_builtins() {
  duk_push_c_function(m_ctx, _print, 1);
  duk_put_global_string(m_ctx, "print");
  duk_push_c_function(m_ctx, _input, 1);
  duk_put_global_string(m_ctx, "input");
}
void Blackhat::Interpreter::run(const std::vector<std::string> &args) {
  _init_builtins();

  // Evaluate the code
  duk_eval_string_noresult(m_ctx, m_code.c_str());

  // Get the main function (should exist in all scripts)
  duk_get_global_string(m_ctx, "main");

  // Push the arguments to the stack (as an array)
  duk_idx_t arr_idx = duk_push_array(m_ctx);
  for (int i = 0; i < args.size(); i++) {
    duk_push_string(m_ctx, args[i].c_str());
    duk_put_prop_index(m_ctx, arr_idx, i);
  }

  // Call the main function with the arguments (1 argument, the array)
  duk_call(m_ctx, 1);

  duk_destroy_heap(m_ctx);
}

// Built-in functions
duk_ret_t Blackhat::Interpreter::_print(duk_context *ctx) {
  std::cout << duk_to_string(ctx, 0) << std::endl;
  return 0;
}
duk_ret_t Blackhat::Interpreter::_input(duk_context *ctx) {
  std::string prompt = duk_to_string(ctx, 0);
  std::string input;
  std::cout << prompt;
  std::getline(std::cin, input);
  duk_push_string(ctx, input.c_str());
  return 1;
}
