#include <blackhat/computer.h>
#include <blackhat/interpreter.h>
#include <blackhat/process.h>

#include <mutex>

thread_local Blackhat::Interpreter* Blackhat::Interpreter::current = nullptr;

int main() {

  return 0;
}