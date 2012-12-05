#include "sys-mon.h"

static struct list *galarm = NULL;
static const char *__cap_alarm_map[] = {
	"cpu-temp", "temperature",
	"env-temp", "temperature",
	"case-temp", "temperature",
	NULL};

size_t mon_alarm_load()
{
	return 0;
}

size_t mon_alarm_reload()
{
	return 0;
}

/*
 * 检查监控模块与响应告警的对应关系
 */
int __get_alarm_action(const char *mod)
{
	const char *alarm_mod = NULL;
	struct list *n, *nt;
	alarm_conf_t *tmp;
	int i;

	for (i=0;__cap_alarm_map[i];i+=2)
	{
		if (strcmp(__cap_alarm_map[i], mod))
		{
			alarm_mod = __cap_alarm_map[i+1];
			break;
		}
	}

	if (!alarm_mod)
		return 0;

	list_iterate_safe(n, nt, galarm)
	{
		tmp = list_struct_base(n, alarm_conf_t, list);
		if (!strcmp(tmp->name, alarm_mod))
			return tmp->action;
	}

	return 0;
}

/*---------------------------------------------------------------------------*/
/*  Actions                                                                  */
/*---------------------------------------------------------------------------*/

void action_buzzer()
{
}

void action_sysled()
{
}

void action_email(const char *mod, const char *msg)
{
}


/*---------------------------------------------------------------------------*/
/* Alarm event                                                               */
/*---------------------------------------------------------------------------*/

void raise_alarm(const char *mod, const char *msg)
{
	int action;

	if ( !(action = __get_alarm_action(mod)) )
		return;

	if (action & ALARM_BUZZER)
		action_buzzer();
	if (action & ALARM_SYSLED)
		action_sysled();
	if (action & ALARM_EMAIL)
		action_email(mod, msg);
}

