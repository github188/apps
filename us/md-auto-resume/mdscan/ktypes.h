#ifndef K_COMPILER_H
#define K_COMPILER_H

#include <stdint.h>
#include <stddef.h>

#ifdef _MSC_VER
#define inline __inline
#endif

#ifdef __GNUC__
#define PACKED __attribute__((packed))
#define likely(x)	__builtin_expect(!!(x), 1)
#define unlikely(x)	__builtin_expect(!!(x), 0)
#else
#define PACKED
#define likely(x)   (x)
#define unlikely(x) (x)
#endif

#ifdef WIN32
#define __LITTLE_ENDIAN 1234
#define __BIG_ENDIAN    4321
/* This line should change for particular machine */
#define BYTE_ORDER __LITTLE_ENDIAN
#define EXPORT __declspec(dllexport)
#define BUG() ((void)0)
#else
#include <endian.h>
#define EXPORT
#include <stdio.h>
#define BUG() \
	fprintf(stderr, "%s: found bug @%d\n", __FUNCTION__, __LINE__)
#endif

typedef uint16_t le16;
typedef uint16_t be16;
typedef uint32_t le32;
typedef uint32_t be32;
typedef uint64_t le64;
typedef uint64_t be64;

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

#define ARRAY_SZ(array) (sizeof(array) / sizeof(array[0]))

static inline uint16_t swap_16(uint16_t x)
{
	return x << 8 | x >> 8;
}
static inline uint32_t swap_32(uint32_t x)
{
	return x << 24 | x >> 24 |
		(x & (uint32_t)0x0000FF00UL) << 8 |
		(x & (uint32_t)0x00FF0000UL) >> 8;
}
static inline uint64_t swap_64(uint64_t x)
{
	return x << 56 | x >> 56 |
                (x & (uint64_t)0x000000000000ff00ULL) << 40 |
                (x & (uint64_t)0x0000000000ff0000ULL) << 24 |
                (x & (uint64_t)0x00000000ff000000ULL) << 8  |
                (x & (uint64_t)0x000000ff00000000ULL) >> 8  |
                (x & (uint64_t)0x0000ff0000000000ULL) >> 24 |
                (x & (uint64_t)0x00ff000000000000ULL) >> 40;
}

#if BYTE_ORDER == __LITTLE_ENDIAN
#define cpu_to_le16(x) ((le16)x)
#define cpu_to_le32(x) ((le32)x)
#define cpu_to_le64(x) ((le64)x)
#define le16_to_cpu(x) ((uint16_t)x)
#define le32_to_cpu(x) ((uint32_t)x)
#define le64_to_cpu(x) ((uint64_t)x)

#define cpu_to_be16(x) ((be16)swap_16(x))
#define cpu_to_be32(x) ((be32)swap_32(x))
#define cpu_to_be64(x) ((be64)swap_64(x))
#define be16_to_cpu(x) ((uint16_t)swap_16(x))
#define be32_to_cpu(x) ((uint32_t)swap_32(x))
#define be64_to_cpu(x) ((uint64_t)swap_64(x))
#else

#define cpu_to_le16(x) ((le16)swap_16(x))
#define cpu_to_le32(x) ((le32)swap_32(x))
#define cpu_to_le64(x) ((le64)swap_64(x))
#define le16_to_cpu(x) ((uint16_t)swap_16(x))
#define le32_to_cpu(x) ((uint32_t)swap_32(x))
#define le64_to_cpu(x) ((uint64_t)swap_64(x))

#define cpu_to_be16(x) ((be16)x)
#define cpu_to_be32(x) ((be32)x)
#define cpu_to_be64(x) ((be64)x)
#define be16_to_cpu(x) ((uint16_t)x)
#define be32_to_cpu(x) ((uint32_t)x)
#define be64_to_cpu(x) ((uint64_t)x)

#endif /* if BYTE_ORDER == __LITTLE_ENDIAN */

#ifndef _STDDEF_H
#define offsetof(type, member) ((size_t) &((type *)0)->member)
#endif

#define container_of(ptr, type, member) \
	((type *)((char *)(ptr) - offsetof(type, member)))

#endif
