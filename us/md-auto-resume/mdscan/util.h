#ifndef K_UTIL_H
#define K_UTIL_H

#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <errno.h>

#ifdef DEBUG
#define DPR(x,...) fprintf(stderr, "[%s]: " x, __func__, ##__VA_ARGS__)
#else
#define DPR(x, ...) ((void)0)
#endif

#define xmalloc(sz)							\
({									\
	void *p = malloc(sz); 						\
	if (p == NULL) {						\
		fprintf(stderr, "%s:%d: Not enough memory for size %u\n", \
		        __FILE__, __LINE__, (unsigned int)(sz));		\
		exit(-ENOMEM);						\
	}								\
	p;								\
})
#define xfree(p) free(p)

#endif
