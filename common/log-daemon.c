#include <stdio.h>
#include <sqlite3.h>
#include "log.h"

#define LOG_FILE "/opt/log/log.db"

int db_create();
void db_write();
void db_close();

void log_daemon()
{
	// 检查数据库是否存在
	// 存在打开，否则创建

	// 创建UNIX socket
	// 监听
}

int main()
{
	daemon();

	signal(SIGINT, sig_int);
	log_daemon();
}
