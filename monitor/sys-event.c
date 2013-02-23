#include "sys-event.h"

void sys_event_zero(sys_event_t *ev)
{
	if (ev)
		ev->module[0] = ev->event[0] =
		ev->param[0] = ev->msg[0] = '\0';
}

sys_event_conf_t *sys_event_conf_alloc()
{
	sys_event_conf_t *ec;

	if ( (ec=(sys_event_conf_t*)malloc(sizeof(*ec))) != NULL )
	{
		list_init(&ec->event_list);
		ec->count = 0;
		ec->action = NULL;

		syslog(LOG_NOTICE, "sys_event_conf_alloc(): OK!");
		return ec;
	}

	syslog(LOG_NOTICE, "sys_event_conf_alloc(): fail!");
	return NULL;
}

/*
 * 请求消息格式
 * { "module":"xxx", "event":"xxx", "param":"xxx", "msg":"xxx" }
 * 其中
 *   module = { disk, vg, udv, iscsi, nas, system }
 *   event: disk = { online, offline, invalid, temp-overflow }
 *          vg = { create, remove, degrad, fail }
 *
 */
void sys_event_fill(sys_event_t *ev, const char *key, const char *value)
{
	if (!strcmp(key, "module"))
		strcpy(ev->module, value);
	else if (!strcmp(key, "event"))
		strcpy(ev->event, value);
	else if (!strcmp(key, "param"))
		strcpy(ev->param, value);
	else if (!strcmp(key, "msg"))
		strcpy(ev->msg, value);
}
