#ifndef LIBLED__H__
#define LIBLED__H__

enum LED_STATUS {
	LED_ON			= 0x01,
	LED_OFF			= 0x02,
	LED_FORCE_OFF           = 0x03,
	LED_BLINK_FAST	        = 0x04,
	LED_BLINK_NORMAL	= 0x05,
	LED_BLINK_SLOW		= 0x06,
};

int led_init(void);
void led_release(void);

/* 返回硬盘灯的个数 */
int diskled_get_num(void);

/* 如果disk_id为0，则设置所有灯 */
int diskled_set(int disk_id, enum LED_STATUS sts);

/* 获取disk_id单个灯的状态，放到sts中 */
int diskled_get(int disk_id, enum LED_STATUS *sts);

/* 获取所有灯的状态，放到数组sts_array中， size必须大于等于硬盘灯个数 */
int diskled_get_all(enum LED_STATUS *sts_array, int size);

/* 
 * sysled系统灯
 * LED_ON sysled计数增一，当计数大于0时打开sysled
 * LED_OFF sysled计数减一，当计数减到0时关闭sysled
 * LED_FORCE_OFF 不修改sysled计数，只关闭sysled
 */
int sysled_set(enum LED_STATUS sts);
int sysled_get(enum LED_STATUS *sts);
int sysled_get_count(void);
#endif // LIBLED__H__
