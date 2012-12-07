#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/fcntl.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <sqlite3.h>
#include <limits.h>

#include "log.h"

/* 记录日志 */
int LogInsert(
		const char *user,	// 用户名，供web接口使用
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
	if (user)
		strcpy(msg->user, user);
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

static inline const char *__session_file(uint32_t session_id)
{
	static char file_name[PATH_MAX];

	sprintf(file_name, "/tmp/.log/session-%.8x", session_id);
	return file_name;
}

#define LOG_DEFAULT_PAGE_SIZE 30

uint64_t __get_header_id()
{
	sqlite3 *db;
	char *errmsg, **result;
	char sql_cmd[256];
	int col, row;
	uint64_t ret = 0;

	if (SQLITE_OK != sqlite3_open_v2(LOG_FILE, &db, SQLITE_OPEN_READONLY, NULL))
		return ret;

	sprintf(sql_cmd, "SELECT min(id) FROM jwlog;");
	if (SQLITE_OK == sqlite3_get_table(db, sql_cmd, &result, &col, &row, &errmsg))
		ret = atol(result[col*row]);
	sqlite3_free_table(result);
	sqlite3_close(db);

	return ret;
}

/*
 * 更新指定SESSION的信息，不存在则创建
 */
bool __session_update(session_s *sess)
{
	int fd;
	const char *fname = __session_file(sess->session_id);

	if (access(fname, R_OK | W_OK))
	{
		// 文件不存在，设置默认值
		if ( (fd=open(fname, O_CREAT | O_RDWR, S_IRUSR|S_IWUSR)) <= 0)
			return false;
		/*
		bzero(sess, sizeof(sess));
		sess->page_size = LOG_DEFAULT_PAGE_SIZE;
		sess->last_rec = __get_header_id();
		*/
	}
	else
	{
		if ((fd=open(fname, O_RDWR)) <= 0)
			return false;
	}

	write(fd, sess, sizeof(session_s));
	close(fd);
	return true;
}

/*
 * 获取指定SESSION ID的信息，不存在则返回NULL
 */
bool __session_info(session_s *sess)
{
	int fd;
	const char *fname = __session_file(sess->session_id);

	if (access(fname, R_OK | W_OK))
		return false;

	if ((fd=open(fname, O_RDONLY)) <= 0)
		return false;
	read(fd, sess, sizeof(session_s));
	close(fd);
	return true;
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
	int col, row, i;
	char *errmsg, **result;
	char sql_cmd[256];
	ssize_t rec_num = 0;

	session_s sess;
	uint64_t header_id;

#define ROW_MAX 6

	/*
	 * 支持两种查询方式
	 * 1. 页方式：指定session_id和页大小，页大小仅在第一次指定时生效
	 * 2. 范围方式：通过start,end指定获取记录的范围，此操作会尽量返回所满足的结果
	 */

	header_id = __get_header_id();

	if (SQLITE_OK != sqlite3_open_v2(LOG_FILE, &db, SQLITE_OPEN_READONLY, NULL))
		goto err_quit;

	if (session_id)
	{
		bzero(&sess, sizeof(session_s));
		sess.session_id = session_id;

		/* 第一次创建Session */
		if (!__session_info(&sess))
		{
			if (page_size <= 0)
				return -1;
			sess.page_size = page_size;
			sess.last_rec = header_id;
			if (!__session_update(&sess))
				return -1;
		}

		/* Session已经存在 */
		sprintf(sql_cmd, "SELECT * FROM jwlog WHERE (ID>=%llu and ID<%llu);",
			(unsigned long long)sess.last_rec, (unsigned long long)sess.last_rec+sess.page_size);
		if (SQLITE_OK == sqlite3_get_table(db, sql_cmd, &result, &col, &row, &errmsg))
		{
			/*
			 * 10|2012-11-16 14:35:54|Web|Manual|Info|测试日志信息
			 */
			for (i=1;(i<=col) && (i<=sess.page_size);i++)
			{
				log[i-1].idid = atoll(result[ROW_MAX*i]) - header_id + 1;
				strcpy(log[i-1].datetime, result[ROW_MAX*i+1]);
				strcpy(log[i-1].module, result[ROW_MAX*i+2]);
				strcpy(log[i-1].category, result[ROW_MAX*i+3]);
				strcpy(log[i-1].event, result[ROW_MAX*i+4]);
				strcpy(log[i-1].content, result[ROW_MAX*i+5]);
			}
			rec_num = col;

			sess.last_rec += sess.page_size;
			__session_update(&sess);
		}
	}
	else if(start>0 && end>start)
	{
	}

	sqlite3_free_table(result);
err_quit:
	sqlite3_close(db);

	return rec_num;
}
