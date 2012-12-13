#include <libxml/parser.h>
#include <libxml/tree.h>
#include "sys-mon.h"

static struct list galarm;

static const char *__alarm_list[] = {
	"power", "disk", "vg", "temperature", "fan", NULL
};

bool __alarm_supported(const char *mod)
{
	const char *p = __alarm_list[0];
	while(p)
	{
		if (!strcmp(p, mod))
			return true;
		p++;
	}
	return false;
}

static const char *__cap_alarm_map[] = {
	"cpu-temp", "temperature",
	"env-temp", "temperature",
	"case-temp", "temperature",
	NULL};

void dump_alarm_conf()
{
	struct list *n, *nt;
	alarm_conf_t *tmp;

	list_iterate_safe(n, nt, &galarm)
	{
		tmp = list_struct_base(n, alarm_conf_t, list);
		printf("name: %s ", tmp->name);
		if (tmp->action & ALARM_BUZZER)
			puts(" BUZZER ");
		if (tmp->action & ALARM_SYSLED)
			puts(" SYSLED ");
		if (tmp->action & ALARM_EMAIL)
			puts(" EMAIL ");
	}
}

size_t mon_alarm_load()
{
	xmlDocPtr doc;
	xmlNodePtr node;

	DBGP("into load conf! %s\n", ALARM_CONF);
	syslog(LOG_INFO, "%s", __func__);

	list_init(&galarm);

	if (access(ALARM_CONF, R_OK))
	{
		syslog(LOG_ERR, "the default alarm conf file %s not exist! this will be created!", ALARM_CONF);
		if (!create_default_conf(ALARM_CONF, ALARM_CONF_CONTENT))
		{
			syslog(LOG_ERR, "create default alarm conf file error!");
			kill(getpid(), SIGTERM);
			return -1;
		}
	}

	if ( (doc=xmlReadFile(ALARM_CONF, "UTF-8", XML_PARSE_RECOVER)) == NULL )
	{
		syslog(LOG_ERR, "load alarm conf fail!");
		return -1;
	}

	if ( (node=xmlDocGetRootElement(doc)) == NULL )
	{
		syslog(LOG_ERR, "load alarm conf fail! nothing to load!");
		goto _mon_load_error;
	}

	node = node->xmlChildrenNode;
	while(node)
	{
		/* <module buzzer="disable" email="disable" name="power" switch="disable" sys-led="enable"/> */
		// concern about label 'module'
		if (xmlStrcmp(node->name, BAD_CAST"module"))
		{
			node = node->next;
			continue;
		}

		xmlChar *modName = xmlGetProp(node, "name"),
			*modSwitch = xmlGetProp(node, "switch"),
			*modFuncEmail = xmlGetProp(node, "email"),
			*modFuncSysLed = xmlGetProp(node, "sys-led"),
			*modFuncBuzzer = xmlGetProp(node, "buzzer");

		alarm_conf_t *tmp = NULL;
		if ( modName && modSwitch && __alarm_supported(modName) &&
			!strcmp(modSwitch, "enable") )
		{
			if ((tmp=(alarm_conf_t*)malloc(sizeof(alarm_conf_t))) != NULL)
			{
				bzero(tmp, sizeof(alarm_conf_t));
				strcpy(tmp->name, modName);
				if (!xmlStrcmp(modFuncEmail, "enable"))
					tmp->action |= ALARM_EMAIL;
				if (!xmlStrcmp(modFuncSysLed, "enable"))
					tmp->action |= ALARM_SYSLED;
				if (!xmlStrcmp(modFuncBuzzer, "enable"))
					tmp->action |= ALARM_BUZZER;
				list_add(&galarm, &tmp->list);
				syslog(LOG_INFO, "Load: %s action: %.8x\n", tmp->name, tmp->action);
			}
		}

		if (modName) xmlFree(modName);
		if (modSwitch) xmlFree(modSwitch);
		if (modFuncEmail) xmlFree(modFuncEmail);
		if (modFuncSysLed) xmlFree(modFuncSysLed);
		if (modFuncBuzzer) xmlFree(modFuncBuzzer);

		node = node->next;
	}

_mon_load_error:
	xmlFreeDoc(doc);
	xmlCleanupParser();

#ifndef NDEBUG
	dump_alarm_conf();
#endif

	return (ssize_t)list_size(&galarm);
}

size_t mon_alarm_reload()
{
	mon_alarm_release();
	return mon_alarm_load();
}

void mon_alarm_release()
{
	struct list *n, *nt;
	alarm_conf_t *tmp;

	syslog(LOG_INFO, "%s\n", __func__);

	list_iterate_safe(n, nt, &galarm)
	{
		tmp = list_struct_base(n, alarm_conf_t, list);
		list_del(n); free(tmp);
	}
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

	list_iterate_safe(n, nt, &galarm)
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
	syslog(LOG_ERR, "*** buzzer action ***");
}

void action_sysled()
{
	syslog(LOG_ERR, "*** sysled action ***");
}

void action_email(const char *mod, const char *msg)
{
	syslog(LOG_ERR, "*** email action ***");
}


/*---------------------------------------------------------------------------*/
/* Alarm event                                                               */
/*---------------------------------------------------------------------------*/

void raise_alarm(const char *mod, const char *msg)
{
	int action;

	LogInsert(NULL, "SysMon", "Auto", "Warning", msg);

	if ( !(action = __get_alarm_action(mod)) )
		return;

	if (action & ALARM_BUZZER)
		action_buzzer();
	if (action & ALARM_SYSLED)
		action_sysled();
	if (action & ALARM_EMAIL)
		action_email(mod, msg);
}

