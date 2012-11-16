#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>

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
	return 0;
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
	return 0;
}
