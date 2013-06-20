#include <stdlib.h>
#include "sys-action.h"

struct list _gaction_list;

void sys_action_init()
{
	list_init(&_gaction_list);
}

void _action_alarm_release(sys_action_t *a)
{
	struct list *n, *nt;
	sys_alarm_t *alr;

	list_iterate_safe(n, nt, &a->alarm_list)
	{
		alr = list_struct_base(n, sys_alarm_t, alarm_list);
		list_del(&alr->alarm_list);
		free(alr);
	}
}

void sys_action_release()
{
	struct list *n, *nt;
	sys_action_t *a;

	list_iterate_safe(n, nt, &_gaction_list)
	{
		a = list_struct_base(n, sys_action_t, list);

		_action_alarm_release(a);

		list_del(&a->list);
		free(a);
	}
}

sys_action_t *sys_action_alloc()
{
	sys_action_t *action;

	if ( (action=(sys_action_t*)malloc(sizeof(*action))) != NULL )
	{
		list_init(&action->list);
		list_init(&action->alarm_list);
		action->name[0] = '\0';
		return action;
	}

	syslog(LOG_NOTICE, "sys_action_alloc(): fail to alloc!");
	return NULL;
}

void _sys_action_default_alarm_add(const char *action)
{
	if (action)
	{
		sys_alarm_t *alarm;
		if ( (alarm=sys_alarm_alloc()) != NULL )
		{	
			strcpy(alarm->name, "default");
			sys_alarm_set_handler(alarm, "default");
			sys_action_alarm_add(action, alarm);
			return;
		}
	}
	syslog(LOG_NOTICE, "_sys_action_default_alarm_add('%s'): add default alarm fail!", action);
}

bool sys_action_add(const char *name)
{
	if (sys_action_get(name))
		return false;

	sys_action_t *action;
	if ( (action=sys_action_alloc()) != NULL )
	{
		strcpy(action->name, name);
		list_add(&_gaction_list, &action->list);
		_sys_action_default_alarm_add(name);
		return true;
	}

	syslog(LOG_NOTICE, "sys_action_add('%s'): add fail!", name);
	return false;
}

sys_action_t *sys_action_get(const char *name)
{
	struct list *n, *nt;
	sys_action_t *action;

	list_iterate_safe(n, nt, &_gaction_list)
	{
		action = list_struct_base(n, sys_action_t, list);
		if (!strcmp(action->name, name))
		{
			return action;
		}
	}

	return NULL;
}

sys_alarm_t *sys_alarm_alloc()
{
	sys_alarm_t *alarm;

	if ( (alarm=(sys_alarm_t*)malloc(sizeof(*alarm))) != NULL )
	{
		list_init(&alarm->alarm_list);
		alarm->name[0] = '\0';
		alarm->handler = NULL;
		return alarm;
	}
	
	syslog(LOG_NOTICE, "sys_alarm_alloc(): fail, no more memory!");
	return NULL;
}

bool sys_action_alarm_add(const char *name, sys_alarm_t *alarm)
{
	sys_action_t *action;
	
	if ( (action=sys_action_get(name)) != NULL )
	{
		list_add(&action->alarm_list, &alarm->alarm_list);
		return true;
	}

	syslog(LOG_NOTICE, "sys_action_alarm_add('%s', '%s'): fail!", name, alarm->name);
	return false;
}

sys_alarm_t *sys_action_alarm_get(const char *action, const char *alarm)
{
	sys_action_t *ac;
	sys_alarm_t *al;
	struct list *n, *nt;

	if ( (ac=sys_action_get(action)) == NULL )
		return NULL;

	list_iterate_safe(n, nt, &ac->alarm_list)
	{
		al = list_struct_base(n, sys_alarm_t, alarm_list);
		if (!strcmp(al->name, alarm))
		{
			return al;
		}
	}
	
	syslog(LOG_NOTICE, "sys_action_alarm_get('%s', '%s'): not found!", action, alarm);
	return NULL;
}

void do_sys_action(sys_action_t *action, void *event)
{
	struct list *n, *nt;
	sys_alarm_t *alarm;

	if (!action)
		return;

	list_iterate_safe(n, nt, &action->alarm_list)
	{
		alarm = list_struct_base(n, sys_alarm_t, alarm_list);
		if (alarm->handler)
			alarm->handler(event);
	}
}

void _dump_alarm(sys_action_t *action)
{
	if (action)
	{
		struct list *n, *nt;
		sys_alarm_t *alarm;

		list_iterate_safe(n, nt, &action->alarm_list)
		{
			alarm = list_struct_base(n, sys_alarm_t, alarm_list);
			printf("\talarm: %s, handler: %p\n", alarm->name, alarm->handler);
		}
	}
}

void dump_action_alarm()
{
	struct list *n, *nt;
	sys_action_t *action;

	printf("--------- dump actions -------------\n");

	list_iterate_safe(n, nt, &_gaction_list)
	{
		action = list_struct_base(n, sys_action_t, list);
		printf("action: %s\n", action->name);
		_dump_alarm(action);
	}
}
