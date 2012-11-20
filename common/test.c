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

void log_test3()
{
	log_info_s log_list[128];
	ssize_t n,i;

	n = LogGet(0x1234aaff, -1, -1, 5, &log_list);
	printf("n = %d\n", n);

	if (n<=0)
		return;

	printf("ID\tDate Time\t\tModule\tCategory\tEvent\tContent\n");
	for (i=0;i<n;i++)
	{
		printf("%llu\t%s\t%s\t%s\t\t%s\t%s\n",
			log_list[i].idid, log_list[i].datetime,
			log_list[i].module, log_list[i].category, log_list[i].event, log_list[i].content);
	}
}

int main()
{
	//log_test1();
	//log_test2();
	log_test3();
	return 0;
}
