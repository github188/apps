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
	{"remain-capacity",	required_argument,	NULL,	'r'},
	{"get-dev-byname",	required_argument,	NULL,	'a'},
	{"get-name-bydev",	required_argument,	NULL,	'e'},
	{"duplicate-check",	required_argument,	NULL,	'D'},
	{"force-init-vg",	required_argument,	NULL,	'f'},
	{0, 0, 0, 0}

};

void udv_usage()
{
	printf(_T("\n"));
	printf(_T("Usage: --list [[--raw | --iscsi | --nas] | --name <udv_name>] "
			"[--vg <vg_name>]\n"));
	printf(_T("       --part-list --vg <vg_name>\n"));
	printf(_T("       --create --vg <vg_name> --name <udv_name> "
			"--start <offset> --capacity <size>\n"));
	printf(_T("       --delete <udv_name>\n"));
	printf(_T("       --modify --old-name <udv_name> --new-name <udv_name>\n"));
	printf(_T("       --remain-capacity <vg_dev>\n"));
	printf(_T("       --get-dev-byname <udv_name>\n"));
	printf(_T("       --get-name-bydev <udv_dev>\n"));
	printf(_T("       --duplicate-check <udv_name>\n"));
	printf(_T("       --force-init-vg <vg_dev>\n"));
	printf(_T("\n"));
	exit(0);
}

enum {
	UDV_MODE_CREATE,
	UDV_MODE_RENAME,
	UDV_MODE_DELETE,
	UDV_MODE_REMAIN,
	UDV_MODE_FORCE_INIT,
	UDV_MODE_PART_LIST,
	UDV_MODE_NONE
};

static int mode = UDV_MODE_NONE;	// for create & rename

// for create or remain
static char vg_name[128] = {0};
static char vg_dev[32] = {0};
static char udv_name[128] = {0};
static uint64_t capacity = 0;
static uint64_t start = 0;

// for rename
static char m_old_name[128] = {0};
static char m_new_name[128] = {0};

static char all_vg_dev[17][32];

void build_err_msg(int err_code, char *err_msg)
{
	if (!err_msg)
		return;
	switch(err_code) {
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

#define RAID_DIR_BYNAME "/tmp/.raid-info/by-name"
int get_vgdev_byname(const char *vg_name, char *vg_dev)
{
	FILE *fp;
	char tmp_path[256];
	char buf[32] = { 0 };

	sprintf(tmp_path, "%s/%s", RAID_DIR_BYNAME, vg_name);
	fp = fopen(tmp_path, "r");
	if (!fp)
		return E_VG_NONEXIST;

	fgets(buf, 32, fp);
	fclose(fp);
	sprintf(vg_dev, "/dev/%s", buf);
	return E_OK;
}

void list_part(const char *vg_name)
{
	struct list list, *n, *nt;
	udv_info_t *udv_info;
	
	ssize_t udv_cnt;
	uint64_t capacity = 0;
	char vg_dev[32];
	int first_print = 1, rows = 0;
	int ret = E_OK;
	char err_msg[256];

	list_init(&list);
	
	// 检查VG是否存在
	ret = get_vgdev_byname(vg_name, vg_dev);
	if (ret != E_OK)		
		goto error_out;
	
	// 获取所有分区
	udv_cnt = udv_get_part_list(vg_dev, &list, UDV_PARTITION_ALL);
	if (udv_cnt <= 0) {
		ret = udv_cnt;
		goto error_out;
	}

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
			udv_info->geom.start<1024 ? 1024*512 : udv_info->geom.start*512,
			udv_info->geom.end*512, udv_info->geom.length*512, udv_info->name,
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

error_out:
	build_err_msg(ret, err_msg);
	exit_json_msg(MSG_ERROR, err_msg);
}

void get_vg_remain(const char *vg_dev)
{
	struct list list, *nn, *nt;
	ssize_t n;
	udv_info_t *udv_info;

	uint64_t max_remain = 0, max_single = 0;
	char err_msg[256];

	list_init(&list);
	n = udv_get_part_list(vg_dev, &list, UDV_PARTITION_FREE);
	if (n < 0) {
		build_err_msg(n, err_msg);
		exit_json_msg(MSG_ERROR, err_msg);
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
	exit(0);
}

int udv_main(int argc, char *argv[])
{
	char c;
	char err_msg[256] = { 0 };
	int ret = 0;

	libudv_custom_init();

	//opterr = 0;  // 关闭错误提示
	while((c=getopt_long(argc, argv, "", udv_options, NULL)) != -1) {
		switch (c) {
		case 'L':  // --part-list
			mode = UDV_MODE_PART_LIST;
			break;
		case 'c':  // --create
			mode = UDV_MODE_CREATE;
			break;
		case 'v':  // --vg <vg_name>
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(vg_name, optarg);
			break;
		case 'u':  // --name <udv_name>
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(udv_name, optarg);
			break;
		case 'p':  // --capacity <size>
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				capacity = atoll(optarg);
			break;
		case 's':  // --start <offset>
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				start = atoll(optarg);
			break;
		case 'd':  // --delete <udv_name>
			mode = UDV_MODE_DELETE;
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(udv_name, optarg);
			break;
		case 'm':
			mode = UDV_MODE_RENAME;
			break;
		case 'o':
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(m_old_name, optarg);
			break;
		case 'n':
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(m_new_name, optarg);
			break;
		case 'r':
			mode = UDV_MODE_REMAIN;
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(vg_dev, optarg);
			break;
		case 'f':
			mode = UDV_MODE_FORCE_INIT;
			if (strlen(optarg) == 0)
				ret = E_FMT_ERROR;
			else
				strcpy(vg_dev, optarg);
			break;
		case 'l':	// --list
		case 'a':	// --get_dev_byname
		case 'e':	// --get_name_bydev
		case 'D':	// --duplicate-chcek
			return exec_new_cmd(argc, argv);
		case '?':
		default:
			udv_usage();
			break;
		}

		if (ret != 0) {
			build_err_msg(ret, err_msg);
			exit_json_msg(ret==E_OK ? MSG_OK : MSG_ERROR, err_msg);
		}
	}

	// 需要输出信息的函数，自己输出正常或错误信息，退出程序
	// 其他函数通过返回值统一输出操作结果
	if (UDV_MODE_CREATE == mode) {
		char vg_dev[32];
		
		// 检查VG是否存在
		ret = get_vgdev_byname(vg_name, vg_dev);
		if (ret != E_OK)
			build_err_msg(ret, err_msg);
			exit_json_msg(ret==E_OK ? MSG_OK : MSG_ERROR, err_msg);

		if (0 == start)
			exit_json_msg(MSG_ERROR, "输入的起始位置错误!");

		ret = udv_create(vg_dev, udv_name, start/512, capacity/512);

	} else if (UDV_MODE_RENAME == mode) {
		ret = udv_rename(m_old_name, m_new_name);
	}
	else if (UDV_MODE_DELETE == mode) {
		ret = udv_delete(udv_name);
		
	} else if (UDV_MODE_FORCE_INIT == mode) {
		ret = udv_force_init_vg(vg_dev);

	} else if (UDV_MODE_REMAIN == mode) {
		get_vg_remain(vg_dev);
		
	} else if (UDV_MODE_PART_LIST == mode) {
		list_part(vg_name);

	} else {
		udv_usage();
	}

	build_err_msg(ret, err_msg);
	exit_json_msg(ret==E_OK ? MSG_OK : MSG_ERROR, err_msg);

	return 0;
}
