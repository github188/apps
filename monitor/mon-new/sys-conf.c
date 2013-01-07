#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include "sys-module.h"
#include "sys-action.h"

#define _XML_STR_VAL(node, key) (char*)xmlGetProp(node, BAD_CAST(key))
#define _XML_IGN_CHECK(node) if (xmlStrcmp(node->name, BAD_CAST"text"))

void _xml_module_event_parse(char *module, xmlNodePtr node)
{
	while(node)
	{
		if (!xmlStrcmp(node->name, BAD_CAST"event"))
		{
			syslog(LOG_NOTICE, "found a new event!");

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
			syslog(LOG_NOTICE, "found a new module!");
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
			syslog(LOG_NOTICE, "find a new alarm!");

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
			syslog(LOG_NOTICE, "find a new action!");
			sys_action_add(node->name);
			_xml_action_alarm_parse(node->name, node->xmlChildrenNode);
		}
		node = node->next;
	}
}

void _xml_global_parse(xmlNodePtr node)
{
}

void _xml_self_run_parse(xmlNodePtr node)
{
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

	sys_mon_conf_check();

	doc = xmlReadFile(SYS_MON_CONF, "UTF-8", XML_PARSE_RECOVER);
	if (!doc)
	{
		syslog(LOG_ERR, "Load system monitor configure file %s error!", SYS_MON_CONF);
		return;
	}

	node = xmlDocGetRootElement(doc);
	if (!node)
	{
		syslog(LOG_ERR, "Parse xml error!");

		xmlErrorPtr err = xmlGetLastError();
		if (err && err->message)
			syslog(LOG_ERR, "xml err: %s\n", err->message);

		goto _conf_clean;
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

_conf_clean:
	xmlFreeDoc(doc);
	xmlCleanupParser();
}
