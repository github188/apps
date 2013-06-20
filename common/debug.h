/*
 * debug.h
 *
 * Copyright (C) 2012
 *
 * Date:	Thu Apr 19, 2012
 * Desc:	Provides the definition of debug routines.
 *
 */

#ifndef __COMMON_DEBUG_H_
#define __COMMON_DEBUG_H_

#include <assert.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>

#include "config.h"

__BEGIN_DECLS

void set_dbgstamp(bool stamp);
bool get_dbgstamp(void);

#ifdef NDEBUG
/* NDEBUG: turn off */
#define DBG_INSERT(...)		__ASSERT_VOID_CAST(0)
#define DBGP(fmt, ...)		__ASSERT_VOID_CAST(0)
#define DBGE(fmt, ...)		__ASSERT_VOID_CAST(0)
#define DBGVP(fmt, ...)		__ASSERT_VOID_CAST(0)
#define DBGVE(fmt, ...)		__ASSERT_VOID_CAST(0)
#else
#define DBG_INSERT(...)	__VA_ARGS__
#define DBGP(fmt, ...)	__dbg_fprintf(					\
				stderr, __FILE__, __func__, __LINE__,	\
				false, (fmt), ## __VA_ARGS__)
#define DBGVP(fmt, ap)	__dbg_vprintf(					\
				stderr, __FILE__, __func__, __LINE__,	\
				false, (fmt), (ap))
#define DBGE(fmt, ...)	__dbg_fprintf(					\
				stderr, __FILE__, __func__, __LINE__,	\
				true, (fmt), ## __VA_ARGS__)
#define DBGVE(fmt, ap)	__dbg_vprintf(					\
				stderr, __FILE__, __func__, __LINE__,	\
				true, (fmt), (ap))
#endif

void __dbg_vprintf(FILE *stream,
		   const char *file,
		   const char *func,
		   size_t line,
		   bool berr,
		   const char *fmt,
		   va_list ap);

static inline
void __dbg_fprintf(FILE *stream,
		   const char *file,
		   const char *func,
		   size_t line,
		   bool berr,
		   const char *fmt,
		   ...)
{
	va_list ap;

	va_start(ap, fmt);
	__dbg_vprintf(stream, file, func, line, berr, fmt, ap);
	va_end(ap);
}

__END_DECLS

#endif

