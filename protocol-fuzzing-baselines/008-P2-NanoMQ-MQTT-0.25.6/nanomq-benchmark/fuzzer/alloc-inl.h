#ifndef MQTT_BENCHMARK_ALLOC_STUB_H
#define MQTT_BENCHMARK_ALLOC_STUB_H
#include <stdlib.h>
#define ck_alloc(size) calloc(1, (size))
#define ck_realloc(ptr, size) realloc((ptr), (size))
#define ck_free(ptr) free((ptr))
#endif
