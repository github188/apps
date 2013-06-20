#include "sys-module.h"

struct list _gmodule_list;

void sys_module_init()
{
	list_init(&_gmodule_list);
}

void _module_event_release(sys_module_t *m)
{
	struct list *n, *nt;
	sys_event_conf_t *e;

	list_iterate_safe(n, nt, &m->event_list)
	{
		e = list_struct_base(n, sys_event_conf_t, event_list);
		list_del(&e->event_list);
		free(e);
	}
}

void sys_module_release(void)
{
	struct list *n, *nt;
	sys_module_t *m;

	list_iterate_safe(n, nt, &_gmodule_list)
	{
		m = list_struct_base(n, sys_module_t, list);

		_module_event_release(m);

		list_del(&m->list);
		free(m);
	}
}

bool sys_module_add(const char *name)
{
	sys_module_t *module;

	if (sys_module_get(name))
	{
		syslog(LOG_NOTICE, "sys_module_add('%s'): module exist!", name);
		return false;
	}

	if ( (module=(sys_module_t*)malloc(sizeof(*module))) != NULL )
	{
		strcpy(module->name, name);
		list_init(&module->list);
		list_init(&module->event_list);
		list_add(&_gmodule_list, &module->list);
		return true;
	}

	syslog(LOG_NOTICE, "sys_module_add('%s'): add fail, module memory alloc fail!", name);
	return false;
}

sys_module_t *sys_module_get(const char *name)
{
	sys_module_t *module;
	struct list *n, *nt;

	list_iterate_safe(n, nt, &_gmodule_list)
	{
		module = list_struct_base(n, sys_module_t, list);
		if (!strcmp(module->name, name))
		{
			return module;
		}
	}

	return NULL;
}

bool sys_module_event_add(const char *name, sys_event_conf_t *event)
{
	sys_module_t *module = sys_module_get(name);

	if ( (module=sys_module_get(name)) == NULL )
	{
		syslog(LOG_NOTICE, "sys_module_event_add('%s', '%s'): module not exist!", name, event->event);
		return false;
	}

	list_add(&module->event_list, &event->event_list);
	return true;
}

sys_event_conf_t *sys_module_event_get(const char *name, const char *event)
{
	struct list *n, *nt;
	sys_event_conf_t *ec;
	sys_module_t *module = sys_module_get(name);

	if ( (module=sys_module_get(name)) == NULL )
	{
		syslog(LOG_NOTICE, "sys_module_event_get('%s', '%s'): module not exist!", name, event);
		return NULL;
	}

	list_iterate_safe(n, nt, &module->event_list)
	{
		ec = list_struct_base(n, sys_event_conf_t, event_list);
		if (!strcmp(ec->event, event))
		{
			return ec;
		}
	}
	
	syslog(LOG_NOTICE, "sys_module_event_get('%s', '%s'): not found!", name, event);
	return NULL;
}

void sys_module_event_update(sys_event_conf_t *ec)
{
	if (ec)
		ec->count++;
}

void _dump_event(sys_module_t *module)
{
	struct list *n, *nt;
	sys_event_conf_t *ec;

	list_iterate_safe(n, nt, &module->event_list)
	{
		ec = list_struct_base(n, sys_event_conf_t, event_list);
		printf("\tevent: %s , level: %s, count: %d, action: %p\n",
				ec->event, ec->level, ec->count, ec->action);
	}
}

void dump_module_event()
{
	struct list *n, *nt;
	sys_module_t *module;

	printf("------------ dump modules ------------\n");

	list_iterate_safe(n, nt, &_gmodule_list)
	{
		module = list_struct_base(n, sys_module_t, list);
		printf("module: %s\n", module->name);
		_dump_event(module);
	}
}
