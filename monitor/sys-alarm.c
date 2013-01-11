#include "sys-action.h"
#include "sys-event.h"

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

void sys_alarm_default(void *event)
{
	syslog(LOG_INFO, "sys_alram_default()");

	sys_event_t *ev;

	// 如果配置关闭了tmpfs告警，则不处理
	if (!gconf.tmpfs)
		return;
	ev = (sys_event_t*)event;

	// 检查当前告警级别是否超出了配置上限，如果是，首先删除1条最旧的信息
	if (tmpfs_msg_count(ev->level) >= _gconf_level_count(ev->level))
		tmpfs_msg_sorted_unlink(tmpfs_msg_remove_oldest(ev->level));

	// 增加新的信息，并且链接到全局列表
	tmpfs_msg_sorted_link(tmpfs_msg_insert(ev->level, ev->msg));
}

void sys_alarm_buzzer(void *event)
{
	syslog(LOG_INFO, "sys_alarm_buzzer()");
}

void sys_alarm_sysled(void *event)
{
	syslog(LOG_INFO, "sys_alarm_sysled()");
}

void sys_alarm_diskled(void *event)
{
	syslog(LOG_INFO, "sys_alarm_diskled()");
}

struct _handler_map {
	char name[128];
	sys_alarm_handler handler;
};

struct _handler_map _map[] = {
	{"default", sys_alarm_default},
	{"buzzer", sys_alarm_buzzer},
	{"sys-led", sys_alarm_sysled},
	{"disk-led", sys_alarm_diskled},
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
