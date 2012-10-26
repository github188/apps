#include <Python.h>
#include <parted/parted.h>
#include "libudv.h"

const static int DFT_SECTOR_SIZE = 512;

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

PedDisk*
_create_disk_label (PedDevice *dev, PedDiskType *type)
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

/**
 * API
 */

ssize_t udv_create(const char *vg_name, const char *name, uint64_t capacity)
{
        PedDevice *device = NULL;
        PedDisk *disk = NULL;
        PedPartition *part;
        PedConstraint *constraint;
	PedDiskType *type = NULL;

	struct list list, *n, *nt;
	struct geom_stru *elem;

	ssize_t ret_code = E_OK;
	char vg_dev[PATH_MAX];

        // 参数检查
        if (!name)
                return E_FMT_ERROR;

        // 检查VG是否存在
	if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))
		return E_VG_NONEXIST;

        // 检查用户数据卷是否存在
        if (get_udv_by_name(name))
                return E_UDV_EXIST;

	// 检查空闲空间
	if ( udv_get_free_list(vg_name, &list) <= 0 )
		return E_NO_FREE_SPACE;

        // 创建用户数据卷
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

	if ( (type = ped_disk_probe(device)) && !strcmp(type->name, "gpt") )
		disk = ped_disk_new(device);
	else
		disk = _create_disk_label(device, ped_disk_type_get("gpt"));

	if (!disk)
	{
		ret_code = E_SYS_ERROR;
		goto error;
	}

	list_iterate_safe(n, nt, &list)
	{
		elem = list_struct_base(n, struct geom_stru, list);
		if (elem->geom.capacity >= capacity)
		{
			part = ped_partition_new(disk, PED_PARTITION_NORMAL,
				NULL,
				(elem->geom.start/DFT_SECTOR_SIZE),
				(uint64_t)((elem->geom.start + capacity)/DFT_SECTOR_SIZE));

			ped_partition_set_name(part, name);
			ped_disk_add_partition(disk, part, constraint);
			ped_disk_commit(disk);
			ret_code = E_OK;
			break;
		}
		ret_code = E_NO_FREE_SPACE;
	}

	free_geom_list(&list);
	ped_disk_destroy(disk);
error:
        ped_device_destroy(device);
	return ret_code;
}

void free_geom_list(struct list *list)
{
        struct list *n, *nt;
        struct geom_stru *elem;

        if (!list_empty(list))
        {
                list_iterate_safe(n, nt, list)
                {
                        elem = list_struct_base(n, struct geom_stru, list);
                        free(elem);
                }
        }
}

ssize_t udv_get_free_list(const char *vg_name, struct list *list)
{
        PedDevice *device = NULL;
        PedDisk *disk = NULL;
        PedPartition *part;

        struct geom_stru *gs;
	ssize_t ret_code = E_FMT_ERROR;
	udv_geom last_geom = { 0, 0, 0 };
	uint64_t end_pos = 0;
	char vg_dev[PATH_MAX];

        if ( !(vg_name && list) )
                return ret_code;

        // 检查VG是否存在
	if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))
		return E_VG_NONEXIST;

        list_init(list);

        if ( !(device = ped_device_get(vg_dev)) )
	{
		ret_code = E_SYS_ERROR;
                goto err_out;
	}
	end_pos = device->length * device->sector_size - 1;

	if ( ped_disk_probe(device) && (disk=ped_disk_new(device)) )
	{
		if (!strcmp(disk->type->name, "gpt"))
		{

			for (part = ped_disk_next_partition(disk, NULL); part;
					part = ped_disk_next_partition(disk, part) )
			{
				if (part->num < 0)
					continue;

				gs = (struct geom_stru*)malloc(sizeof(struct geom_stru));
				gs->geom.start = last_geom.end;
				gs->geom.end = part->geom.start * DFT_SECTOR_SIZE - 1;
				gs->geom.capacity = gs->geom.end - gs->geom.start + 1;
				list_add(list, &gs->list);

				last_geom.end = (part->geom.end+1) * DFT_SECTOR_SIZE;

				if (ret_code<0)
					ret_code = 0;
				ret_code++;
			}
		}
	}

	if (last_geom.end < end_pos)
	{
		gs = (struct geom_stru*)malloc(sizeof(struct geom_stru));

		gs->geom.start = last_geom.end;
		gs->geom.end = end_pos;
		gs->geom.capacity = gs->geom.end - gs->geom.start + 1;

		list_add(list, &gs->list);

		if (ret_code < 0)
			ret_code = 1;
		else
			ret_code++;
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

        PedDevice *device;
        PedDisk *disk;
        PedPartition *part;

        // 参数检查
        if (!name)
                return E_FMT_ERROR;

	// 检查是否已经映射
	if (isISCSIVolume(name) || isNasVolume(name))
		return E_UDV_MOUNTED;

        // 查找UDV
        if (!(udv=get_udv_by_name(name)))
                return E_UDV_NONEXIST;

        // 删除分区
        if (!(device = ped_device_get(udv->vg_dev)))
                goto error_eio;

        if (!(disk = ped_disk_new(device)))
                goto error;

        if (!(part = ped_disk_get_partition(disk, udv->part_num)))
                goto error;

        if (ped_disk_delete_partition(disk, part) &&
                ped_disk_commit(disk))
                goto success;

success:
        return E_OK;
error:
        ped_device_destroy(device);
error_eio:
        return E_SYS_ERROR;
}

size_t udv_list(udv_info_t *list, size_t n)
{
        size_t udv_cnt = 0;

        PedDevice *dev = NULL;
        PedDisk *disk;
        PedPartition *part;

        const char *part_name;
        udv_info_t *udv = list;

        ped_device_probe_all();

        while((dev=ped_device_get_next(dev)))
        {
#ifndef _UDV_DEBUG
                // 获取所有MD列表
		if (dev->type != PED_DEVICE_MD)
			continue;
#else
		if (!strcmp(dev->path, "/dev/sda"))
			continue;
#endif

                // 获取当前MD分区信息
		if ( !ped_disk_probe(dev) || !(disk=ped_disk_new(dev)) )
			continue;

                for (part=ped_disk_next_partition(disk, NULL); part;
                                part=ped_disk_next_partition(disk, part))
                {
                        if (part->num < 0) continue;

                        part_name = ped_partition_get_name(part);
                        if (!part_name) continue;

                        if (udv_cnt >= n)
                                break;

                        strcpy(udv->name, part_name);

			if (dev->type == PED_DEVICE_MD)
				sprintf(udv->dev, "%sp%d", dev->path, part->num);
			else
				sprintf(udv->dev, "%s%d", dev->path, part->num);

                        strcpy(udv->vg_dev, dev->path);
                        udv->part_num = part->num;

                        udv->geom.start = part->geom.start * DFT_SECTOR_SIZE;
                        udv->geom.capacity = part->geom.length * DFT_SECTOR_SIZE;
                        udv->geom.end = udv->geom.start + udv->geom.capacity - 1;

			if (isISCSIVolume(udv->dev))
				udv->state = UDV_ISCSI;
			else if (isNasVolume(udv->name))
				udv->state = UDV_NAS;
			else
				udv->state = UDV_RAW;

                        udv_cnt++; udv++;
                }
                ped_disk_destroy(disk);
        }

        return udv_cnt;
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

        const char *part_name;
        static udv_info_t udv_info;
        udv_info_t *udv = NULL;

        ped_device_probe_all();

        while((dev=ped_device_get_next(dev)))
        {
#ifndef _UDV_DEBUG
                // 获取所有MD列表
                if (dev->type != PED_DEVICE_MD)
                        continue;
#else
		if (!strcmp(dev->path, "/dev/sda"))
			continue;
#endif

                // 获取当前MD分区信息
                if ( !(disk=ped_disk_new(dev)) )
			continue;

                for (part=ped_disk_next_partition(disk, NULL); part;
                                part=ped_disk_next_partition(disk, part))
                {
                        if (part->num < 0) continue;

                        part_name = ped_partition_get_name(part);
                        if ( part_name && !strcmp(part_name, name) )
                        {
                                udv = &udv_info;
                                strcpy(udv->name, part_name);
                                strcpy(udv->vg_dev, dev->path);
                                udv->part_num = part->num;

                                udv->geom.start = part->geom.start * DFT_SECTOR_SIZE;
                                udv->geom.capacity = part->geom.length * DFT_SECTOR_SIZE;
                                udv->geom.end = udv->geom.start + udv->geom.capacity - 1;

                                // TODO: udv->state;
				udv->state = UDV_RAW; // for debug

				ped_disk_destroy(disk);
				return udv;

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

        PedDevice *device = NULL;
        PedDisk *disk;
        PedPartition *part;

	ssize_t ret_code = E_SYS_ERROR;

        // 参数检查
        if (!(name && new_name))
                return E_FMT_ERROR;

	// 被修改的名称确保存在
	if (!(udv=get_udv_by_name(name)))
		return E_UDV_NONEXIST;

	// 修改的新名称确保不存在
	if (get_udv_by_name(new_name))
		return E_UDV_EXIST;

        // 修改名称
        if (!(device = ped_device_get(udv->vg_dev)))
                return E_SYS_ERROR;

        if (!(disk = ped_disk_new(device)))
                goto error;

        if (!(part = ped_disk_get_partition(disk, udv->part_num)))
                goto error_part;

        if (ped_partition_set_name(part, new_name) &&
                ped_disk_commit(disk))
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
