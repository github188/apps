/*******************************************************************************
* Author : liyunteng
* Email : li_yunteng@163.com
* Created Time : 2014-03-17 17:14
* Filename : test.c
* Description : 
* *****************************************************************************/
#include <stdio.h>
#include <unistd.h>
#include "./cmd/libled.h"
#include "./daemon/i2c_dev.h"

int main(int argc, char *argv[])
{
	//unsigned long i;
	//for (i=0; i<100000000; i++) {
	diskled_on(1);
	diskled_off(2);
	diskled_blink1s4(3);
	diskled_blink1s1(4);
	diskled_blink2s1(5);
	sysled_on();
	//}

	printf("done!\n");
	sleep(10);
	return 0;
}
