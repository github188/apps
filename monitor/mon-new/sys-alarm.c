#include "sys-action.h"

void sys_alarm_default(void *event)
{
}

void sys_alarm_buzzer(void *event)
{
}

void sys_alarm_sysled(void *event)
{
}

void sys_alarm_diskled(void *event)
{
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
