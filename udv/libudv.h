#include <errno.h>
#include <stdio.h>
#include <limits.h>	// for PATH_MAX
#include <stdint.h>
#include <stdbool.h>
#include "list.h"

#ifndef _LIB_UDV_H
#define _lib_UDV_H

//#define ALIGN_BEGIN_SECT 1024
#define ALIGN_BEGIN_SECT 0

/**
 * Defination
 */

#define MAX_UDV 128

/* Error code for c call py */
enum {
	PYEXT_RET_OK = 0,
	PYEXT_ERR_INPUT_ARG,
	PYEXT_ERR_INIT,
	PYEXT_ERR_LOAD_MODULE,
	PYEXT_ERR_LOAD_FUNC,
	PYEXT_ERR_SET_ARG,
	PYEXT_ERR_NORESULT,
	PYEXT_ERR_RUN
};

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
	E_DEVICE_NOTMD = -8,
	E_DEVNODE_NOT_EXIST = -9,
	E_UDV_MOUNTED_ISCSI = -10,
	E_UDV_MOUNTED_NAS = -11
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
	char dev[UDV_NAME_LEN];
        char vg_dev[PATH_MAX];
	char vg_name[PATH_MAX];
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

ssize_t udv_force_init_vg(const char *vg_name);

size_t getVGDev_ByName(const char *vg_name, char *vg_dev);

int isISCSIVolume(const char *udv_dev);

int isNasVolume(const char *volume_name);

ssize_t udv_get_free_list(const char *vg_name, struct list *list);

/**
 * Utils
 */
bool udv_exist(const char *name);

const char* vg_name2dev(const char *name);

const char* vg_dev2name(const char *dev);

const char* udv_name2dev(const char *name);

const char* dev_dev2name(const char *dev);

udv_info_t* get_udv_by_name(const char *name);


void free_geom_list(struct list *list);

#endif/*_LIB_UDV_H*/
