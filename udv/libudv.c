#include <Python.h>
#include <syslog.h>
#include <parted/parted.h>
#include "libudv.h"

/*
 * import from libpyext_udv.py
 */
size_t getVGDevByName(const char *vg_name, char *vg_dev)
{
	PyObject *pModule, *pFunc, *pArg, *pRetVal;

	if (!(vg_name && vg_dev))
		return PYEXT_ERR_INPUT_ARG;
	vg_dev[0] = '\0';

	Py_Initialize();
	if (!Py_IsInitialized())
		return PYEXT_ERR_INIT;

	pModule = pFunc = pArg = pRetVal = NULL;

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append('./')");
	PyRun_SimpleString("sys.path.append('/usr/local/bin')");

	if (!(pModule = PyImport_ImportModule("libpyext_udv")))
		return PYEXT_ERR_LOAD_MODULE;

	pFunc = PyObject_GetAttrString(pModule, "getVGDevByName");
	if(!PyCallable_Check(pFunc))
		return PYEXT_ERR_LOAD_FUNC;

	if (!(pArg = Py_BuildValue("(s)", vg_name)))
		return PYEXT_ERR_SET_ARG;

	if(!(pRetVal = PyObject_CallObject(pFunc, pArg)))
		return PYEXT_ERR_RUN;

	strcpy(vg_dev, PyString_AsString(pRetVal));

	return PYEXT_RET_OK;
}

size_t getVGNameByDev(const char *vg_dev, char *vg_name)
{
	PyObject *pModule, *pFunc, *pArg, *pRetVal;

	if (!(vg_name && vg_dev))
		return PYEXT_ERR_INPUT_ARG;
	vg_name[0] = '\0';

	Py_Initialize();
	if (!Py_IsInitialized())
		return PYEXT_ERR_INIT;

	pModule = pFunc = pArg = pRetVal = NULL;

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append('./')");
	PyRun_SimpleString("sys.path.append('/usr/local/bin')");

	if (!(pModule = PyImport_ImportModule("libpyext_udv")))
		return PYEXT_ERR_LOAD_MODULE;

	pFunc = PyObject_GetAttrString(pModule, "getVGNameByDev");
	if(!PyCallable_Check(pFunc))
		return PYEXT_ERR_LOAD_FUNC;

	if (!(pArg = Py_BuildValue("(s)", vg_dev)))
		return PYEXT_ERR_SET_ARG;

	if(!(pRetVal = PyObject_CallObject(pFunc, pArg)))
		return PYEXT_ERR_RUN;

	strcpy(vg_name, PyString_AsString(pRetVal));

	return PYEXT_RET_OK;
}

// python 函数返回值: True - 1, False - 0
/*
 * import from libpyext_udv.py
 */
int isISCSIVolume(const char *udv_dev)
{
	int ret = 1;
	PyObject *pModule, *pFunc, *pArg, *pRetVal;

	if (!udv_dev)
		return PYEXT_ERR_INPUT_ARG;

	Py_Initialize();
	if (!Py_IsInitialized())
		return PYEXT_ERR_INIT;

	pModule = pFunc = pArg = pRetVal = NULL;

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append('./')");
	PyRun_SimpleString("sys.path.append('/usr/local/bin')");

	if (!(pModule = PyImport_ImportModule("libpyext_udv")))
		return PYEXT_ERR_LOAD_MODULE;

	pFunc = PyObject_GetAttrString(pModule, "isISCSIVolume");
	if(!PyCallable_Check(pFunc))
		return PYEXT_ERR_LOAD_FUNC;

	if (!(pArg = Py_BuildValue("(s)", udv_dev)))
		return PYEXT_ERR_SET_ARG;

	if(!(pRetVal = PyObject_CallObject(pFunc, pArg)))
		return PYEXT_ERR_RUN;

	ret = PyInt_AsLong(pRetVal);

	// Clean up
	Py_DECREF(pModule);
	Py_DECREF(pFunc);

	Py_Finalize();

	return ret;
}

/*
 *  import from libnas.py
 */
int isNasVolume(const char *volume_name)
{
	int ret = 1;
	PyObject *pModule, *pFunc, *pArg, *pRetVal;

	if (!volume_name)
		return PYEXT_ERR_INPUT_ARG;

	Py_Initialize();
	if (!Py_IsInitialized())
		return PYEXT_ERR_INIT;

	pModule = pFunc = pArg = pRetVal = NULL;

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append('./')");
	PyRun_SimpleString("sys.path.append('/usr/local/bin')");

	if (!(pModule = PyImport_ImportModule("libnas")))
		return PYEXT_ERR_LOAD_MODULE;

	pFunc = PyObject_GetAttrString(pModule, "isNasVolume");
	if(!PyCallable_Check(pFunc))
		return PYEXT_ERR_LOAD_FUNC;

	if (!(pArg = Py_BuildValue("(s)", volume_name)))
		return PYEXT_ERR_SET_ARG;

	if(!(pRetVal = PyObject_CallObject(pFunc, pArg)))
		return PYEXT_ERR_RUN;

	ret = PyInt_AsLong(pRetVal);

	// Clean up
	Py_DECREF(pModule);
	Py_DECREF(pFunc);

	Py_Finalize();

	return ret;
}

static PedExceptionOption libudv_exception_handler(PedException *e)
{
	// TODO: 记录日志
	openlog("libudv", LOG_NDELAY|LOG_PID, LOG_USER);
	syslog(LOG_ERR, "exception: %s\n", e->message);
	closelog();
	return PED_EXCEPTION_OK;
}

void libudv_custom_init()
{
	// replace default exception handler
	ped_exception_set_handler(libudv_exception_handler);
}

PedDisk* _create_disk_label (PedDevice *dev, PedDiskType *type)
{
	PedDisk* disk = NULL;

	/* Create the label */
	disk = ped_disk_new_fresh (dev, type);
	if (!disk)
		return NULL;
	if (!ped_disk_commit(disk))
		return NULL;

	return disk;
}

#define _fix_4k(sector) ((uint64_t)((sector)/8*8))

ssize_t udv_force_init_vg(const char *vg_name)
{
	PedDevice *device = NULL;
	PedDisk *disk = NULL;
	PedConstraint *constraint;
	ssize_t ret_code = E_OK;
	char vg_dev[PATH_MAX];

	// 参数检查
	if (!vg_name)
		return E_FMT_ERROR;

	// 检查VG是否存在
	if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))
		return E_VG_NONEXIST;

	if (!(device = ped_device_get(vg_dev)))
		return E_SYS_ERROR;
	constraint = ped_constraint_any(device);

#ifndef _UDV_DEBUG
	// 检查是否为MD设备
	if (device->type != PED_DEVICE_MD)
		return E_DEVICE_NOTMD;
#else
	if (!strcmp(device->path, "/dev/sda"))
		return E_SYS_ERROR;
#endif

	disk = _create_disk_label(device, ped_disk_type_get("gpt"));
	if (!disk)
	{
		ret_code = E_SYS_ERROR;
		goto error;
	}

	ped_disk_destroy(disk);
error:
	ped_device_destroy(device);

	return ret_code;
}

/**
 * API
 */

ssize_t udv_create(const char *vg_dev, const char *name, 
					uint64_t start, uint64_t length)
{
	PedDevice *device = NULL;
	PedDisk *disk = NULL;
	PedPartition *part;
	PedConstraint *constraint;
	PedDiskType *type = NULL;

	ssize_t ret_code = E_OK;

	// 参数检查
	if (!name)
		return E_FMT_ERROR;

	// 检查用户数据卷是否存在
	if (get_udv_by_name(name))
		return E_UDV_EXIST;

	// 创建用户数据卷
	device = ped_device_get(vg_dev);
	if (!device) {
		//printf("load device error!\n");
		return E_SYS_ERROR;
	}
	constraint = ped_constraint_any(device);

#ifndef _UDV_DEBUG
	// 检查是否为MD设备
	if (device->type != PED_DEVICE_MD)
		return E_DEVICE_NOTMD;
#else
	if (!strcmp(device->path, "/dev/sda"))
		return E_SYS_ERROR;
#endif

	if ( (type = ped_disk_probe(device)) && !strcmp(type->name, "gpt") ) {
		disk = ped_disk_new(device);
	} else {
		//printf("old label!\n");
		disk = _create_disk_label(device, ped_disk_type_get("gpt"));
	}

	if (!disk) {
		ret_code = E_SYS_ERROR;
		//printf("get disk info error!\n");
		goto error;
	}

	if (start < 1024)
		start = 1024;
	else
		start = _fix_4k(start);

	length = _fix_4k(length);

	ret_code = E_NO_FREE_SPACE;
	for (part = ped_disk_next_partition(disk, NULL); part;
		part = ped_disk_next_partition(disk, part)) {

		if (part->type & PED_PARTITION_METADATA)
			continue;

		if (!(part->type & PED_PARTITION_FREESPACE))
			continue;

		if (start >= part->geom.start) {
			if (start <= part->geom.end) {
				if (start+length-1 <= part->geom.end) {
					part = ped_partition_new(disk, PED_PARTITION_NORMAL, NULL,
									start, start+length-1);
					ped_partition_set_name(part, name);
					ped_disk_add_partition(disk, part, constraint);
					ped_disk_commit(disk);
					ret_code = E_OK;
				}
				break;
			}
		}
	}

	ped_disk_destroy(disk);

error:
	ped_device_destroy(device);
	return ret_code;
}

void free_udv_list(struct list *list)
{
	struct list *n, *nt;
	udv_info_t *elem;

	if (!list_empty(list)) {
		list_iterate_safe(n, nt, list) {
			elem = list_struct_base(n, udv_info_t, list);
			free(elem);
		}
	}
}

ssize_t udv_get_part_list(const char *vg_dev, struct list *list, int type)
{
	PedDevice *device = NULL;
	PedDisk *disk = NULL;
	PedPartition *part;

	udv_info_t *udv_info;
	ssize_t ret_code = E_FMT_ERROR;

	if (!(vg_dev && list))
		return ret_code;

	device = ped_device_get(vg_dev);
	if (!device) {
		ret_code = E_SYS_ERROR;
		goto err_out;
	}

	if (ped_disk_probe(device) && (disk=ped_disk_new(device))) {
		if (!strcmp(disk->type->name, "gpt")) {
			ret_code = 0;
			for (part = ped_disk_next_partition(disk, NULL); part;
				part = ped_disk_next_partition(disk, part)) {
				if (part->type & PED_PARTITION_METADATA)
					continue;

				if (part->type & PED_PARTITION_FREESPACE) {
					if (UDV_PARTITION_USED == type)
						continue;
				} else {
					if (UDV_PARTITION_FREE == type)
						continue;
				}

				udv_info = (udv_info_t*)calloc(1, sizeof(udv_info_t));
				list_init(&udv_info->list);

				udv_info->part_used = !(part->type & PED_PARTITION_FREESPACE);
				if (udv_info->part_used) {
					strcpy(udv_info->name, ped_partition_get_name(part));
					udv_info->part_num = part->num;
					sprintf(udv_info->dev, "%sp%d", device->path, part->num);
				}
				udv_info->geom.start = part->geom.start;
				udv_info->geom.end = part->geom.end;
				udv_info->geom.length = part->geom.length;

				list_add(list, &udv_info->list);
				ret_code++;
			}
		}
	}

	if (disk)
		ped_disk_destroy(disk);
	ped_device_destroy(device);
err_out:
	return ret_code;
}

/**
 * @breif 删除指定名称的用户数据卷
 * @param name - 被删除用户数据卷名称
 * @return EINVAL - 参数错误
 *         ENODEV - 用户数据卷不存在
 *         EIO - 设置失败
 *         0 - 成功
 */
ssize_t udv_delete(const char *name)
{
	udv_info_t *udv;
	char vg_dev[32];

	PedDevice *device;
	PedDisk *disk;
	PedPartition *part;
	ssize_t retcode = E_OK;

	// 参数检查
	if (!name)
		return E_FMT_ERROR;

	// 查找UDV
	udv = get_udv_by_name(name);
	if (!udv)
		return E_UDV_NONEXIST;

	// 检查是否已经映射
	if (isISCSIVolume(udv->dev))
		return E_UDV_MOUNTED_ISCSI;
	if (isNasVolume(udv->name))
		return E_UDV_MOUNTED_NAS;

	// 删除分区
	strcpy(vg_dev, udv->dev);
	strtok(vg_dev, "p");
	device = ped_device_get(vg_dev);
	if (!device) {
		retcode = E_DEVNODE_NOT_EXIST;
		goto error_eio;
	}

	disk = ped_disk_new(device);
	if (!disk)
		goto error;

	part = ped_disk_get_partition(disk, udv->part_num);
	if (!part)
		goto error;

	if (!(ped_disk_delete_partition(disk, part) && ped_disk_commit(disk)))
		goto error;

	// 删除设备节点
	unlink(udv->dev);

error:
	ped_device_destroy(device);
error_eio:
	return retcode;
}

// 检查UDV名称是否存在
// 返回值：
//    udv_info_t* 存在，并且返回udv节点信息
//    NULL udb不存在
udv_info_t* get_udv_by_name(const char *name)
{
	PedDevice *dev = NULL;
	PedDisk *disk;
	PedPartition *part;
	PedDiskType *type = NULL;

	const char *part_name;
	static udv_info_t udv_info;

	ped_device_probe_all();

	while((dev=ped_device_get_next(dev))) {
#ifndef _UDV_DEBUG
		// 获取所有MD列表
		if (dev->type != PED_DEVICE_MD)
			continue;
#else
		if (!strcmp(dev->path, "/dev/sda"))
			continue;
#endif

		// 获取当前MD分区信息
		if ( (type = ped_disk_probe(dev)) && !strcmp(type->name, "gpt") )
			disk = ped_disk_new(dev);
		else
			disk = _create_disk_label(dev, ped_disk_type_get("gpt"));

		if (!disk)
			continue;

		for (part = ped_disk_next_partition(disk, NULL); part;
			part = ped_disk_next_partition(disk, part)) {

			if (part->type & PED_PARTITION_METADATA)
				continue;

			if (part->type & PED_PARTITION_FREESPACE)
				continue;

			part_name = ped_partition_get_name(part);
			if (part_name && !strcmp(part_name, name)) {
				strcpy(udv_info.name, part_name);
				udv_info.part_num = part->num;
				udv_info.geom.start = part->geom.start;
				udv_info.geom.end = part->geom.end;
				udv_info.geom.length = part->geom.length;
				sprintf(udv_info.dev, "%sp%d", dev->path, part->num);

				ped_disk_destroy(disk);
				return &udv_info;
			}
		}
		ped_disk_destroy(disk);
	}

	return NULL;
}

/**
 * @param name - 被修改用户数据卷名称 
 * @param new_name - 用户数据卷新名称
 * @return
 *      EINVAL - 参数错误
 *      ENODEV - 用户数据卷不存在
 *      EEXIST - 用户数据卷新名称存在
 *      EIO    - 设置失败
 *      0 - 成功
 */
ssize_t udv_rename(const char *name, const char *new_name)
{
	udv_info_t *udv;
	char vg_dev[32];

	PedDevice *device = NULL;
	PedDisk *disk;
	PedPartition *part;

	ssize_t ret_code = E_SYS_ERROR;

	// 参数检查
	if (!(name && new_name))
		return E_FMT_ERROR;

	// 被修改的名称确保存在
	udv = get_udv_by_name(name);
	if (!udv)
		return E_UDV_NONEXIST;

	// 修改的新名称确保不存在
	if (get_udv_by_name(new_name))
		return E_UDV_EXIST;

	// 修改名称
	strcpy(vg_dev, udv->dev);
	strtok(vg_dev, "p");
	device = ped_device_get(vg_dev);
	if (!device)
		return E_SYS_ERROR;

	disk = ped_disk_new(device);
	if (!disk)
		goto error;

	part = ped_disk_get_partition(disk, udv->part_num);
	if (!part)
		goto error_part;

	if (ped_partition_set_name(part, new_name) && ped_disk_commit(disk))
		ret_code = E_OK;

error_part:
	ped_disk_destroy(disk);
error:
	ped_device_destroy(device);
	return ret_code;
}

/**
 * Utils
 */
const char* vg_name2dev(const char *name)
{
	return NULL;
}

const char* vg_dev2name(const char *dev)
{
	return NULL;
}

const char* udv_name2dev(const char *name)
{
	return NULL;
}

const char* dev_dev2name(const char *dev)
{
	return NULL;
}
