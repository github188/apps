#include <stdio.h>
#include <unistd.h>
#include <getopt.h>

#include "web-iface.h"
#include "common.h"

#include "../udv/libudv.h"

struct option udv_options[] = {
	{"create",		no_argument,		NULL,	'c'},
	{"vg",			required_argument,	NULL,	'v'},
	{"name",		required_argument,	NULL,	'u'},
	{"capacity",		required_argument,	NULL,	'p'},
	{"delete",		required_argument,	NULL,	'd'},
	{"list",		no_argument,		NULL,	'l'},
	{"iscsi",		no_argument,		NULL,	'I'},
	{"nas",			no_argument,		NULL,	'N'},
	{"raw",			no_argument,		NULL,	'R'},
	{"modify",		no_argument,		NULL,	'm'},
	{"old-name",		required_argument,	NULL,	'o'},
	{"new-name",		required_argument,	NULL,	'n'},
	{"remain-capacity",	no_argument,		NULL,	'r'},
	{"get-dev-byname",	required_argument,	NULL,	'a'},
	{"get-name-bydev",	required_argument,	NULL,	'e'},
	{"duplicate-check",	required_argument,	NULL,	'D'},
	{0, 0, 0, 0}

};

void udv_usage()
{
  printf(_T("\nsys-udv\n\n"));
  printf(_T("Usage: --list [ [--raw | --iscsi | --nas] | --name <udv_name> ]\n"));
  printf(_T("       --create --vg <vg_name> --name <udv_name> --capacity <size>\n"));
  printf(_T("       --delete <udv_name>\n"));
  printf(_T("       --modify --old-name <udv_name> --new-name <udv_name>\n"));
  printf(_T("       --remain-capacity --vg <vg_name>\n"));
  printf(_T("       --get-dev-byname <name>\n"));
  printf(_T("       --get-name-bydev <dev>\n"));
  printf(_T("       --duplicate-check <udv_name>\n"));
  printf(_T("\n\n"));
  exit(0);
}

enum {
	UDV_MODE_CREATE = 1,
	UDV_MODE_RENAME = 2,
	UDV_MODE_REMAIN = 3,
	UDV_MODE_LIST = 4,
	UDV_MODE_NONE
};


static int mode = UDV_MODE_NONE;	// for create & rename

// for create or remain
static char vg_name[128] = {0};
static char udv_name[128] = {0};
static uint64_t capacity = 0;

// for rename
static char m_old_name[128] = {0};
static char m_new_name[128] = {0};


typedef struct _list_type list_type_t;
struct _list_type{
	bool iscsi, nas, raw;
};

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

void list_udv(list_type_t t)
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;
	int printed = 0;

	char udv_state[128];
	bool print = false;

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	udv = &list[0];

	puts("{");
	printf("\t\"rows\":");

	if (udv_cnt==0)
		printf("[");
	else
		printf("\n\t[");

	for (i=0; i<udv_cnt; i++)
	{
		print = false;

		// 获取指定udv的信息优先级最高
		if (udv_name[0]!=0)
		{
			if (!strcmp(udv->name, udv_name))
				print = true;
			else
				print = false;
		}
		else if ( t.raw && (udv->state == UDV_RAW) )
			print = true;
		else if ( t.nas && (udv->state == UDV_NAS) )
			print = true;
		else if ( t.iscsi && (udv->state == UDV_ISCSI) )
			print = true;


		if (print)
		{
			__udv_set_state(udv_state, udv->state);

			if (printed==0)
				printf("\n\t\t{\"name\":\"%s\", \"capacity\":%llu, \"state\":\"%s\", \"vg\":\"%s\", \"combin\":\"%s|%llu\"}",
						udv->name, (unsigned long long)udv->geom.capacity, udv_state, udv->vg_name,
						udv->name, (unsigned long long)udv->geom.capacity);
			else
				printf(",\n\t\t{\"name\":\"%s\", \"capacity\":%llu, \"state\":\"%s\", \"vg\":\"%s\", \"combin\":\"%s|%llu\"}",
						udv->name, (unsigned long long)udv->geom.capacity, udv_state, udv->vg_name,
						udv->name, (unsigned long long)udv->geom.capacity);
			printed++;
		}
		udv++;
	}

	if (udv_cnt==0)
		puts("],");
	else
		puts("\n\t],");
	printf("\t\"total\":%d\n", printed);
	puts("}");

	exit(0);
}

int get_udv_remain()
{
	struct list list, *nn, *nt;
	ssize_t n;
	struct geom_stru *elem;

	uint64_t max_remain = 0,
		 max_single = 0;

	n = udv_get_free_list(vg_name, &list);
	if (n<0)
		return_json_msg(MSG_ERROR, "无法获取剩余空间!");
	else if (n==0)
		return printf("{\"vg\":\"%s\",\"max_avaliable\":0,\"max_single\":0}\n",
				vg_name);

	list_iterate_safe(nn, nt, &list)
	{
		elem = list_struct_base(nn, struct geom_stru, list);

		max_remain += elem->geom.capacity;

		if (max_single < elem->geom.capacity)
			max_single = elem->geom.capacity;
	}

	printf("{\"vg\":\"%s\",\"max_avaliable\":%llu,\"max_single\":%llu}\n",
			vg_name, (unsigned long long)max_remain, (unsigned long long)max_single);
	return 0;
}


// 通过udv设备名称获取udv名称
int get_name_bydev(const char *udv_dev)
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;

	if (!udv_dev)
		return_json_msg(MSG_ERROR, "用户数据卷设备名称无效!");

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	udv = &list[0];

	for (i=0; i<udv_cnt; i++)
	{
		if (!strcmp(udv->dev, udv_dev))
		{
			printf("{\"status\":true,\"udv_name\":\"%s\",\"udv_dev\":\"%s\"}\n",
				udv->name, udv->dev);
			return 0;
		}
		udv++;
	}

	return_json_msg(MSG_ERROR, "用户数据卷不存在!");
	return -1;
}


// 通过udv名称获取udv设备名称
int get_dev_byname(const char *udv_name)
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;

	if (!udv_name)
		return_json_msg(MSG_ERROR, "用户数据卷名称无效!");

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	udv = &list[0];

	for (i=0; i<udv_cnt; i++)
	{
		if (!strcmp(udv->name, udv_name))
		{
			printf("{\"status\":true,\"udv_name\":\"%s\",\"udv_dev\":\"%s\"}\n",
				udv->name, udv->dev);
			return 0;
		}
		udv++;
	}

	return_json_msg(MSG_ERROR, "用户数据卷不存在!");
	return -1;
}

int duplicate_check(const char *udv_name)
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;

	if (!udv_name)
		return_json_msg(MSG_ERROR, "用户数据卷名称无效!");

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	udv = &list[0];

	for (i=0; i<udv_cnt; i++)
	{
		if (!strcmp(udv->name, udv_name))
		{
			printf("{\"udv_name\":\"%s\",\"duplicate\":true}\n", udv_name);
			return 0;
		}
		udv++;
	}

	printf("{\"udv_name\":\"%s\",\"duplicate\":false}\n", udv_name);
	return 0;
}

void build_err_msg(int err_code, char *err_msg)
{
	if (!err_msg)
		return;
	switch(err_code)
	{
		case E_FMT_ERROR:
			sprintf(err_msg, "参数格式错误!");
			break;
		case E_VG_NONEXIST:
			sprintf(err_msg, "VG不存在!");
			break;
		case E_UDV_NONEXIST:
			sprintf(err_msg, "UDV不存在!");
			break;
		case E_VG_EXIST:
			sprintf(err_msg, "VG已经存在!");
			break;
		case E_UDV_EXIST:
			sprintf(err_msg, "UDV已经存在!");
			break;
		case E_SYS_ERROR:
			sprintf(err_msg, "系统调用出错!");
			break;
		case E_NO_FREE_SPACE:
			sprintf(err_msg, "可供使用的有效剩余空间不足!");
			break;
		case E_DEVICE_NOTMD:
			sprintf(err_msg, "设备类型不是VG设备!");
			break;
		default:
			sprintf(err_msg, "未知错误!");
			break;
	}
}

int udv_main(int argc, char *argv[])
{
	char c;
	list_type_t t;
	char err_msg[256];

	t.raw = t.iscsi = t.nas = false;

	//opterr = 0;  // 关闭错误提示
	while( (c=getopt_long(argc, argv, "", udv_options, NULL)) != -1 )
	{
		switch (c)
		{
			case 'l':  // --list
				mode = UDV_MODE_LIST;
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
			case 'd':  // --delete <udv_name>
				if (udv_delete(optarg)>=0)
					return_json_msg(MSG_OK, "删除用户数据卷成功!");
				else
					return_json_msg(MSG_ERROR, "删除用户数据卷失败!");
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
			case '?':
			default:
				udv_usage();
				break;
		}
	}

	if (UDV_MODE_CREATE == mode)
	{
		int ret = 0;
		if ( ! (vg_name[0] && udv_name[0] && capacity) )
			return_json_msg(MSG_ERROR, "创建用户数据卷参数错误!");

		if ((ret=udv_create(vg_name, udv_name, capacity)) >= 0)
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

	udv_usage();

	return 0;
}
