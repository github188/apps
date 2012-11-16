#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "web-iface.h"
#include "common.h"

#include "../common/log.h"

struct option log_options[] = {
	{"insert",	no_argument,		NULL,	'i'},
	{"module",	required_argument,	NULL,	'm'},
	{"category",	required_argument,	NULL,	'c'},
	{"event",	required_argument,	NULL,	'v'},
	{"content",	required_argument,	NULL,	't'},
	{"get-quantity",no_argument,		NULL,	'q'},
	{"get",		no_argument,		NULL,	'g'},
	{"begin",	required_argument,	NULL,	'b'},
	{"end",		required_argument,	NULL,	'e'},
	{"get-next",	no_argument,		NULL,	'n'},
	{"amount-per-page",	required_argument,	NULL,	'p'},
	{"session-id",	required_argument,	NULL,	's'}
};

enum {
	MODE_INSERT = 1,
	MODE_GET,
	MODE_GET_NEXT,
	MODE_UNKNOWN
};

void log_usage()
{
	printf(_T("\nlog\n\n"));
	printf(_T("Usage: --insert --module <name> --category <auto|manual> --event <event_info> --content <content_text>\n"));
	printf(_T("       --get-quantity\n"));
	printf(_T("       --get --begin <rec_start> --end <rec_end>\n"));
	printf(_T("       --get-next --amount-per-page <num> --session-id <random_number>\n\n"));
	exit(-1);
}

/* 全局变量 */

// --insert
static char g_ins_module[128] = {0};
static char g_ins_category[128] = {0};
static char g_ins_event[128] = {0};
static char g_ins_content[128] = {0};

// --get
static uint64_t g_get_begin = -1;
static uint64_t g_get_end = -1;

// --get-next
static int g_per_page = -1;
static uint32_t g_session_id = -1;

// 模式定义
int mode = MODE_UNKNOWN;

#define _STR(x) (x[0]=='\0')

/* 记录一条日志 */
int log_insert()
{
	// 检查参数不能为空
	if ( _STR(g_ins_module) &&  _STR(g_ins_category) &&
		_STR(g_ins_event) && _STR(g_ins_content) )
	{
		if (LogInsert(g_ins_module, g_ins_category, g_ins_event, g_ins_content))
		{
			return_json_msg(MSG_ERROR, "日志参数不正确!请检查!");
			return -1;
		}
		return 0;
	}
	return_json_msg(MSG_ERROR, "参数不完整，请检查!");
	return -1;
}

/* 获取日志数量 */
int log_get_quantity()
{
	ssize_t q = LogGetQuantity();
	if (q<0)
		return_json_msg(MSG_ERROR, "获取日志数量失败!");
	fprintf(stdout, "{\"quantity\":%d}\n", (int)q);
	return 0;
}

void log_print(log_info_s *info, size_t num)
{
	int i;

	printf("{\n");
	printf("\t\"total\":%d,", (int)num);
	if (num>0)
		printf("\n\t\n\"rows\":[");
	else
		printf("\"rows\":[");

	for (i=0;i<num;i++)
	{
		if (i>0)
			printf(",");
		printf("\n\t\t{\"datetime\":\"%s\", \"module\":\"%s\", \"category\":\"%s\", \"event\":\"%s\", \"content\":\"%s\"",
				asctime(gmtime(&info[i].datetime)), LogModuleStr(info[i].module),
				LogCategoryStr(info[i].category), LogEventStr(info[i].event), info[i].content);
	}

	if (num>0)
		printf("\n\t]\n");
	else
		printf("]\n");
	printf("}\n");
}

/* 获取指定区间日志 */
int log_get()
{
	ssize_t q;
	log_info_s *info;

	if ( !( (g_get_begin!=-1) && (g_get_end!=-1) ) )
		return_json_msg(MSG_ERROR, "请输入获取日志的条目区间!");

	if (g_get_end >= g_get_begin)
		return_json_msg(MSG_ERROR, "获取日志记录的区间不正确!");

	if (!(info=(log_info_s*)malloc(sizeof(log_info_s)*(g_get_end-g_get_begin))))
		return_json_msg(MSG_ERROR, "可用内存不足!");

	q = LogGet(0, g_get_begin, g_get_end, 0, info);
	if (q<0)
	{
		free(info);
		return_json_msg(MSG_ERROR, "获取日志记录失败!");
	}

	// 输出日志内容
	log_print(info, q);
	free(info);

	return 0;
}

/* 获取一页日志 */
int log_get_next()
{
	return 0;
}

int log_main(int argc, char *argv[])
{
	char c;

	opterr = 0;	// 关闭系统函数库的错误提示
	while ( (c=getopt_long(argc, argv, "", log_options, NULL)) != -1 )
	{
		switch (c)
		{
		case 'i':	// --insert
			mode = MODE_INSERT;
			continue;
		case 'm':	// --module <>
			strcpy(g_ins_module, optarg);
			continue;
		case 'c':	// --category <>
			strcpy(g_ins_category, optarg);
			continue;
		case 'v':	// --event <>
			strcpy(g_ins_event, optarg);
			continue;
		case 't':	// --content <>
			strcpy(g_ins_content, optarg);
			continue;
		case 'q':	// --get-quantity
			return log_get_quantity();
		case 'g':	// --get
			mode = MODE_GET;
			continue;
		case 'b':	// --begin <>
			//g_get_begin = atoull(optarg);
			g_get_begin = (uint64_t)atol(optarg);
			continue;
		case 'e':	// --end <>
			//g_get_end = atoull(optarg);
			g_get_end = (uint64_t)atol(optarg);
			continue;
		case 'n':	// --get-next
			mode = MODE_GET_NEXT;
			continue;
		case 'p':	// --amount-per-page <>
			g_per_page = atoi(optarg);
			continue;
		case 's':	// --session-id <>
			//g_session_id = atoul(optarg);
			g_session_id = (uint32_t)atol(optarg);
			continue;
		case '?':
		default:
			log_usage();
			break;
		}
	}

	if (mode == MODE_INSERT)
		return log_insert();
	else if (mode == MODE_GET)
		return log_get();
	else if (mode == MODE_GET_NEXT)
		return log_get_next();

	log_usage();

	return 0;
}
