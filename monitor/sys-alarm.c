#include <stdio.h>
#include <sys/types.h>
#include <regex.h>
#include "sys-action.h"
#include "sys-event.h"
#include "sys-utils.h"
#include "../pic_ctl/pic_ctl.h"

int _gconf_level_count(const char *level)
{
	if (!level)
		return 0;

	if (!strcmp(level, "info"))
		return gconf.info_size;
	else if (!strcmp(level, "warning"))
		return gconf.warning_size;
	else if (!strcmp(level, "error"))
		return gconf.error_size;
	return 0;
}

//----------------------- handlers --------------------------------

void sys_alarm_default(void *event)
{
	syslog(LOG_INFO, "sys_alram_default()");

	sys_event_t *ev = (sys_event_t*)event;
	
	// 如果配置关闭了tmpfs告警，则不处理
	if (!gconf.tmpfs)
		return;

	// 检查当前告警级别是否超出了配置上限，如果是，首先删除1条最旧的信息
	if (tmpfs_msg_count(ev->level) >= _gconf_level_count(ev->level))
		tmpfs_msg_sorted_unlink(tmpfs_msg_remove_oldest(ev->level));

	// 增加新的信息，并且链接到全局列表
	tmpfs_msg_sorted_link(tmpfs_msg_insert(ev->level, ev->msg));
}

void sys_alarm_buzzer_on(void *event)
{
	syslog(LOG_INFO, "sys_alarm_buzzer()");
}

void sys_alarm_buzzer_off(void *event)
{
	syslog(LOG_INFO, "sys_alarm_buzzer()");
}

const char *_get_next_disk_slot(const char *str)
{
	int cflags = REG_EXTENDED;
	int status;
	regmatch_t pmatch[1];
	const size_t nmatch = 1;
	regex_t reg;
	const char *pattern = "[0-9]:[0-9]+$";
	static char buf[128];
	static char slot[12];

	if (buf[0] == '\0')
		strcpy(buf, str);

	bzero(slot, 12);
	regcomp(&reg, pattern, cflags);
	status = regexec(&reg, buf, nmatch, pmatch, 0);
	if (status==0)
	{
		int i,j;
		for (j=0, i=pmatch[0].rm_so; i<pmatch[0].rm_eo; i++, j++)
			slot[j] = buf[i];
		buf[pmatch[0].rm_so-1] = '\0';
	}
	regfree(&reg);

	if (slot[0]=='\0')
		return NULL;
	return slot;
}

void sys_alarm_diskled_on(void *event)
{
	sys_event_t *ev = (sys_event_t*)event;

	syslog(LOG_INFO, "sys_alarm_diskled_on()");
	
	char *p;
	while( (p=_get_next_disk_slot(ev->param)) != NULL)
	{
		int enc,slot;
		sscanf("%d:%d", p, &enc, &slot);
		pic_set_led(slot, PIC_LED_ON, 0);
		syslog(LOG_INFO, "set disk %d:%d on", enc, slot);
	}
}

void sys_alarm_diskled_off(void *event)
{
	sys_event_t *ev = (sys_event_t*)event;

	syslog(LOG_INFO, "sys_alarm_diskled_off()");
	
	char *p;
	while( (p=_get_next_disk_slot(ev->param)) != NULL)
	{
		int enc,slot;
		sscanf("%d:%d", p, &enc, &slot);
		pic_set_led(slot, PIC_LED_OFF, 0);
		syslog(LOG_INFO, "set disk %d:%d off", enc, slot);
	}
}

void sys_alarm_diskled_blink1(void *event)
{
	sys_event_t *ev = (sys_event_t*)event;
	
	char *p;
	while( (p=_get_next_disk_slot(ev->param)) != NULL)
	{
		int enc,slot;
		sscanf("%d:%d", p, &enc, &slot);
		pic_set_led(slot, PIC_LED_BLINK, PIC_LED_FREQ_SLOW);
	}
}

void sys_alarm_diskled_blink5(void *event)
{
	sys_event_t *ev = (sys_event_t*)event;

	syslog(LOG_INFO, "sys_alarm_diskled_blink5()");
	
	char *p;
	while( (p=_get_next_disk_slot(ev->param)) != NULL)
	{
		int enc = -1, slot = -1;
		sscanf(p, "%d:%d", &enc, &slot);
		pic_set_led(slot, PIC_LED_BLINK, PIC_LED_FREQ_FAST);
		syslog(LOG_INFO, "set disk %d:%d to blink5", enc, slot);
	}
}

void sys_alarm_sysled_on(void *event)
{
	syslog(LOG_INFO, "sys_alarm_sysled_on()");
	sb_gpio28_set(true);
}

void sys_alarm_sysled_off(void *event)
{
	syslog(LOG_INFO, "sys_alarm_sysled_off()");
	sb_gpio28_set(false);
}

struct _handler_map {
	char name[128];
	sys_alarm_handler handler;
};

struct _handler_map _map[] = {
	{"default", sys_alarm_default},
	{"buzzer-on", sys_alarm_buzzer_on},
	{"buzzer-off", sys_alarm_buzzer_off},
	{"disk-led-on", sys_alarm_diskled_on},
	{"disk-led-off", sys_alarm_diskled_off},
	{"disk-led-blink1", sys_alarm_diskled_blink1},
	{"disk-led-blink5", sys_alarm_diskled_blink5},
	{"sys-led-on", sys_alarm_sysled_on},
	{"sys-led-off", sys_alarm_sysled_off},
	{'\0', 0}
};

void sys_alarm_set_handler(sys_alarm_t *alarm, const char *handler_name)
{
	struct _handler_map *p = &_map[0];

	if (alarm && handler_name)
	{
		while(p->name[0] != '\0')
		{
			if (!strcmp(handler_name, p->name))
			{
				alarm->handler = p->handler;
				return;
			}
			p++;
		}
	}
}
