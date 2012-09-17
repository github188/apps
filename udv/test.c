#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include "libudv.h"

void test_create()
{
	ssize_t ret;

	ret = udv_create("/dev/md1", "udv1", 15000000);
	if (ret!=0)
	{
		printf("ret = %ld\n", ret);
		exit(1);
	}
}

void test_list()
{
	udv_info_t list[MAX_UDV], *udv;
	size_t udv_cnt = 0, i;

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<=0)
	{
		printf("no udv found!\n");
		return;
	}

	printf("VG        NAME    NUM  START    END    CAPACITY\n");

	udv = &list[0];
	for (i=0; i<udv_cnt; i++)
	{
		printf("%-10s %-8s %-2d %-8lld %-8lld %-8lld %-10s\n",
			udv->vg_dev, udv->name, udv->part_num,
			udv->geom.start, udv->geom.end, udv->geom.capacity,
			udv->dev);
		udv++;
	}
}

int main(int argc, char *argv[])
{
	/*
	if (argc!=2)
	{
		printf("input udv name to be deleted!\n");
		return -1;
	}
	*/

	char vg_dev[128];
	if (getVGDevByName("slash-server", vg_dev)==PYEXT_RET_OK)
		printf("vg dev: %s\n", vg_dev);
	else
		printf("get error!\n");


	printf("=========== before delete =============\n");
	test_list();

	if (argc!=3)
	{
		printf("%s udv_name size\n", argv[0]);
		return -1;
	}

	//udv_delete(argv[1]);
	//udv_create("/dev/md1", argv[1], atoll(argv[2]));
	udv_rename(argv[1], argv[2]);

	printf("=========== after delete =============\n");
	//printf("=========== after create =============\n");
	test_list();

	/*
	struct list list, *nn, *nt;
	ssize_t n;
	struct geom_stru *elem;

	n = get_udv_free_list("/dev/md1", &list);
	printf("n = %d\n", n);

	list_iterate_safe(nn, nt, &list)
	{
		elem = list_struct_base(nn, struct geom_stru, list);
		printf("start = %llu, end = %llu, capacity = %llu\n",
			elem->geom.start, elem->geom.end, elem->geom.capacity);
	}
	*/

	return 0;
}
