#include <stdio.h>
#include "log.h"

void log_test1()
{
	LogInsert(LOG_MOD_WEB, LOG_CATG_MANUAL, LOG_EV_INFO, "测试日志信息");
}

int main()
{
	log_test1();
	//log_db_exist();
	return 0;
}
