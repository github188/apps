#include <unistd.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>

#ifndef _SYS_LOG_H
#define _SYS_LOG_H

#define LOG_INVALID_ARG -1
#define LOG_FILE "/opt/log/jw-log.db"
#define LOG_TABLE "jwlog"
#define LOCAL_ADDR "/tmp/.log_socket_do_not_remove"


extern const char *_mod_name[];
extern const char *_mod_category[];
extern const char *_mod_event[];

static inline const char *_IntToStr(const char *name[], int value)
{
	int x = 0;
	while(name[x] != NULL)
	{
		if (x==value)
			return name[x];
		x++;
	}
	return "N/A";
}

static inline const int _StrToInt(const char *name[], const char *value)
{
	int x = 0;
	while(name[x] != NULL)
	{
		if (!strcmp(name[x], value))
			return x;
		x++;
	}
	return -1;
}


/*--------------------------------------------------------------------------- */

typedef enum _module log_module_e;
enum _module
{
	LOG_MOD_WEB = 0,
	LOG_MOD_DISK,
	LOG_MOD_VG,
	LOG_MOD_UDV,
	LOG_MOD_ISCSI,
	LOG_MOD_NAS,
	LOG_MOD_SYSCONF,
	LOG_MOD_UNKNOWN = -1
};

static inline const char *LogModuleStr(log_module_e module)
{
	return _IntToStr(_mod_name, module);
}

static inline const int LogModuleInt(const char *module)
{
	return _StrToInt(_mod_name, module);
}

/*--------------------------------------------------------------------------- */

typedef enum _category log_category_e;
enum _category
{
	LOG_CATG_AUTO = 0,
	LOG_CATG_MANUAL,
	LOG_CATG_UNKNOWN = -1
};

static inline const char *LogCategoryStr(log_category_e category)
{
	return _IntToStr(_mod_category, category);
}

static inline const int LogCategoryInt(const char *category)
{
	return _StrToInt(_mod_category, category);
}

/*--------------------------------------------------------------------------- */

typedef enum _event log_event_e;
enum _event
{
	LOG_EV_INFO = 0,
	LOG_EV_WARNING,
	LOG_EV_ERROR,
	LOG_EV_UNKNOWN = -1
};

static inline const char *LogEventStr(log_event_e event)
{
	return _IntToStr(_mod_event, event);
}

static inline const int LogEventInt(const char *event)
{
	return _StrToInt(_mod_event, event);
}

/*--------------------------------------------------------------------------- */

typedef struct _log_stru log_info_s;
struct _log_stru
{
	uint64_t idid;
	char datetime[32];
	char module[32];
	char category[32];
	char event[32];
	char content[1024];
};

#if 0
/*
 * 消息格式
 * -----------------------------
 *  请求: msg_request_t
 *  ----------------------------
 *  | 字段         | 长度（字节）|    取值            |
 *  | magic number |    4        |  0x915a925a        |
 *  | 记录获取模式 |    4        |  0x0001 - 指定范围 |
 *  |              |             |  0x0002 - 指定页   |
 *  |---------------指定页方式格式--------------------|
 *  | session id   |    4        |  32位无符号数      |
 *  | 页记录个数   |    4        |   1 ~ 最大记录数   |
 *  |---------------指定范围方式格式------------------|
 *  | 起始位置     |    8        |   1 ~ 最大记录数   |
 *  | 结束位置     |    8        |   1 ~ 最大记录数   |
 *
 * 返回: msg_response_t
 * -----------------------------
 *  | 字段         | 长度（字节）|    取值            |
 *  | magic number |    4        |  0x915a925a        |
 *  | 记录获取模式 |    4        |  0x0001 - 指定范围 |
 *  | 返回总个数   |    4        |                    |
 *  | 当前个数     |    4        |                    |
 *  | session id   |    4        |  32位无符号数      |
 *  | 记录编号     |    8        |  1 ~ 最大记录数    |
 *  | 日期时间     |    8        |  time_t            |
 *  | 模块         |    4        |  log_module_e      |
 *  | 类型         |    4        |  log_category_e    |
 *  | 事件         |    4        |  log_event_e       |
 *  | 内容长度     |    4        |                    |
 *  | 内容         |    x        |                    |
 */

#define LOG_MAGIC 0x915A925A
struct _msg_header
{
	uint32_t magic;		// 魔术字
	int req_mode;		// 记录获取模式
}

/* 请求报文格式 */
typedef struct _msg_request msg_request_t;
struct _msg_request
{
	struct _msg_header header;
#define magic header.magic
#define req_mode header.req_mode
	union {
		// 指定页方式请求
		struct {
			uint32_t session_id;	// 32位无符号数
			int page_size;		// 页记录个数
		}_page;

		// 指定范围方式请求
		struct {
			uint64_t start;		// 记录起始位置
			uint64_t end;		// 记录结束位置
		}_range;
	}_req;
#define mode_page _req._page
#define mode_range _req._range
#define session_id mode_page.session_id
#define page_size mode_page.page_size
#define start_rec mode_range.start
#define end_rec mode_range.end
};

/* 响应报文格式 */
typedef struct _msg_response msg_response_t;
struct _msg_response
{
	struct _msg_header header;
#define magic header.magic
#define req_mode header.req_mode
	uint32_t total;		// 返回记录总个数
	uint32_t curr;		// 当前记录个数
	uint32_t session_id;
	uint64_t rec_no;	// 记录编号
	time_t	datetime;	// 记录时间
	log_module_e module;	// 模块
	log_category_e category;	// 类型
	log_event_e event;	// 事件
	int content_length;	// 内容长度
	char content[0];	// 内容 (本地传输不考虑报文分片问题)
};
#endif

/* ---------------------------------------------------------------------------
 *   写日志消息格式
 * ---------------------------------------------------------------------------
 *   发送:
 *   --------------------------
 *   | 字段         | 长度（字节）|    取值            |
 *   | magic number |    4        |  0x915a925a        |
 *   | 模块         |    4        |  log_module_e      |
 *   | 类型         |    4        |  log_category_e    |
 *   | 事件         |    4        |  log_event_e       |
 *   | 内容长度     |    4        |                    |
 *   | 内容         |    x        |                    |
 *   | 模块         |    4        |                    |
 */

#define LOG_MAGIC 0x915A925A
struct _msg_header
{
	uint32_t magic;		// 魔术字
	int req_mode;		// 记录获取模式
};

enum
{
	LOG_REQ_WRITE = 1,
	LOG_REQ_UNKNOWN
};

#define MSG_HEADER_INIT(msg, req) \
	msg->magic = LOG_MAGIC; \
	msg->req_mode = req;

#define MSG_HEADER_CORRECT(msg) \
	(msg->magic == LOG_MAGIC)

typedef struct _msg_request msg_request_t;
struct _msg_request
{
	struct _msg_header header;
#define magic header.magic
#define req_mode header.req_mode
	log_module_e module;		// 模块
	log_category_e category;	// 类型
	log_event_e event;		// 事件
	int content_length;		// 内容长度
	char content[0];		// 内容 (本地传输不考虑报文分片问题)
};

/* -------------------------------------------------------------------------- */
/* Log Utils                                                                  */
/* -------------------------------------------------------------------------- */
bool log_db_exist();

bool log_db_create();

/* -------------------------------------------------------------------------- */
/*   API                                                                      */
/* -------------------------------------------------------------------------- */

/* 记录日志 */
/* 返回值不为0表示参数格式错误 */
int LogInsert(
		const char *module,	// 写入日志的模块
		const char *category,	// 日志类型
		const char *event,	// 日志事件
		const char *content	// 日志内容
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
