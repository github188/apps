#ifndef LIBLED__H__
#define LIBLED__H__

int led_init(void);
void led_release(void);
int diskled_get_disknum(void);
int diskled_on(int disk_id);
int diskled_off(int disk_id);
int diskled_blink1s4(int disk_id);
int diskled_blink1s1(int disk_id);
int diskled_blink2s1(int disk_id);
int sysled_on(void);
int sysled_off(void);

#endif // LIBLED__H__
