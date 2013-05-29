#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdint.h>
#include <stdbool.h>

#include "web-iface.h"
#include "common.h"

#include "../udv/libudv.h"

struct option udv_options[] = {
	{"create",		no_argument,		NULL,	'c'},
	{"vg",			required_argument,	NULL,	'v'},
	{"name",		required_argument,	NULL,	'u'},
	{"start",		required_argument,	NULL,	's'},
	{"capacity",		required_argument,	NULL,	'p'},
	{"delete",		required_argument,	NULL,	'd'},
	{"list",		no_argument,		NULL,	'l'},
	{"iscsi",		no_argument,		NULL,	'I'},
	{"nas",			no_argument,		NULL,	'N'},
	{"raw",			no_argument,		NULL,	'R'},
	{"part-list",	no_argument,		NULL,	'L'},
	{"modify",		no_argument,		NULL,	'm'},
	{"old-name",		required_argument,	NULL,	'o'},
	{"new-name",		required_argument,	NULL,	'n'},
	{"remain-capacity",	no_argument,		NULL,	'r'},
	{"get-dev-byname",	required_argument,	NULL,	'a'},
	{"get-name-bydev",	required_argument,	NULL,	'e'},
	{"duplicate-check",	required_argument,	NULL,	'D'},
	{"force-init-vg",	required_argument,	NULL,	'f'},
	{0, 0, 0, 0}

};

void udv_usage()
{
  printf(_T("\nsys-udv\n\n"));
  printf(_T("Usage: --list [[--raw | --iscsi | --nas] | --name <udv_name>] "
  		"[--vg <vg_name>]\n"));
  printf(_T("       --part-list --vg <vg_name>\n"));
  printf(_T("       --create --vg <vg_name> --name <udv_name> "
  		"--start <offset> --capacity <size>\n"));
  printf(_T("       --delete <udv_name>\n"));
  printf(_T("       --modify --old-name <udv_name> --new-name <udv_name>\n"));
  printf(_T("       --remain-capacity --vg <vg_name>\n"));
  printf(_T("       --get-dev-byname <name>\n"));
  printf(_T("       --get-name-bydev <dev>\n"));
  printf(_T("       --duplicate-check <udv_name>\n"));
  printf(_T("       --force-init-vg <vg_name>\n"));
  printf(_T("\n\n"));
  exit(0);
}

enum {
	UDV_MODE_CREATE = 1,
	UDV_MODE_RENAME = 2,
	UDV_MODE_REMAIN = 3,
	UDV_MODE_LIST = 4,
	UDV_MODE_PART_LIST = 5,
	UDV_MODE_NONE
};


static int mode = UDV_MODE_NONE;	// for create & rename

// for create or remain
static char vg_name[128] = {0};
static char udv_name[128] = {0};
static uint64_t capacity = 0;
static uint64_t start = 0;

// for rename
static char m_old_name[128] = {0};
static char m_new_name[128] = {0};

static char all_vg_dev[17][32];

typedef struct _list_type list_type_t;
struct _list_type{
	bool iscsi, nas, raw;
};

void build_err_msg(int err_code, char *err_msg)
{
	if (!err_msg)
		return;
	switch(err_code)
	{
		case E_OK:
			sprintf(err_msg, "操作成功!");
			break;
		case E_FMT_ERROR:
			sprintf(err_msg, "操作失败,参数格式错误!");
			break;
		case E_VG_NONEXIST:
			sprintf(err_msg, "操作失败,VG不存在!");
			break;
		case E_UDV_NONEXIST:
			sprintf(err_msg, "操作失败,UDV不存在!");
			break;
		case E_VG_EXIST:
			sprintf(err_msg, "操作失败,VG已经存在!");
			break;
		case E_UDV_EXIST:
			sprintf(err_msg, "操作失败,UDV已经存在!");
			break;
		case E_SYS_ERROR:
			sprintf(err_msg, "操作失败,系统调用出错!");
			break;
		case E_NO_FREE_SPACE:
			sprintf(err_msg, "操作失败,可供使用的有效剩余空间不足!");
			break;
		case E_DEVICE_NOTMD:
			sprintf(err_msg, "操作失败,设备类型不是VG设备!");
			break;
		case E_DEVNODE_NOT_EXIST:
			sprintf(err_msg, "操作失败,设备节点不存在!");
			break;
		case E_UDV_MOUNTED_ISCSI:
			sprintf(err_msg, "操作失败,用户数据卷已经被挂载为iSCSI卷!");
			break;
		case E_UDV_MOUNTED_NAS:
			sprintf(err_msg, "操作失败,用户数据卷已经被挂载为NAS卷!");
			break;
		default:
			sprintf(err_msg, "操作失败,未知错误!");
			break;
	}
}

static inline void __udv_set_state(char *udv_state_str, udv_state state)
{
	if (UDV_RAW == state)
		strcpy(udv_state_str, "raw");
	else if (UDV_ISCSI == state)
		strcpy(udv_state_str, "iscsi");
	else if (UDV_NAS == state)
		strcpy(udv_state_str, "nas");
	else
		strcpy(udv_state_str, "N/A");
}

void probe_all_vg()
{
	char buf[32];
	int i = 0;
	FILE *fp;

	all_vg_dev[0][0] = '\0';
	fp = popen("ls /sys/block | grep md[0-9]", "r");
	if (!fp)
		return;

	while (fgets(buf, sizeof(buf), fp)) {
		if (buf[strlen(buf)-1] == '\n')
			buf[strlen(buf)-1] = '\0';
		sprintf(all_vg_dev[i], "/dev/%s",  buf);
		++i;
		if (i >= sizeof(all_vg_dev)/sizeof(all_vg_dev[0]))
			break;
	}
	pclose(fp);
	all_vg_dev[i][0] = '\0';
}

void list_udv(list_type_t t)
{
	struct list list, *n, *nt;
	udv_info_t *udv_info;
	
	ssize_t udv_cnt;
	char vg_dev[32];
	char udv_state[16];
	int i = 0, rows = 0; 
	int first_print = 1, finished = 0;

	// 输入udv_name时, 忽略vg_name
	if (vg_name[0] != '\0' && udv_name[0] == '\0') {
		if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))		
			return_json_msg(MSG_ERROR, "卷组不存在");
		strcpy(all_vg_dev[0], vg_dev);
		all_vg_dev[1][0] = '\0';
	} else {
		probe_all_vg();
	}
	
	printf("{\n");
	printf("\t\"rows\":\n");
	printf("\t[\n");

	for (; !finished && all_vg_dev[i][0] != '\0'; i++) {
		list_init(&list);

		// 获取已使用的分区
		udv_cnt = udv_get_part_list(all_vg_dev[i], &list, UDV_PARTITION_USED);
		if (udv_cnt <= 0)
			continue;

		getVGNameByDev(all_vg_dev[i], vg_name);
		list_iterate_safe(n, nt, &list)	{
			udv_info = list_struct_base(n, udv_info_t, list);

			if (udv_name[0] != '\0') {
				if (!strcmp(udv_name, udv_info->name))
					finished = 1;
				else
					continue;

			} else if (isISCSIVolume(udv_info->dev)) {
				if (!t.iscsi)
					continue;

				udv_info->state = UDV_ISCSI;
			} else if(isNasVolume(udv_info->name)) {
				if (!t.nas)
					continue;

				udv_info->state = UDV_NAS;
			} else {
				if (!t.raw)
					continue;

				udv_info->state = UDV_RAW;
			}
			
			__udv_set_state(udv_state, udv_info->state);

			if (first_print)
				first_print = 0;
			else
				printf(",\n");
		
			printf("\t\t"
				"{\"name\":\"%s\", \"capacity\":%llu, \"state\":\"%s\", "
				"\"vg\":\"%s\", \"combin\":\"%s|%llu\", \"dev\":\"%s\"}",
				udv_info->name, (unsigned long long)udv_info->geom.length*512,
				udv_state, vg_name, udv_info->name,
				(unsigned long long)udv_info->geom.length*512, udv_info->dev);

			++rows;

			if (finished)
				break;
		}

		free_udv_list(&list);
	}

	printf("\n\t],\n");
	printf("\t\"total\":%d\n", rows);
	printf("}\n");

	exit(0);
}

void list_part(const char *vg_name)
{
	struct list list, *n, *nt;
	udv_info_t *udv_info;
	
	ssize_t udv_cnt;
	uint64_t capacity = 0;
	char vg_dev[32];
	int first_print = 1, rows = 0;

	list_init(&list);
	
	// 检查VG是否存在
	if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))		
		return_json_msg(MSG_ERROR, "卷组不存在");
	
	// 获取所有分区
	udv_cnt = udv_get_part_list(vg_dev, &list, UDV_PARTITION_ALL);
	if (udv_cnt <= 0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	printf("{\n");
	printf("\t\"rows\":\n");
	printf("\t[\n");

	list_iterate_safe(n, nt, &list)	{
		udv_info = list_struct_base(n, udv_info_t, list);
	
		// 不显示小于100M的空闲空间
		if (!udv_info->part_used && udv_info->geom.length < 204800)
			continue;

		if (first_print)
			first_print = 0;
		else
			printf(",\n");

		printf("\t\t{\"start\": %llu, \"end\": %llu, \"len\": %llu, "
			"\"name\":\"%s\", \"stat\":\"%s\"}",
			udv_info->geom.start*512, udv_info->geom.end*512,
			udv_info->geom.length*512, udv_info->name,
			udv_info->part_used ? "used" : "free");

		++rows;
		capacity += udv_info->geom.length*512;
	}

	printf("\n\t],\n");
	printf("\t\"total\":%d,\n", rows);
	printf("\t\"capacity\":%llu\n", capacity);
	printf("}\n");

	free_udv_list(&list);
	exit(0);
}

int get_udv_remain()
{
	struct list list, *nn, *nt;
	ssize_t n;
	udv_info_t *udv_info;
	char vg_dev[PATH_MAX];

	uint64_t max_remain = 0, max_single = 0;
	char err_msg[256];

	// 检查VG是否存在
	if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))
		return E_VG_NONEXIST;

	list_init(&list);
	n = udv_get_part_list(vg_dev, &list, UDV_PARTITION_FREE);
	if (n < 0) {
		build_err_msg(n, err_msg);
		return_json_msg(MSG_ERROR, err_msg);
	}

	list_iterate_safe(nn, nt, &list) {
		udv_info = list_struct_base(nn, udv_info_t, list);
		max_remain += udv_info->geom.length;
		if (max_single < udv_info->geom.length)
			max_single = udv_info->geom.length;
	}

	max_remain *= 512;
	max_single *= 512;
	printf("{\"vg\":\"%s\",\"max_avaliable\":%llu,\"max_single\":%llu}\n",
		vg_name, (unsigned long long)max_remain, (unsigned long long)max_single);

	free_udv_list(&list);
	return 0;
}


// 通过udv设备名称获取udv名称
int get_name_bydev(const char *udv_dev)
{
	struct list list, *nn, *nt;
	ssize_t n;
	udv_info_t *udv_info;
	char vg_dev[32];
	char err_msg[256];
	int find = 0;

	if (!udv_dev)
		return_json_msg(MSG_ERROR, "用户数据卷设备名称无效!");

	strcpy(vg_dev, udv_dev);
	strtok(vg_dev, "p");

	list_init(&list);
	n = udv_get_part_list(vg_dev, &list, UDV_PARTITION_USED);
	if (n < 0) {
		build_err_msg(n, err_msg);
		return_json_msg(MSG_ERROR, err_msg);
	}

	list_iterate_safe(nn, nt, &list) {
		udv_info = list_struct_base(nn, udv_info_t, list);
		if (!strcmp(udv_info->dev, udv_dev)) {
			printf("{\"status\":true,\"udv_name\":\"%s\",\"udv_dev\":\"%s\"}\n",
				udv_info->name, udv_info->dev);

			find = 1;
			break;
		}
	}
	free_udv_list(&list);

	if (find)
		return 0;

	return_json_msg(MSG_ERROR, "用户数据卷不存在!");
	return -1;
}


// 通过udv名称获取udv设备名称
int get_dev_byname(const char *udv_name)
{
	struct list list, *n, *nt;
	udv_info_t *udv_info;
	
	ssize_t udv_cnt;
	int i = 0;
	int find = 0;

	if (!udv_name)
		return_json_msg(MSG_ERROR, "用户数据卷名称无效!");

	probe_all_vg();
	for (; !find && all_vg_dev[i][0] != '\0'; i++) {
		list_init(&list);

		// 获取已使用的分区
		udv_cnt = udv_get_part_list(all_vg_dev[i], &list, UDV_PARTITION_USED);
		if (udv_cnt <= 0)
			continue;

		list_iterate_safe(n, nt, &list)	{
			udv_info = list_struct_base(n, udv_info_t, list);
			if (!strcmp(udv_info->name, udv_name)) {
				printf("{\"status\":true,\"udv_name\":\"%s\","
					"\"udv_dev\":\"%s\"}\n",
					udv_info->name, udv_info->dev);

				find = 1;
				break;
			}
		}

		free_udv_list(&list);
	}

	if (find)
		return 0;

	return_json_msg(MSG_ERROR, "用户数据卷不存在!");
	return -1;
}

int duplicate_check(const char *udv_name)
{
	struct list list, *n, *nt;
	udv_info_t *udv_info;
	
	ssize_t udv_cnt;
	int i = 0;
	int find = 0;

	if (!udv_name)
		return_json_msg(MSG_ERROR, "用户数据卷名称无效!");

	probe_all_vg();
	for (; !find && all_vg_dev[i][0] != '\0'; i++) {
		list_init(&list);

		// 获取已使用的分区
		udv_cnt = udv_get_part_list(all_vg_dev[i], &list, UDV_PARTITION_USED);
		if (udv_cnt <= 0)
			continue;

		list_iterate_safe(n, nt, &list)	{
			udv_info = list_struct_base(n, udv_info_t, list);
			if (!strcmp(udv_info->name, udv_name)) {
				printf("{\"udv_name\":\"%s\",\"duplicate\":true}\n", udv_name);
				find = 1;
				break;
			}
		}

		free_udv_list(&list);
	}

	if (find)
		return 0;

	printf("{\"udv_name\":\"%s\",\"duplicate\":false}\n", udv_name);
	return 0;
}

int force_init_vg(const char *vg)
{
	ssize_t ret = udv_force_init_vg(vg);
	char _msg[128] = {0};

	if (0 != ret) {
		build_err_msg(ret, _msg);
		printf("{\"status\":\"false\", "
			"\"msg\":\"卷组强制初始化失败!%s\"}\n", _msg);
	} else{
		printf("{\"status\":\"true\", "
			"\"msg\":\"卷组强制初始化成功!\"}\n");
	}

	return ret;
}


int udv_main(int argc, char *argv[])
{
	char c;
	list_type_t t;
	char err_msg[256] = {0};
	char _tmp[512];
	ssize_t _ret;

	t.raw = t.iscsi = t.nas = false;

	libudv_custom_init();

	//opterr = 0;  // 关闭错误提示
	while( (c=getopt_long(argc, argv, "", udv_options, NULL)) != -1 )
	{
		switch (c)
		{
			case 'l':  // --list
				mode = UDV_MODE_LIST;
				continue;
			case 'L':  // --part-list
				mode = UDV_MODE_PART_LIST;
				continue;
			case 'c':  // --create
				mode = UDV_MODE_CREATE;
				continue;
			case 'v':  // --vg <vg_name>
				strcpy(vg_name, optarg);
				continue;
			case 'u':  // --name <udv_name>
				strcpy(udv_name, optarg);
				continue;
			case 'p':  // --capacity <size>
				capacity = atoll(optarg);
				continue;
			case 's':  // --start <offset>
				start = atoll(optarg);
				continue;
			case 'd':  // --delete <udv_name>
				_ret = udv_delete(optarg);
				build_err_msg(_ret, err_msg);
				sprintf(_tmp, "删除用户数据卷 %s : %s", optarg, err_msg);
				if (_ret>=0)
					return_json_msg(MSG_OK, _tmp);
				else
					return_json_msg(MSG_ERROR, _tmp);
				break;
			case 'm':
				mode = UDV_MODE_RENAME;
				break;
			case 'o':
				strcpy(m_old_name, optarg);
				break;
			case 'n':
				strcpy(m_new_name, optarg);
				break;
			case 'r':
				mode = UDV_MODE_REMAIN;
				break;
			case 'a':
				return get_dev_byname(optarg);
			case 'e':
				return get_name_bydev(optarg);
			case 'D':	// --duplicate-chcek <udv_name>
				return duplicate_check(optarg);
			case 'I':	// --iscsi
				t.iscsi = true;
				continue;
			case 'R':	// --raw
				t.raw = true;
				continue;
			case 'N':	// --nas
				t.nas = true;
				continue;
			case 'f':	// --force-init-vg
				return force_init_vg(optarg);
			case '?':
			default:
				udv_usage();
				break;
		}
	}

	if (UDV_MODE_CREATE == mode)
	{
		int ret = 0;
		char vg_dev[32];
		if ( ! (vg_name[0] && udv_name[0] && capacity) )
			return_json_msg(MSG_ERROR, "创建用户数据卷参数错误!");
		
		// 检查VG是否存在
		if (PYEXT_RET_OK != getVGDevByName(vg_name, vg_dev))
			return_json_msg(MSG_ERROR, "输入的卷组不存在!");

		if (0 == start)
			return_json_msg(MSG_ERROR, "输入的起始位置错误!");
		
		if ((ret=udv_create(vg_dev, udv_name, start/512, capacity/512)) >= 0)
			return_json_msg(MSG_OK, "创建用数据卷成功!");
		build_err_msg(ret, err_msg);
		return_json_msg(MSG_ERROR, err_msg);
	}
	else if (UDV_MODE_RENAME == mode)
	{
		if ( !(m_old_name[0] && m_new_name[0]) )
			return_json_msg(MSG_ERROR, "修改用户数据卷参数错误!");

		if (udv_rename(m_old_name, m_new_name) >= 0)
			return_json_msg(MSG_OK, "修改用户数据卷名称操作成功!");
		return_json_msg(MSG_ERROR, "修改用户数据卷名称操作失败!");
	}
	else if (UDV_MODE_REMAIN == mode)
	{
		if (vg_name[0] == '\0')
			return_json_msg(MSG_ERROR, "请输入卷组名称!");
		return get_udv_remain();
	}
	else if (UDV_MODE_LIST == mode)
	{
		// 三个参数都不设置，则显示所有类型的分区
		if ( !t.raw && !t.iscsi && !t.nas )
			t.raw = t.iscsi = t.nas = true;
		list_udv(t);
	}
	else if (UDV_MODE_PART_LIST == mode)
	{
		if (vg_name[0] == '\0')
			return_json_msg(MSG_ERROR, "请输入卷组名称!");
		list_part(vg_name);
	}

	udv_usage();

	return 0;
}
