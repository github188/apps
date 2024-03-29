#define _GNU_SOURCE
#include <libudev.h>
#include <stdlib.h>
#include <stdint.h>
#include <regex.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <ctype.h>
#include "clog.h"
#include "us_ev.h"
#include "types.h"
#include "disk_utils.h"
#include "us_disk.h"
#include "us_mon.h"
#include "script.h"
#include "safe_popen.h"
#include "list.h"

#define DISK_HOTREP_CONF "/opt/etc/disk/hotreplace.xml"
#define MAP_SLOT_CONF	 "/opt/jw-conf/disk/ata2slot.xml"

typedef struct slot_map slot_map_t;
struct slot_map {
	struct list slot_map_list;
	char hw_addr[16];
	int slot;
};

extern regex_t udev_sd_regex;
extern regex_t udev_usb_regex;
extern regex_t udev_md_regex;
extern regex_t udev_dom_disk_regex;
extern regex_t ata_disk_slot_regex;

int us_prewarn_flag = 0;

struct us_disk_pool us_dp;
struct list _g_slot_map_list;

static int find_slot(const char *path);
static int is_md(const char *path)
{
	return regexec(&udev_md_regex, path, 0, NULL, 0) == 0;
}

static void slot_map_release(void)
{
	 struct list *ptr;
	 struct list *n;
	 slot_map_t *slot_map_p;

	 list_for_each_safe(ptr, n, &_g_slot_map_list) {
	 		slot_map_p = list_entry(ptr, slot_map_t, slot_map_list);
	 		list_del(&slot_map_p->slot_map_list);
	 		free(slot_map_p);		
	 }
}

static int slot_map_init(void)
{
	xmlDocPtr doc;
	xmlNodePtr node;
	xmlChar *xmlhwaddr, *xmlslot;
	slot_map_t *slot_map_p;
	int ret = -1, i = 0, count = 0;

	init_list(&_g_slot_map_list);

	if ((doc=xmlReadFile(MAP_SLOT_CONF, "UTF-8", XML_PARSE_RECOVER)) == NULL) {
		clog(LOG_ERR, "%s: read config file %s error, file not found.\n",
			__func__, MAP_SLOT_CONF);
		return -1;
	}

	if ((node=xmlDocGetRootElement(doc)) == NULL) {
			clog(LOG_ERR, "%s: get xml root node error.\n", __func__);
			goto out;
	}

	node = node->xmlChildrenNode;

	while (node) {
		if ((!xmlStrcmp(node->name, (const xmlChar *)"map")) &&
		 ((xmlhwaddr=xmlGetProp(node, (const xmlChar *)"hw_addr")) != NULL) &&
		 ((xmlslot=xmlGetProp(node, (const xmlChar *)"slot")) != NULL)) {
			slot_map_p = (slot_map_t *)malloc(sizeof(slot_map_t));
			if (!slot_map_p) {
				clog(LOG_ERR, "%s: init slot map list error, no more memory.\n", __func__);
				goto mem_error;
			}
			list_add(&slot_map_p->slot_map_list, &_g_slot_map_list);
			++count;
			strncpy (slot_map_p->hw_addr, (const char *)xmlhwaddr,
				sizeof(slot_map_p->hw_addr));
			slot_map_p->slot = atoi((const char *)xmlslot);

			xmlFree(xmlhwaddr);
		}
		node = node->next;
	}

	/* check config file */
	for (i=1; i<=count; ++i) {
		struct list *ptr;
		slot_map_t *slot_map_p;
		int found = 0;
		list_for_each(ptr, &_g_slot_map_list) {
		 	slot_map_p = list_entry(ptr, slot_map_t, slot_map_list);
		 	if (i == slot_map_p->slot) {
				clog(LOG_INFO, "slot:%d, hw_addr: %s\n",  slot_map_p->slot,
					slot_map_p->hw_addr);
				found = 1;
		 	}
		}
		if (!found) {
			clog(LOG_ERR, "%s: config file: %s is not correct.\n",
				__func__, MAP_SLOT_CONF);
			clog(LOG_ERR, "%s: not found config for slot %d.\n",
				__func__, i);
			goto mem_error;
		}
	}
	
	ret = 0;

out:
	xmlFreeDoc(doc);
	xmlCleanupParser();
	return ret;

mem_error:
	slot_map_release();
	goto out;
}

static int find_slot(const char *path)
{
	/*
	 * example: ../devices/pci0000:00/0000:00:1c.1/0000:09:00.0/ata11/host10/target10:0:0/10:0:0:0/block/sdc
	 */
	int start = -1, end = -1, pos, count = 0;
	char hw_addr[16] = { '\0' };

	struct list *ptr;
	slot_map_t *slot_map_p;

	pos = strlen(path) - 1;
	if ('/' == path[pos])
		--pos;
	do {
		if ('/' == path[pos]) {
			++count;
			if (2 == count)
				end = pos - 1;
			else if (3 == count) {
				start = pos + 1;
				break;
			}
		}
	} while (--pos);

	if (end != -1 && start != -1 && end-start+1 >= 7)
		strncpy(hw_addr, &path[start], end-start+1);
	else
		return -1;

	 list_for_each(ptr, &_g_slot_map_list) {
	 	slot_map_p = list_entry(ptr, slot_map_t, slot_map_list);
	 	if (strcmp(hw_addr, slot_map_p->hw_addr) == 0) {
	 		return slot_map_p->slot;
	 	}
	 }
	 return -1;
}

#if 0
static int find_free_slot(struct us_disk_pool *dp)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(dp->disks); i++) {
		struct us_disk *disk = &dp->disks[i];

		if (!disk->is_exist)
			return i;
	}

	return -1;
}
#endif

struct us_disk *find_disk(struct us_disk_pool *dp, const char *dev)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(dp->disks); i++) {
		struct us_disk *disk = &dp->disks[i];

		if (!disk->is_exist)
			continue;
		if (strcmp(disk->dev_node, dev) == 0)
			return &dp->disks[i];
	}

	return NULL;
}

const char* __disk_get_hotrep(const char *serial, char *raid_name)
{
	xmlDocPtr doc;	// 定义文件指针
	xmlNodePtr node;
	static char __hotrep_type[128];
	char *hotrep_type = NULL;

	if ( (doc=xmlReadFile(DISK_HOTREP_CONF, "UTF-8", XML_PARSE_RECOVER)) == NULL)
		return NULL;

	// 获取根节点
	if ((node=xmlDocGetRootElement(doc)) == NULL)
		goto error_quit;

	// 获取节点内容
	node = node->xmlChildrenNode;
	memset(__hotrep_type, 0, sizeof(__hotrep_type));
	while (node)
	{
		xmlChar *xmlType, *xmlSerial, *xmlRaidName;
		if( (!xmlStrcmp(node->name, BAD_CAST"disk")) &&
		    ((xmlSerial=xmlGetProp(node, (const xmlChar *)"serial"))!=NULL ) &&
		    (!xmlStrcmp(xmlSerial, (const xmlChar *)serial)) )
		{
			hotrep_type = __hotrep_type;
			xmlType = xmlGetProp(node, (const xmlChar *)"type");
			strcpy(hotrep_type, (const char *)xmlType);
			// 如果是专用热备盘，同时提供对应的raid名称
			if (raid_name && !xmlStrcmp(xmlType, BAD_CAST"Special"))
			{
				xmlRaidName = xmlGetProp(node, (const xmlChar *)"md_name");
				strcpy(raid_name, (const char *)xmlRaidName);
				xmlFree(xmlRaidName);
			}
			xmlFree(xmlType);
			xmlFree(xmlSerial);
			break;
		}
		node = node->next;
	}

error_quit:
	xmlFreeDoc(doc);
	xmlCleanupParser();
	return hotrep_type;
}

static void do_update_disk(struct us_disk *disk, int op)
{
	const char *dev = disk->dev_node;

	if (!disk->is_exist)
		return;

	disk->is_fail = disk_get_fail(dev);

	if (op & DISK_UPDATE_SMART) {
		if (disk_get_smart_info(dev, &disk->di) < 0) {
			clog(LOG_ERR,
			     "%s: get disk smartinfo failed\n", __func__);
		}
	}
	if (op & DISK_UPDATE_RAID) {
		if (disk_get_raid_info(dev, &disk->ri) < 0) {
			clog(LOG_ERR,
			     "%s: get disk raid info failed\n", __func__);

		}
	}

	if (op & DISK_UPDATE_STATE) {
		// 从磁盘热备盘配置文件更新磁盘信息
		const char *hotrep = __disk_get_hotrep(disk->di.serial, NULL);
		printf("------------update disk, serial = %s, hotrep = %s\n", disk->di.serial, hotrep);
		disk->is_special = disk->is_global = 0;
		if (hotrep)
		{
			if (!strcmp(hotrep, "Special"))
				disk->is_special = 1;
			else if (!strcmp(hotrep, "Global"))
				disk->is_global = 1;
		}
	}
}

static void update_disk(struct us_disk_pool *dp, const char *dev)
{
	struct us_disk *disk = find_disk(dp, dev);
	if (!disk) {
		clog(LOG_WARNING, "%s: update %s doesn't exist\n",
		     __func__, dev);
		return;
	}

	do_update_disk(disk, DISK_UPDATE_RAID);
}

static void us_disk_update_all(int op)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];

		if (disk->is_exist)
			do_update_disk(disk, op);
	}
}

ssize_t disk_name2slot(const char *name, char *slot)
{
	int i;
	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];

		if (disk->is_exist)
		{
			sprintf(slot, "0:%d", disk->slot);
			return 0;
		}

	}
	return -EEXIST;
}

static void add_disk(struct us_disk_pool *dp, const char *dev, int slot)
{
	int i;
	struct us_disk *disk;
	size_t n;
	extern int disk_get_size(const char *dev, uint64_t *sz);

	disk = &dp->disks[slot];
	memset(disk, 0, sizeof(*disk));	// 磁盘掉线后会设置is_removed标志，需要清除
	n = sizeof(disk->dev_node);
	strncpy(disk->dev_node, dev, n);
	disk->dev_node[n - 1] = '\0';
	disk->slot = slot;
	disk->is_exist = 1;
	disk->ref = 1;

	for (i=0; i<ARRAY_SIZE(dp->disks); ++i) {
		if (!strcmp(disk->dev_node, dp->disks[i].dev_node) &&
			i != disk->slot) {
			dp->disks[i].dev_node[0] = '\0';
			break;
		}
	}

	do_update_disk(disk, DISK_UPDATE_RAID | DISK_UPDATE_SMART | DISK_UPDATE_STATE);

	if (us_prewarn_flag) {
		disk->di.wi.max_map_cnt = disk->di.size/1000000/512;
	} else {
		disk->di.wi.max_map_cnt = -1;
	}
}

static void remove_disk(struct us_disk_pool *dp, const char *dev)
{
	int slot;
	struct us_disk *disk = find_disk(dp, dev);
	if (!disk) {
		clog(LOG_WARNING, "%s: remove %s doesn't exist\n",
		     __func__, dev);
		return;
	}

	disk->ref--;
	slot = disk->slot;
	memset(disk, 0, sizeof(*disk));
	// 供磁盘掉线查询磁盘槽位号使用
	disk->is_removed = 1;
	disk->slot = slot;
	strcpy(disk->dev_node, dev);
}

static int us_disk_on_event(const char *path, const char *dev, const char *act)
{
	char cmd[128];
	int slot;
	clog(LOG_INFO, "%s: %s\n", dev, act);
	
	if (is_md(path)) {
		if (strcmp(act, MA_CHANGE) != 0 && strcmp(act, MA_ADD) != 0) {
			sprintf(cmd, "%s %s %s", MD_SCRIPT, dev, act);
			safe_system(cmd);
		}
		return MA_HANDLED;
	}

	if (strcmp(act, MA_ADD) == 0) {
		slot = find_slot(path);
		if (slot < 0) {
			clog(LOG_ERR, "%s: can't find slot for %s\n", __func__, path);
			return MA_NONE;
		}

		add_disk(&us_dp, dev, slot);

		sprintf(cmd, "%s %s %s", DISK_SCRIPT, dev, MA_ADD);
		safe_system(cmd);
	} else if (strcmp(act, MA_REMOVE) == 0) {
		sprintf(cmd, "%s %s %s", DISK_SCRIPT, dev, MA_REMOVE);
		safe_system(cmd);

		remove_disk(&us_dp, dev);
	} else if (strcmp(act, MA_CHANGE) != 0) {
		if (strcmp(act, MA_RDKICKED) == 0) {
			sprintf(cmd, "%s %s %s", DISK_SCRIPT, dev, act);
			safe_system(cmd);
			disk_set_fail(dev);
		}

		update_disk(&us_dp, dev);
	}

	return MA_HANDLED;
}

static struct mon_node us_disk_mon_node = {
	.on_event = us_disk_on_event,
};

int us_disk_init(void)
{
	if (slot_map_init() < 0) 
		return -1;
	memset(&us_dp, 0, sizeof(us_dp));
	us_mon_register_notifier(&us_disk_mon_node);

	return 0;
}

void us_disk_release(void)
{
	slot_map_release();
	us_mon_unregister_notifier(&us_disk_mon_node);
	memset(&us_dp, 0, sizeof(us_dp));
}

/**
 * User interface
 */
static struct us_disk *us_disk_find_by_slot(char *slot)
{
	char *s;
	char *p = NULL;
	int num;
	struct us_disk *disk;
	const char *delim = " \t:";

	s = strtok_r(slot, delim, &p);
	if (s == NULL)
		return NULL;
	if (*s != '0')
		return NULL;
	s = strtok_r(NULL, delim, &p);
	if (s == NULL)
		return NULL;
	num = atoi(s);
	if (num < 0 || num >= ARRAY_SIZE(us_dp.disks))
		return NULL;

	disk = &us_dp.disks[num];
	if (!disk->is_exist)
		return NULL;
	return disk;

}

const char *disk_get_state(const struct us_disk *disk)
{
	if (disk->is_special)
		return "Special";
	else if (disk->is_global)
		return "Global";
	else if (disk->is_fail)
		return "Fail";
	return disk_get_md_state(&(disk->ri));
}

void us_dump_disk(int fd, const struct us_disk *disk, int is_detail)
{
	char buf[4096];
	char *pos = &buf[0];
	char *end = &buf[sizeof(buf)];
	const char *delim = ", ";
	const struct disk_info *di = &disk->di;

	if (!disk->is_exist)
		return;

	/* get disk bad sector info first, make sure smart state correct */
	disk_get_warning_info(disk->dev_node, 
						(struct disk_warning_info *)&disk->di.wi);

	pos += snprintf(pos, end - pos, "{ ");
	pos += snprintf(pos, end - pos, "\"slot\":\"0:%u\"", disk->slot);
	pos += snprintf(pos, end - pos, "%s\"model\":\"%s\"", delim, di->model);
	pos += snprintf(pos, end - pos, "%s\"serial\":\"%s\"", delim, di->serial);
	pos += snprintf(pos, end - pos, "%s\"firmware\":\"%s\"", delim,
	                di->firmware);
	pos += snprintf(pos, end - pos, "%s\"capacity\":%llu", delim,
	                (unsigned long long)di->size);

	const char *p_state = disk_get_state(disk);
	pos += snprintf(pos, end - pos, "%s\"state\":\"%s\"", delim, p_state);

	const char *raid_name = disk_get_raid_name(disk);
	char p_raid[128];
	if (!strcmp(p_state, "Special") && !strcmp(raid_name, "N/A")) {
		__disk_get_hotrep(disk->di.serial, p_raid);
	} else {
		strncpy(p_raid, raid_name, sizeof(p_raid) - 1);
		p_raid[sizeof(p_raid) - 1] = 0;
	}

	pos += snprintf(pos, end - pos, "%s\"raid_name\":\"%s\"", delim, p_raid);

	if (!strcmp(p_state, "Fail"))
		pos += snprintf(pos, end - pos, "%s\"SMART\":\"Bad\"", delim);
	else
		pos += snprintf(pos, end - pos, "%s\"SMART\":\"%s\"", delim,
	                disk_get_smart_status(di));

	pos += snprintf(pos, end - pos, "%s\"dev\":\"%.*s\"", delim, 9,
					disk->dev_node);

	if (is_detail) {
		pos += snprintf(pos, end - pos, "%s\"bus_type\": \"SATA\"", delim);
		pos += snprintf(pos, end - pos, "%s\"rpm\":7200", delim);
		pos += snprintf(pos, end - pos, "%s\"wr_cache\": \"enable\"", delim);
		pos += snprintf(pos, end - pos, "%s\"rd_ahead\": \"enable\"", delim);
		pos += snprintf(pos, end - pos, "%s\"standby\":0", delim);
		pos += snprintf(pos, end - pos, "%s\"cmd_queue\": \"enable\"", delim);
		pos += snprintf(pos, end - pos, "%s\"mapped_cnt\": \"%u\"",
				delim, di->wi.mapped_cnt);
		if (di->wi.max_map_cnt != -1) {
			pos += snprintf(pos, end - pos, "%s\"max_map_cnt\": \"%u\"",
					delim, di->wi.max_map_cnt);
		} else {
			pos += snprintf(pos, end - pos, "%s\"max_map_cnt\": \"-1\"", delim);
		}
		pos += snprintf(pos, end - pos, "%s\"smart_attr\":{", delim);
		pos += snprintf(pos, end - pos, "\"read_err\":%llu",
		                (unsigned long long)di->si.read_error);
		pos += snprintf(pos, end - pos, "%s\"spin_up\":%llu",
		                delim, (unsigned long long)di->si.spin_up);
		pos += snprintf(pos, end - pos,
		                "%s\"reallocate_sectors\":%llu", delim,
		                (unsigned long long)di->si.reallocate_sectors);
		pos += snprintf(pos, end - pos,
		                "%s\"pending_sectors\":%llu", delim,
		                (unsigned long long)di->si.pending_sectors);
		pos += snprintf(pos, end - pos,
		                "%s\"uncorrectable\":%llu", delim,
		                (unsigned long long)di->si.uncorrectable_sectors);
		pos += snprintf(pos, end - pos, "%s\"power_on_hours\":%llu", delim,
		                (unsigned long long)di->si.power_on / 3600 / 1000);
		pos += snprintf(pos, end - pos, "%s\"temperature\":%.0f", delim,
		                di->si.temperature / 1000.0);
		pos += snprintf(pos, end - pos, "}");
	}

	pos += snprintf(pos, end - pos, " }");
	write(fd, buf, pos - buf);
}

void us_disk_dump(int fd, char *slot, int detail)
{
	const char *delim = "\n";
	char s[128];
	int i;
	int dev_no = 0;

	if (slot != NULL) {
		const struct us_disk *disk = us_disk_find_by_slot(slot);
		if (disk)
			us_dump_disk(fd, disk, detail);
		write(fd, delim, 1);

		return;
	}

	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];
		if (disk->is_exist)
			dev_no++;
	}

	sprintf(s, "{ \"total\":%u, \n\"rows\":[", dev_no);
	write(fd, s, strlen(s));
	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];

		if (disk->is_exist) {
			write(fd, delim, strlen(delim));
			us_dump_disk(fd, disk, detail);
			delim = ",\n";
		}
	}
	sprintf(s, "]\n}\n");
	write(fd, s, strlen(s));
}

static int us_disk_dump_slot_name(int fd, char *slot)
{
	const struct us_disk *disk;
	char name[128];

	disk = us_disk_find_by_slot(slot);
	if (disk == NULL)
		return 0;
	sprintf(name, "%s ", disk->dev_node);
	write(fd, name, strlen(name));
	return 1;
}

void us_disk_slot_to_name(int fd, char *slots)
{
	char *p;
	char *s;
	const char *delim = " \t,";
	int devs = 0;

	s = strtok_r(slots, delim, &p);
	while (s) {
		devs += us_disk_dump_slot_name(fd, s);
		s = strtok_r(NULL, delim, &p);
	}
	if (devs)
		write(fd, "\n", 1);
}

void us_disk_name_to_slot(int fd, char *name)
{
	int i;
	int slot = -1;
	char s[16];

	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];

		if (strcmp(disk->dev_node, name) == 0) {
			slot = disk->slot;
			if (disk->is_exist)
				break;
		}
	}
	
	if (slot != -1) {
		sprintf(s, "0:%u\n", slot);
		write(fd, s, strlen(s));
	}
}

void us_disk_update_slot(char *slot, const char *op)
{
	struct us_disk *disk;
	int update = DISK_UPDATE_ALL;

	if (op == NULL) {
		update = DISK_UPDATE_ALL;
	} else if (strcmp(op, "smart") == 0) {
		update = DISK_UPDATE_SMART;
	} else if (strcmp(op, "md") == 0) {
		update = DISK_UPDATE_RAID;
	} else if (strcmp(op, "state") == 0) {
		update = DISK_UPDATE_STATE;
	}

	if (slot == NULL) {
		us_disk_update_all(update);
		return;
	}
	disk = us_disk_find_by_slot(slot);
	if (disk == NULL)
		return;
	do_update_disk(disk, update);
}
