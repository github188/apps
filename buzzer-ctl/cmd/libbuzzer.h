#ifndef LIBBUZZER__H__
#define LIBBUZZER__H__

enum {
	BUZZER_ON			= 0x01,
	BUZZER_OFF			= 0x02,
	BUZZER_FORCE_OFF           = 0x03,
	BUZZER_BLINK_FAST	        = 0x04,
	BUZZER_BLINK_NORMAL	= 0x05,
	BUZZER_BLINK_SLOW		= 0x06,
};

int buzzer_init(void);
void buzzer_release(void);
int buzzer_get(int *sts);
/*设置系统灯状态，BUZZER_ON打开并增加count计数，BUZZER_OFF减少计数，如果计数小于等于0则关闭，
 * BUZZER_FORCE_OFF不更改计数，关闭灯  */
int buzzer_set(int mode);
int buzzer_set_time(long time);


#endif // LIBLED__H__
