#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include "sys-module.h"
#include "sys-action.h"
#include "sys-interval-check.h"

#define _XML_STR_VAL(node, key) (char*)xmlGetProp(node, BAD_CAST(key))
#define _XML_IGN_CHECK(node) if ((xmlStrcmp(node->name, BAD_CAST"text")) || xmlStrcmp(node->name, BAD_CAST"comment"))
#define _XML_NODE_NAME(node, name1) (!xmlStrcmp(node->name, BAD_CAST(name1)))
#define _XML_ATTR_EQU(node, key, value) (!strcmp(_XML_STR_VAL(node, key), value))

void _xml_module_event_parse(char *module, xmlNodePtr node)
{
	while(node)
	{
		if (!xmlStrcmp(node->name, BAD_CAST"event"))
		{
			syslog(LOG_NOTICE, "XML(module_event_parser): found a new event!");

			sys_event_conf_t *ec = sys_event_conf_alloc();
			strcpy(ec->module, module);
			strcpy(ec->event, _XML_STR_VAL(node, "name"));
			strcpy(ec->level, _XML_STR_VAL(node, "level"));
			ec->action = sys_action_get(_XML_STR_VAL(node, "action"));
			sys_module_event_add(module, ec);
		}
		node = node->next;
	}
}

void _xml_module_parse(xmlNodePtr node)
{
	while(node)
	{
		_XML_IGN_CHECK(node)
		{
			syslog(LOG_NOTICE, "XML(module_parser): found a new module!");
			sys_module_add(node->name);
			_xml_module_event_parse(node->name, node->xmlChildrenNode);
		}
		node = node->next;
	}
}

void _xml_action_alarm_parse(char *action_name, xmlNodePtr node)
{
	while(node)
	{
		if (!xmlStrcmp(node->name, BAD_CAST"alarm"))
		{
			syslog(LOG_NOTICE, "XML(action_alarm_parser): find a new alarm!");

			sys_alarm_t *alarm = sys_alarm_alloc();
			strcpy(alarm->name, _XML_STR_VAL(node, "name"));
			sys_alarm_set_handler(alarm, _XML_STR_VAL(node, "name"));
			sys_action_alarm_add(action_name, alarm);
		}
		node = node->next;
	}
}

void _xml_action_parse(xmlNodePtr node)
{
	while(node)
	{

		_XML_IGN_CHECK(node)
		{
			syslog(LOG_NOTICE, "XML(action_parser): find a new action %s!", node->name);
			sys_action_add(node->name);
			_xml_action_alarm_parse(node->name, node->xmlChildrenNode);
		}
		node = node->next;
	}
}

void _xml_global_parse(xmlNodePtr node)
{
	while(node)
	{
		char *tmp;

		// tmpfs
		if (_XML_NODE_NAME(node, "tmpfs") && _XML_ATTR_EQU(node, "active", "enable"))
			gconf.tmpfs = true;
		if _XML_NODE_NAME(node, "msg_buff_size")
		{
			if ((tmp=_XML_STR_VAL(node, "info")))
				gconf.info_size = atoi(tmp);
			if ((tmp=_XML_STR_VAL(node, "warning")))
				gconf.warning_size = atoi(tmp);
			if ((tmp=_XML_STR_VAL(node, "error")))
				gconf.error_size = atoi(tmp);
		}
		node = node->next;
	}
}

void _xml_self_run_parse(xmlNodePtr node)
{
	while(node)
	{
		if (!xmlStrcmp(node->name, BAD_CAST"item") &&
			isCaptureSupported(_XML_STR_VAL(node, "name")))
		{
			syslog(LOG_NOTICE, "XML(self_run_parse): find a new alarm %s!", _XML_STR_VAL(node, "name"));

			sys_capture_t *cap = sys_capture_alloc();
			if (cap)
			{
				strcpy(cap->name, _XML_STR_VAL(node, "name"));
				cap->check_intval = atoi(_XML_STR_VAL(node, "interval"));
				cap->min_thr = atoi(_XML_STR_VAL(node, "min_threshold"));
				cap->max_thr = atoi(_XML_STR_VAL(node, "max_threshold"));
				sys_capture_set_handler(cap);
				sys_capture_add(cap);
			}
		}
		node = node->next;
	}
}

void sys_mon_conf_check()
{
}

void sys_mon_load_conf()
{
	xmlDocPtr doc;
	xmlNodePtr node, tmp;

	sys_action_init();
	sys_module_init();
	sys_global_init();
	sys_capture_init();

	sys_mon_conf_check();

	doc = xmlReadFile(SYSMON_CONF, "UTF-8", XML_PARSE_RECOVER);
	if (!doc)
	{
		syslog(LOG_ERR, "XML: Load system monitor configure file %s error!", SYSMON_CONF);
		return;
	}

	if ( (node=xmlDocGetRootElement(doc)) &&
		!xmlStrcmp(node->name, BAD_CAST"monitor") )
	{
		// load actions first
		tmp = node->xmlChildrenNode;
		while(tmp)
		{
			if (!xmlStrcmp(tmp->name, BAD_CAST"actions"))
			{
				_xml_action_parse(tmp->xmlChildrenNode);
				break;
			}
			tmp = tmp->next;
		}

		node = node->xmlChildrenNode;
		while(node)
		{
			if (!xmlStrcmp(node->name, BAD_CAST"modules"))
				_xml_module_parse(node->xmlChildrenNode);
			else if (!xmlStrcmp(node->name, BAD_CAST"global"))
				_xml_global_parse(node->xmlChildrenNode);
			else if (!xmlStrcmp(node->name, BAD_CAST"self_run"))
				_xml_self_run_parse(node->xmlChildrenNode);
			node = node->next;
		}
	}

#ifndef _NDEBUG
	printf("conf loaded!\n");
#endif

_conf_clean:
	xmlFreeDoc(doc);
	xmlCleanupParser();
}
