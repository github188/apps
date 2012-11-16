#include <stdio.h>
#include "log.h"

void log_test1()
{
	LogInsert("Web", "Manual", "Info", "测试日志信息");
}

void log_test2()
{
	printf("count = %d\n", LogGetQuantity());
}

int main()
{
	//log_test1();
	log_test2();
	return 0;
}
