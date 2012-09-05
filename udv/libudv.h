#include <errno.h>
#include <stdio.h>
#include <limits.h>	// for PATH_MAX
#include <stdint.h>
#include <stdbool.h>
#include "list.h"

#ifndef _LIB_UDV_H
#define _lib_UDV_H

/**
 * Defination
 */

#define MAX_UDV 10

/* Error Code */
enum {
	E_OK = 0,
	E_FMT_ERROR = -1,
	E_VG_NONEXIST = -2,
	E_UDV_NONEXIST = -3,
	E_VG_EXIST = -4,
	E_UDV_EXIST = -5,
	E_SYS_ERROR = -6,
	E_NO_FREE_SPACE = -7,
	E_DEVICE_NOTMD = -8
};

typedef enum _udv_state udv_state;
enum _udv_state {
        UDV_RAW = 0,
        UDV_ISCSI,
        UDV_NAS
};

// 用户数据卷容量信息
typedef struct _udv_geom udv_geom;
struct _udv_geom {
        uint64_t start, end, capacity;
};

typedef struct _udv_info udv_info_t;

#define UDV_NAME_LEN 72
struct _udv_info {
        char name[UDV_NAME_LEN];
        char vg_dev[PATH_MAX];
        int part_num;
        udv_geom geom;
        uint32_t sector_size;   // not used currently
        udv_state state;
};

struct geom_stru {
        struct list list;
        udv_geom geom;
};

/**
 * API
 */

ssize_t udv_create(const char *vg_name, const char *name, uint64_t capacity);

ssize_t udv_delete(const char *name);

size_t udv_list(udv_info_t *list, size_t n);

ssize_t udv_rename(const char *name, const char *new_name);

/**
 * Utils
 */
bool udv_exist(const char *name);

const char* vg_name2dev(const char *name);

const char* vg_dev2name(const char *dev);

const char* udv_name2dev(const char *name);

const char* dev_dev2name(const char *dev);

udv_info_t* get_udv_by_name(const char *name);

ssize_t get_udv_free_list(const char *vg_name, struct list *list);

void free_geom_list(struct list *list);

#endif/*_LIB_UDV_H*/
