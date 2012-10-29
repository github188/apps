#include <unistd.h>
#include <stdint.h>
#include <time.h>

#ifndef _SYS_LOG_H
#define _SYS_LOG_H

#define LOG_INVALID_ARG -1

typedef enum _module log_module_e;
enum _module
{
	LOG_MOD_UNKNOWN = 0,
	LOG_MOD_WEB,
	LOG_MOD_DISK,
	LOG_MOD_VG,
	LOG_MOD_UDV,
	LOG_MOD_ISCSI,
	LOG_MOD_NAS,
	LOG_MOD_SYSCONF
};

typedef enum _category log_category_e;
enum _category
{
	LOG_CATG_AUTO = 1,
	LOG_CATG_MANUAL
};

typedef enum _event log_event_e;
enum _event
{
	LOG_INFO = 1,
	LOG_WARNING,
	LOG_ERROR
};

typedef struct _log_stru log_info_s;
struct _log_stru
{
	time_t datetime;
	log_module_e module;
	log_category_e category;
	log_event_e event;
	char content[1024];
};

/* 记录日志 */
void LogInsert(
		log_module_e module,		// 写入日志的模块
		log_category_e category,	// 日志类型
		log_event_e event,		// 日志事件
		const char *content		// 日志内容
	);

/* 获取日志数量 */
ssize_t LogGetQuantity();

/* 获取日志
 * session_id 为0时，不关心page_size大小
 * 请求的start,end之差要小于log能存储的记录个数，否则会发生越界
 */
ssize_t LogGet(
	uint32_t session_id,
	uint64_t start,
	uint64_t end,
	int page_size,
	log_info_s *log
	);

#endif/*_SYS_LOG_H*/
