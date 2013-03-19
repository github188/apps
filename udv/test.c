#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include "libudv.h"

void test_create()
{
	ssize_t ret;

	ret = udv_create("vgtest1", "udv3", 5000000);
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
	char udv_state[128];

	udv_cnt = udv_list(list, MAX_UDV);
	if (udv_cnt<=0)
	{
		printf("no udv found!\n");
		return;
	}

	printf("VG        NAME    NUM  START    END    CAPACITY    DEVICE    STATE\n");

	udv = &list[0];
	for (i=0; i<udv_cnt; i++)
	{
		if (udv->state == UDV_ISCSI)
			strcpy(udv_state, "iSCSI Volume");
		else if (udv->state == UDV_NAS)
			strcpy(udv_state, "NAS");
		else
			strcpy(udv_state, "RAW");

		printf("%-10s %-8s %-2d %-8lld %-8lld %-8lld %-10s %-10s\n",
			udv->vg_dev, udv->name, udv->part_num,
			udv->geom.start, udv->geom.end, udv->geom.capacity,
			udv->dev, udv_state);
		udv++;
	}
}

int main(int argc, char *argv[])
{
	//test_list();

	//printf("is nas: %d\n", isNasVolume("abc"));
	/*
	if (argc!=2)
	{
		printf("input udv name to be deleted!\n");
		return -1;
	}
	*/

	//printf("iscsi volume /dev/md1 check, return: %d\n", isISCSIVolume("/dev/md1"));

	/*
	char vg_dev[128];
	if (getVGDevByName("vgtest1", vg_dev)==PYEXT_RET_OK)
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
	*/

	//udv_delete(argv[1]);
	//udv_create("/dev/md1", argv[1], atoll(argv[2]));
	//udv_rename(argv[1], argv[2]);

	//printf("=========== after delete =============\n");
	//printf("=========== after create =============\n");
	/*
	if (udv_get_free_list("slash", &list)>0)
	{
		list_iterate_safe(n, nt, &list)
		{
			tmp = list_struct_base(n, struct geom_stru, list);
			printf("start : %llu, end: %llu\n",
					tmp->geom.start, tmp->geom.end);
		}
	}
	*/
	//test_list();
	//test_create();
	//test_list();

	struct list list, *nn, *nt;
	ssize_t n;
	struct geom_stru *elem;

	n = udv_get_free_list("/dev/md2", &list);
	printf("n = %d\n", n);

	list_iterate_safe(nn, nt, &list)
	{
		elem = list_struct_base(nn, struct geom_stru, list);
		printf("start = %llu, end = %llu, capacity = %llu\n",
			elem->geom.start, elem->geom.end, elem->geom.capacity);
	}

	return 0;
}
