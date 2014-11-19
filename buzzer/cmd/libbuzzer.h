#ifndef LIBBUZZER__H__
#define LIBBUZZER__H__

#ifdef __cplusplus
extern "C" {
#endif // __cplusplus

enum BUZZER_STATUS{
	/* 计数增一, 当计数大于0时打开蜂鸣器 */
	BUZZER_ON			= 0x01,
	/* 计数减一，当计数减到0时关闭蜂鸣器 */
	BUZZER_OFF			= 0x02,
	/* 直接关闭蜂鸣器，不修改计数 */
	BUZZER_FORCE_OFF           = 0x03,
};

int buzzer_init(void);
void buzzer_release(void);
int buzzer_get(enum BUZZER_STATUS *sts);
int buzzer_set(enum BUZZER_STATUS sts);
int buzzer_get_count(void);

#ifdef __cplusplus
}
#endif // __cplusplus

#endif


