// #include <blackhat/computer.h>
// #include <blackhat/interpreter.h>
// #include <blackhat/process.h>
//
// #include <mutex>
//
// thread_local Blackhat::Interpreter* Blackhat::Interpreter::current = nullptr;
//
// int main() {
//
//   return 0;
// }

#include <pocketpy.h>

using namespace pkpy;

// https://pocketpy.dev/

int main() {
  // Create a virtual machine
  VM *vm = new VM(false); // Disable OS access

  // Hello world!
 vm->exec("def main():\n\tprint('hello world!')\n\treturn 0");

 auto obj = vm->eval("main()");

 std::cout << CAST(i64, obj) << std::endl;

//  PyObject* tp = vm->builtins->attr("dict");
//  PyObject* obj = vm->call(tp);	// this is a `dict`
//
//  vm->call_method(obj, "__setitem__", VAR("a"), VAR(5));
//
//  PyObject* ret = vm->call_method(obj, "__getitem__", VAR("a"));
//  std::cout << CAST(i64, ret) << std::endl;


  return 0;
  // Create a list
  vm->exec("a = [1, 2, 3]");

  // Eval the sum of the list
  PyObject *result = vm->eval("sum(a)");
  std::cout << CAST(int, result); // 6

  // Bindings
  vm->bind(vm->_main, "add(a: int, b: int)", [](VM *vm, ArgsView args) {
    int a = CAST(int, args[0]);
    int b = CAST(int, args[1]);
    return VAR(a + b);
  });

  // Call the function
  PyObject *f_add = vm->_main->attr("add");
  result = vm->call(f_add, VAR(3), VAR(7));
  std::cout << CAST(int, result); // 10

  // Dispose the virtual machine
  delete vm;
  return 0;
}