#ifndef NFS_TEST_ALLOC_INL_H
#define NFS_TEST_ALLOC_INL_H

#include <stdlib.h>

#define ck_alloc(size) calloc(1, (size))
#define ck_realloc(ptr, size) realloc((ptr), (size))
#define ck_free(ptr) free((ptr))

#endif
