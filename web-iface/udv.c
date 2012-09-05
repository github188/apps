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
	{"modify",		no_argument,		NULL,	'm'},
	{"old-name",		required_argument,	NULL,	'o'},
	{"new-name",		required_argument,	NULL,	'n'},
	{0, 0, 0, 0}

};

void udv_usage()
{
  printf(_T("\nsys-udv\n\n"));
  printf(_T("Usage: --list\n"));
  printf(_T("       --create --vg <vg_name> --name <udv_name> --capacity <size>\n"));
  printf(_T("       --delete <udv_name>\n"));
  printf(_T("       --modify --old-name <udv_name> --new-name <udv_name>\n"));
  printf(_T("\n\n"));
  exit(0);
}

enum {
	UDV_MODE_CREATE = 1,
	UDV_MODE_RENAME = 2,
	UDV_MODE_NONE
};

enum {
	MSG_OK = 1,
	MSG_ERROR
};

static int mode = UDV_MODE_NONE;	// for create & rename

// for create
static char vg_name[128] = {0};
static char udv_name[128] = {0};
static uint64_t capacity = 0;

// for rename
static char m_old_name[128] = {0};
static char m_new_name[128] = {0};

void return_json_msg(const int type, const char *msg)
{
	if (MSG_OK == type)
	{
		fprintf(stdout, "{\"status\":true, \"msg\":\"%s\"}\n", msg);
		exit(0);
	}
	else
	{
		fprintf(stdout, "{\"status\":false, \"msg\":\"%s\"}\n", msg);
		exit(-1);
	}
}

void list_udv()
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;

	char udv_type[128];

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<0)
		return_json_msg(MSG_ERROR, "获取用户数据卷失败!");

	udv = &list[0];

	puts("{");
	printf("\t\"total\":%d,\n", (int)udv_cnt);
	printf("\t\"rows\":");

	if (udv_cnt==0)
		printf("[");
	else
		puts("\n\t[");

	for (i=0; i<udv_cnt; i++)
	{
		if (udv->state==UDV_RAW)
			strcpy(udv_type, "raw");
		else if (udv->state==UDV_NAS)
			strcpy(udv_type, "nas");

		if (i+1==udv_cnt)
			printf("\n\t\t{\"name\":\"%s\", \"capacity\":%llu, \"state\":\"%s\"}",
					udv->name, (unsigned long long)udv->geom.capacity, udv_type);
		else
			printf("\n\t\t{\"name\":\"%s\", \"capacity\":%llu, \"state\":\"%s\"},",
					udv->name, (unsigned long long)udv->geom.capacity, udv_type);
		udv++;
	}

	if (udv_cnt==0)
		printf("]\n");
	else
		puts("\n\t]\n");
	puts("}");

	exit(0);
}

int udv_main(int argc, char *argv[])
{
	char c;

	//opterr = 0;  // 关闭错误提示
	while( (c=getopt_long(argc, argv, "", udv_options, NULL)) != -1 )
	{
		switch (c)
		{
			case 'l':  // --list
				list_udv(NULL);
				break;
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
			case '?':
			default:
				udv_usage();
				break;
		}
	}

	if (UDV_MODE_CREATE == mode)
	{
		if ( ! (vg_name[0] && udv_name[0] && capacity) )
			return_json_msg(MSG_ERROR, "创建用户数据卷参数错误!");

		if (udv_create(vg_name, udv_name, capacity) >= 0)
			return_json_msg(MSG_OK, "创建用数据卷成功!");
		return_json_msg(MSG_ERROR, "创建用户数据卷失败!");
	}
	else if (UDV_MODE_RENAME == mode)
	{
		if ( !(m_old_name[0] && m_new_name[0]) )
			return_json_msg(MSG_ERROR, "修改用户数据卷参数错误!");

		if (udv_rename(m_old_name, m_new_name) >= 0)
			return_json_msg(MSG_OK, "修改用户数据卷名称操作成功!");
		return_json_msg(MSG_ERROR, "修改用户数据卷名称操作失败!");
	}

	udv_usage();

	return 0;
}
