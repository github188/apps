#ifndef LIBLED__H__
#define LIBLED__H__

enum {
	LED_ON			= 0x01,
	LED_OFF			= 0x02,
	LED_BLINK_FAST	        = 0x03,
	LED_BLINK_NORMAL	= 0x04,
	LED_BLINK_SLOW		= 0x05,
};

int led_init(void);
void led_release(void);
/* 如果disk_id为0，则设置所有灯 */
int diskled_set(int disk_id, int mode);
/* 返回硬盘灯的个数 */
int diskled_get_num(void);
/* 获取所有灯的状态，放到数组arr中， size必须大于等于硬盘灯个数 */
int diskled_get_all(int *arr, int size);
/* 获取disk_id单个灯的状态，放到sts中 */
int diskled_get(int disk_id, int *sts);
int sysled_set(int mode);
int sysled_get(int *sts);

#endif // LIBLED__H__
