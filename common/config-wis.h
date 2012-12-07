/*
 * config-wis.h: project config header file
 *
 * Copyright (C) 2012-2013 WISDATA, Inc. (yanyonggang@wisdata.com.cn)
 *
 */

#ifndef __WIS_CONFIG_WIS_H_
#define __WIS_CONFIG_WIS_H_

#ifdef __GNUC__
#include "config-gcc.h"
#endif

#ifndef __aligned
#define __aligned(x)
#endif

#ifndef __always_inline
#define __always_inline inline
#endif

/*
 * offsetof(TYPE, MEMBER)
 *  the offset of MEMBER of structure TYPE */
#ifndef offsetof
#ifdef __compiler_offsetof
#define offsetof(TYPE, MEMBER)	__compiler_offsetof(TYPE,MEMBER)
#else
#define offsetof(TYPE, MEMBER)	((size_t) &((TYPE*)0)->MEMBER)
#endif
#endif

#ifndef container_of
#define container_of(ptr, type, member)	\
	((type*)((char*)ptr - offsetof(type, member)))
#endif

/* prevent compiler warning */
#ifndef __WIS_UNUSED
#define __WIS_UNUSED(var)	((void)(var))
#endif

#ifndef __BEGIN_DECLS
#ifdef __END_DECLS
# undef __END_DECLS
#endif
#ifdef  __cplusplus
# define __BEGIN_DECLS  extern "C" {
# define __END_DECLS    }
#else
# define __BEGIN_DECLS
# define __END_DECLS
#endif
#endif

#endif /* __WIS_CONFIG_WIS_H_ */
