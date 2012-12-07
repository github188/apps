/*
 * config-os.h: platform-specific code
 *
 * Copyright (C) 2012-2013 WISDATA, Inc. (yanyonggang@wisdata.com.cn)
 *
 */

#ifndef __WIS_CONFIG_OS_H_
#define __WIS_CONFIG_OS_H_

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef HAVE_STDBOOL_H
#  include <stdbool.h>
#else
#  ifndef HAVE__BOOL
#    ifdef __cplusplus
typedef bool _Bool;
#    else
#      define _Bool signed char
#    endif
#  endif
#  define bool _Bool
#  define false 0
#  define true  1
#  define __bool_true_false_are_defined 1
#endif

#ifdef HAVE_UNISTD_H
#  include <sys/types.h>
#  include <unistd.h>
#endif

#ifdef TIME_WITH_SYS_TIME
#  include <sys/time.h>
#  include <time.h>
#else
#  ifdef HAVE_SYS_TIME_H
#    include <sys/time.h>
#  else
#    include <time.h>
#  endif
#endif

#ifdef HAVE_STDINT_H
#  include <stdint.h>
#endif

#ifndef HAVE_U_CHAR
#  ifndef  __u_char_defined
#  define __u_char_defined
typedef unsigned char u_char;
typedef unsigned short u_short;
typedef unsigned int u_int;
typedef unsigned long u_long;
typedef unsigned long long u_longlong;
#  endif
#endif

#endif /* __WIS_CONFIG_OS_H_ */
