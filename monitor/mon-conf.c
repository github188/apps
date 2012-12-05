#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include "sys-mon.h"


struct list gconf;

#ifndef NDEBUG
void dump_mon_conf()
{
	struct list *n, *nt;
	mon_conf_t *tmp;

	list_iterate_safe(n, nt, &gconf)
	{
		tmp = list_struct_base(n, mon_conf_t, list);
		printf("name: %s\n", tmp->name);
		printf("check_int: %d\n", tmp->name);
		printf("min_thr: %d\n", tmp->min_thr);
		printf("max_thr: %d\n", tmp->max_thr);
		printf("min_alr: %d\n", tmp->min_alr);
		printf("max_alr: %d\n", tmp->max_alr);
	}
}
#endif

size_t mon_conf_load()
{
	xmlDocPtr doc;
	xmlNodePtr node;

	DBGP("into load conf! %s\n", MON_CONF);

	if ( (doc=xmlReadFile(MON_CONF, "UTF-8", XML_PARSE_RECOVER)) == NULL )
	{
		DBGP("load xml fail\n");
		return -1;
	}

	list_init(&gconf);

	if ( (node=xmlDocGetRootElement(doc)) == NULL )
	{
		DBGP("get root fail!\n");
		goto _mon_load_error;
	}

	node = node->xmlChildrenNode;
	while(node)
	{
		// concern about label 'target'
		if (xmlStrcmp(node->name, BAD_CAST"target"))
		{
			node = node->next;
			continue;
		}

		xmlChar *tgtName = xmlGetProp(node, "name"),
			*tgtChkInt = xmlGetProp(node, "check_interval"),
			*tgtMinThr = xmlGetProp(node, "min_threshold"),
			*tgtMaxThr = xmlGetProp(node, "max_threshold"),
			*tgtMinAlr = xmlGetProp(node, "min_alarm"),
			*tgtMaxAlr = xmlGetProp(node, "max_alarm");

		if (tgtName && tgtChkInt && tgtMinThr && tgtMaxThr
			&& tgtMinAlr && tgtMaxAlr)
		{
			mon_conf_t *tmp = NULL;
			if ( (tmp=(mon_conf_t*)malloc(sizeof(mon_conf_t))) != NULL)
			{
				bzero(tmp, sizeof(mon_conf_t));
				strcpy(tmp->name, tgtName);
				tmp->check_int = atoi(tgtChkInt);
				tmp->min_thr = atoi(tgtMinThr);
				tmp->max_thr = atoi(tgtMaxThr);
				tmp->min_alr = atoi(tgtMinThr);
				tmp->max_alr = atoi(tgtMaxThr);
				list_add(&gconf, &tmp->list);

#ifndef NDEBUG
				DBGP("check_int: %d / %s\n", tmp->check_int, tgtChkInt);
				dump_mon_conf();
#endif
			}
		}

		if (tgtName) xmlFree(tgtName);
		if (tgtChkInt) xmlFree(tgtChkInt);
		if (tgtMinThr) xmlFree(tgtMinThr);
		if (tgtMaxThr) xmlFree(tgtMaxThr);
		if (tgtMinAlr) xmlFree(tgtMinAlr);
		if (tgtMaxAlr) xmlFree(tgtMaxAlr);

		node = node->next;
	}

_mon_load_error:
	xmlFreeDoc(doc);
	xmlCleanupParser();

	return (ssize_t)list_size(&gconf);
}

size_t mon_conf_reload()
{
	mon_conf_release(&gconf);
	return mon_conf_load();
}

void mon_conf_release()
{
	struct list *n, *nt;
	mon_conf_t *tmp;

	list_iterate_safe(n, nt, &gconf)
	{
		tmp = list_struct_base(n, mon_conf_t, list);
		list_del(n); free(tmp);
		DBGP("free node!\n");
	}
}
