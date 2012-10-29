#include "log.h"

/* 记录日志 */
void LogInsert(
		log_module_e module,		// 写入日志的模块
		log_category_e category,	// 日志类型
		log_event_e event,		// 日志事件`
		const char *content		// 日志内容
	)
{
	return;
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
