#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include "sys-mon.h"

#define _IGNORE BAD_CAST"ignore"
#define _ASSIGN(prop, item) \
{ \
	if (!xmlStrcmp(prop, _IGNORE)) \
		item = VAL_IGNORE; \
	else \
		item = atoi(prop); \
}

#define ALARM_DIR "/tmp/jw/alarm"

struct list gconf;

#ifndef NDEBUG
void dump_mon_conf()
{
	struct list *n, *nt;
	mon_conf_t *tmp;

	list_iterate_safe(n, nt, &gconf)
	{
		tmp = list_struct_base(n, mon_conf_t, list);
		printf("tmp addr: %.8x\n", tmp);
		printf("name: %s\n", tmp->name);
		printf("check_int: %d\n", tmp->check_int);
		printf("min_thr: %d\n", tmp->min_thr);
		printf("max_thr: %d\n", tmp->max_thr);
		printf("min_alr: %d\n", tmp->min_alr);
		printf("max_alr: %d\n", tmp->max_alr);
	}
}
#endif

bool create_default_conf(const char *file, const char *content)
{
	char _conf_dir[PATH_MAX], *p = NULL;
	int fd;

	strcpy(_conf_dir, file);
	if (! (p = strrchr(_conf_dir, '/')) )
		return false;

	*(p+1) = '\0';
	if (!mkdir_p(_conf_dir))
		return false;

	if ( (fd=open(file, O_CREAT | O_TRUNC | O_RDWR, S_IRWXU|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH)) > 0 )
	{
		write(fd, content, strlen(content));
		close(fd);
		syslog(LOG_INFO, "Create default conf %s", file);
		return true;
	}

	return false;
}

size_t mon_conf_load()
{
	xmlDocPtr doc;
	xmlNodePtr node;

	DBGP("into load conf! %s\n", MON_CONF);

	syslog(LOG_INFO, "%s", __func__);

	list_init(&gconf);

	if (access(MON_CONF, R_OK))
	{
		syslog(LOG_ERR, "the mon conf file %s not exists! default conf file will be created!", MON_CONF);
		if (!create_default_conf(MON_CONF, MON_CONF_CONTENT))
		{
			syslog(LOG_ERR, "create default conf file error!");
			kill(getpid(), SIGTERM);
			return -1;
		}
	}

	if ( (doc=xmlReadFile(MON_CONF, "UTF-8", XML_PARSE_RECOVER)) == NULL )
	{
		syslog(LOG_ERR, "fail to load xml conf!");
		return -1;
	}

	if ( (node=xmlDocGetRootElement(doc)) == NULL )
	{
		syslog(LOG_ERR, "load capture conf fail! nothing to load!");
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
			if (!isCaptureSupported(tgtName))
			{
				syslog(LOG_ERR, "%s : module not supported!", __func__);
			}
			else if ( (tmp=(mon_conf_t*)malloc(sizeof(mon_conf_t))) != NULL)
			{
				bzero(tmp, sizeof(mon_conf_t));

				strcpy(tmp->name, tgtName);
				tmp->check_int = atoi(tgtChkInt);
				_ASSIGN(tgtMinThr, tmp->min_thr);
				_ASSIGN(tgtMaxThr, tmp->max_thr);
				_ASSIGN(tgtMinAlr, tmp->min_alr);
				_ASSIGN(tgtMaxAlr, tmp->max_alr);
				update(tmp);
				tmp->_capture = capture_get(tgtName);
				sprintf(tmp->_alarm_file, "%s/%s", ALARM_DIR, tmp->name);
				list_add(&gconf, &tmp->list);

				syslog(LOG_INFO, "Load: %s (min_thr: %d, max_thr: %d, min_alr: %d, max_thr: %d, check_int: %d)",
						tmp->name, tmp->min_thr, tmp->max_thr, tmp->min_alr, tmp->max_alr, tmp->check_int);

#ifndef NDEBUG
				DBGP("check_int: %d / %s\n", tmp->check_int, tgtChkInt);
				DBGP("tmp addr: %.8x\n", tmp);
				dump_mon_conf();
#endif
			}
			else
			{
				syslog(LOG_ERR, "%s : alloc mem fail!", __func__);
			}
		}
		else
		{
			syslog(LOG_ERR, "%s : %s : get attr error!", __func__, node->name);
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

	syslog(LOG_INFO, "%s", __func__);

	list_iterate_safe(n, nt, &gconf)
	{
		tmp = list_struct_base(n, mon_conf_t, list);
		syslog(LOG_INFO, "Release: %s\n", tmp->name);
		list_del(n); free(tmp);
		DBGP("free node!\n");
	}
}
