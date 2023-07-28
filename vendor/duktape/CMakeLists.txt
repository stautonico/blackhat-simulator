# Compile duktape as a static library

set(DUKTAPE_SOURCES duktape.c)

add_library(duktape STATIC ${DUKTAPE_SOURCES})