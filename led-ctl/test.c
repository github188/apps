/*******************************************************************************
* Author : liyunteng
* Email : li_yunteng@163.com
* Created Time : 2014-03-17 17:14
* Filename : test.c
* Description : 
* *****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "./cmd/libled.h"
#include "./daemon/i2c_dev.h"

int main(int argc, char *argv[])
{
	int a;
	int *arr;
	int num;

	sysled_get(&a);
	printf("sysled: %d\n", a);

	num = diskled_get_num();
	arr = (int *)malloc(sizeof(int) * num);
	diskled_get_all(arr, num);

	int i;
	for(i=0; i<num; i++) {

		printf("%d: %d\n", i+1, arr[i]);
	}
	printf("\n");
	
	return 0;
}
