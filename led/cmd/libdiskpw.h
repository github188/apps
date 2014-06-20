#ifndef LIBDISKPW__H__
#define LIBDISKPW__H__
enum DISKPW_STATUS {
	POWER_OFF 		= 0x00, 	//暂不支持
	POWER_ON 		= 0x01, 	//暂不支持
	POWER_RESET 		= 0x02,
};

int diskpw_init(void);
void diskpw_release(void);
int diskpw_get_num(void);
/*
 * 设置硬盘上下电， mode为设置的模式，
 * 如果设置的模式为reset，seconds为中间等待的时间,最大为16，
 * 否则seconds为0
 */
int diskpw_set(int id, enum DISKPW_STATUS mode, int seconds);
#endif // LIBDISKPW__H__

