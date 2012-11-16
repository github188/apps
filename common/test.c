#include <stdio.h>
#include "log.h"

void log_test1()
{
	LogInsert("Web", "Manual", "Info", "测试日志信息");
}

int main()
{
	log_test1();
	//log_db_exist();
	return 0;
}
