#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <sqlite3.h>

#include "log.h"

/* 记录日志 */
int LogInsert(
		const char *module,	// 写入日志的模块
		const char *category,	// 日志类型
		const char *event,	// 日志事件
		const char *content	// 日志内容
	)
{
        int sock_fd;
        struct sockaddr_un serv_addr;
        socklen_t addr_len;
	size_t msg_len;
	msg_request_t *msg;

        if ( (sock_fd=socket(AF_UNIX, SOCK_DGRAM, 0)) < 0)
		return -1;

        serv_addr.sun_family = AF_UNIX;
        strcpy(serv_addr.sun_path, LOCAL_ADDR);

	// 分配消息内存
	msg_len = sizeof(msg_request_t) + strlen(content) + 1;
	if (!(msg=(msg_request_t*)malloc(msg_len)))
	{
		close(sock_fd);
		return -1;
	}

	// 填充msg结构
	MSG_HEADER_INIT(msg, LOG_REQ_WRITE);
	msg->module = LogModuleInt(module);
	msg->category = LogCategoryInt(category);
	msg->event = LogEventInt(event);
	msg->content_length = strlen(content);
	strcpy(msg->content, content);

	// 发消息，不关心返回
        addr_len = strlen(serv_addr.sun_path) + sizeof(serv_addr.sun_family);
        sendto(sock_fd, (char*)msg, msg_len, 0,
                        (struct sockaddr*)&serv_addr, addr_len);

        close(sock_fd);
	free(msg);

        return 0;
}

/* 获取日志数量 */
ssize_t LogGetQuantity()
{
	sqlite3 *db;
	char *errmsg, **result;
	char sql_cmd[256];
	int col, row, pos;
	ssize_t ret = -1;

	if (SQLITE_OK != sqlite3_open_v2(LOG_FILE, &db, SQLITE_OPEN_READONLY, NULL))
		return -1;

	sprintf(sql_cmd, "SELECT count(id) FROM jwlog;");
	if (SQLITE_OK == sqlite3_get_table(db, sql_cmd, &result, &col, &row, &errmsg))
		ret = atol(result[col*row]);

	sqlite3_free_table(result);
	sqlite3_close(db);

	return ret;
}

typedef struct _session_info session_s;
struct _session_info {
	uint32_t session_id;	// SESSION ID
	int page_size;		// 每一页大小
	uint64_t last_rec;	// 上一次获取的最大记录编号
};

bool __update_session(session_s *session)
{
}

bool __session_get_info(session_s *session)
{
}

ssize_t __get_header_id()
{
	sqlite3 *db;
	char *errmsg, **result;
	char sql_cmd[256];
	int col, row;
	ssize_t ret = -1;

	if (SQLITE_OK != sqlite3_open_v2(LOG_FILE, &db, SQLITE_OPEN_READONLY, NULL))
		return ret;

	sprintf(sql_cmd, "SELECT min(id) FROM jwlog;");
	if (SQLITE_OK == sqlite3_get_table(db, sql_cmd, &result, &col, &row, &errmsg))
		ret = atol(result[col*row]);
	sqlite3_free_table(result);
	sqlite3_close(db);

	return ret;
}

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
	)
{
	sqlite3 *db;
	int col, row;
	char *errmsg, **result;
	char sql_cmd[256];

	session_s sess;
	uint64_t header_id;

#define ROW_MAX 6

	/*
	 * 支持两种查询方式
	 * 1. 页方式：指定session_id和页大小，页大小仅在第一次指定时生效
	 * 2. 范围方式：通过start,end指定获取记录的范围，此操作会尽量返回所满足的结果
	 */

	header_id = __get_header_id();

	if (session_id)
	{
		sess.session_id = session_id;

		/* 第一次创建Session */
		if (!__session_get_info(&sess))
		{
			if (page_size <= 0)
				return -1;
			sess.page_size = page_size;
			sess.last_rec = header_id;
			if (!__update_session(&sess))
				return -1;
		}

		/* Session已经存在 */
		sprintf(sql_cmd, "SELECT * FROM jwlog WHERE (id>=%llu and id<%llu);",
			sess.last_rec, sess.last_rec+sess.page_size);
		if (SQLITE_OK == sqlite3_get_table(db, sql_cmd, &result, &col, &row, &errmsg))
		{
			/*
			 * 10|2012-11-16 14:35:54|Web|Manual|Info|测试日志信息
			 */
			while(col>0)
			{
				log->idid = header_id - atoull(result[ROW_MAX*col]);
				col--;
			}
		}
	}
	else if(start>0 && end>start)
	{
	}

	sqlite3_free_table(result);
	sqlite3_close(db);

	return -1;
}
