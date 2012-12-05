/*
 * debug.c
 *
 * Copyright (C) 2012 WISDATA Ltd. <yanyonggang@wisdata.com.cn>
 *
 * Date:	Thu Apr 19, 2012
 * Desc:	Provides the definition of debug routines.
 *
 */

#include <assert.h>
#include <errno.h>
#include <pthread.h>
#include <string.h>
#include <time.h>

#include "config-os.h"

#include "debug.h"

static bool bstamp = true;

void set_dbgstamp(bool stamp)
{
	bstamp = stamp;
}

bool get_dbgstamp()
{
	return bstamp;
}

void __dbg_vprintf(FILE *stream,
		   const char *file,
		   const char *func,
		   size_t line,
		   bool berr,
		   const char *fmt,
		   va_list ap)
{
	char buf[32];
	size_t i = 0;
	static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

	if(bstamp) {
		time_t now = time(NULL);
		struct tm now_tm;
		i = strftime(buf, 31,
			     "%h %e %T ",
			     localtime_r(&now, &now_tm));
	}
	buf[i] = '\0';

	/* lock write for multi-threads apps. */
	pthread_mutex_lock(&lock);

	fprintf(stream, "%s %s, %zu, %s: ", buf, file, line, func);
	vfprintf(stream, fmt, ap);
	if (berr) {
		fprintf(stream, ": %s\n", strerror(errno));
	} else if (*fmt) {
		/* append a LF if fmt's suffix is not LF */
		i = strlen(fmt);
		--i;	/* i is always positive */
		if (fmt[i] != '\n')
			fprintf(stream, "\n");
	}

	pthread_mutex_unlock(&lock);
}

/* eof */
