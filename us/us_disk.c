#include <libudev.h>
#include <stdint.h>
#include <regex.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include "clog.h"
#include "us_ev.h"
#include "types.h"
#include "disk_utils.h"
#include "us_disk.h"
#include "us_mon.h"
#include "script.h"
#include "safe_popen.h"

struct us_disk {
	int		ref;
	int		slot;
	int             is_exist :1;
	int             is_raid : 1;
	char            dev_node[64];
	struct disk_info di;
	struct disk_md_info ri;
};

struct us_disk_pool {
	struct us_disk disks[MAX_SLOT];
};

extern regex_t udev_sd_regex;
extern regex_t udev_usb_regex;
extern regex_t udev_md_regex;

static struct us_disk_pool us_dp;

static int is_md(const char *path)
{
	return regexec(&udev_md_regex, path, 0, NULL, 0) == 0;
}

static int is_usb(const char *path)
{
	int ret;
	ret = regexec(&udev_usb_regex, path, 0, NULL, 0);
	return ret == 0;
}

static int is_sd(const char *path)
{
	int ret;
	ret = regexec(&udev_sd_regex, path, 0, NULL, 0);
	return ret == 0;
}

static int is_sata_sas(const char *path)
{
	return is_sd(path) && !is_usb(path);
}

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

static int find_disk(struct us_disk_pool *dp, const char *dev)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(dp->disks); i++) {
		struct us_disk *disk = &dp->disks[i];

		if (!disk->is_exist)
			continue;
		if (strcmp(disk->dev_node, dev) == 0)
			return i;
	}

	return -1;
}

static void do_update_disk(struct us_disk *disk, int op)
{
	const char *dev = disk->dev_node;

	if (!disk->is_exist)
		return;

	if (op & DISK_UPDATE_SMART) {
		if (disk_get_info(dev, &disk->di) < 0) {
			clog(LOG_ERR,
			     "%s: get disk smart info failed\n", __func__);
		}
		disk_get_smart_info(dev, &disk->di);
	}
	if (op & DISK_UPDATE_RAID) {
		if (disk_get_raid_info(dev, &disk->ri) < 0) {
			clog(LOG_ERR,
			     "%s: get disk raid info failed\n", __func__);

		}
	}
}

static void update_disk(struct us_disk_pool *dp, const char *dev)
{
	int slot = find_disk(dp, dev);
	struct us_disk *disk;

	if (slot < 0) {
		clog(LOG_WARNING, "%s: update %s doesn't exist\n",
		     __func__, dev);
		return;
	}
	disk = &dp->disks[slot];
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

static void add_disk(struct us_disk_pool *dp, const char *dev)
{
	int slot;
	struct us_disk *disk;
	size_t n;
	extern int disk_get_size(const char *dev, uint64_t *sz);

	slot = find_free_slot(dp);
	if (slot < 0) {
		clog(LOG_ERR, "%s: no free slots\n", __func__);
		return;
	}

	disk = &dp->disks[slot];
	n = sizeof(disk->dev_node);
	strncpy(disk->dev_node, dev, n);
	disk->dev_node[n - 1] = '\0';
	disk->slot = slot;
	disk->is_exist = 1;
	disk->ref = 1;
	do_update_disk(disk, DISK_UPDATE_RAID |DISK_UPDATE_SMART);
}

static void remove_disk(struct us_disk_pool *dp, const char *dev)
{
	int slot = find_disk(dp, dev);
	struct us_disk *disk;

	if (slot < 0) {
		clog(LOG_WARNING, "%s: remove %s doesn't exist\n",
		     __func__, dev);
		return;
	}
	disk = &dp->disks[slot];
	disk->ref--;
	memset(disk, 0, sizeof(*disk));
}

static int us_disk_on_event(const char *path, const char *dev, int act)
{
	if (is_md(path)) {
		char cmd[128];

		sprintf(cmd, "%s %s %s",
		        MD_SCRIPT, dev,
		        act == MA_ADD ? "add" :
		        act == MA_REMOVE ? "remove" : "change");
		safe_system(cmd);

		return MA_HANDLED;
	}

	if (!is_sata_sas(path))
		return MA_NONE;

	printf("%s: %d\n", dev, act);

	if (act == MA_ADD)
		add_disk(&us_dp, dev);
	else if (act == MA_REMOVE)
		remove_disk(&us_dp, dev);
	else if (act == MA_CHANGE)
		update_disk(&us_dp, dev);

	return MA_HANDLED;
}

static struct mon_node us_disk_mon_node = {
	.on_event = us_disk_on_event,
};

int us_disk_init(void)
{
	memset(&us_dp, 0, sizeof(us_dp));
	us_mon_register_notifier(&us_disk_mon_node);

	return 0;
}

void us_disk_release(void)
{
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

void us_dump_disk(int fd, const struct us_disk *disk, int is_detail)
{
	char buf[4096];
	char *pos = &buf[0];
	char *end = &buf[sizeof(buf)];
	const char *delim = ", ";
	const struct disk_info *di = &disk->di;

	if (!disk->is_exist)
		return;
	pos += snprintf(pos, end - pos, "{ ");
	pos += snprintf(pos, end - pos, "\"slot\":\"0:%u\"", disk->slot);
	pos += snprintf(pos, end - pos, "%s\"model\":\"%s\"", delim,
	                di->model);
	pos += snprintf(pos, end - pos, "%s\"serial\":\"%s\"", delim,
	                di->serial);
	pos += snprintf(pos, end - pos, "%s\"capacity\":\"%llu\"", delim,
	                (unsigned long long)di->size);
	pos += snprintf(pos, end - pos, "%s\"state\":\"%s\"", delim,
	                disk_get_state(&disk->ri));
	pos += snprintf(pos, end - pos, "%s\"SMART\":\"%s\"", delim,
	                disk_get_smart_status(di));

	if (is_detail) {
		pos += snprintf(pos, end - pos, "%s\"bus_type\": \"NaN\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"rpm\": \"NaN\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"wr_cache\": \"enable\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"rd_ahead\": \"enable\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"standby\": \"0\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"cmd_queue\": \"enable\"",
		                delim);
		pos += snprintf(pos, end - pos, "%s\"smart_attr\":{", delim);
		pos += snprintf(pos, end - pos, "\"read_err\":\"%llu\"",
		                (unsigned long long)di->si.spin_up);
		pos += snprintf(pos, end - pos, "%s\"spin_up\":\"%llu\"",
		                delim, (unsigned long long)di->si.spin_up);
		pos += snprintf(pos, end - pos,
		                "%s\"reallocate_sectors\":\"%llu\"", delim,
		                (unsigned long long)di->si.reallocate_sectors);
		pos += snprintf(pos, end - pos,
		                "%s\"pending_sectors\":\"%llu\"", delim,
		                (unsigned long long)di->si.pending_sectors);
		pos += snprintf(pos, end - pos,
		                "%s\"uncorrectable\":\"%llu\"", delim,
		                (unsigned long long)di->si.uncorrectable_sectors);
		pos += snprintf(pos, end - pos, "%s\"power_on_hours\":\"%llu\"",
		                delim,
		                (unsigned long long)di->si.power_on / 3600 / 1000);
		pos += snprintf(pos, end - pos, "%s\"temperature\":\"%.0f\"",
		                delim,
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
		}
		delim = ",\n";
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

	for (i = 0; i < ARRAY_SIZE(us_dp.disks); i++) {
		struct us_disk *disk = &us_dp.disks[i];

		if (disk->is_exist &&
		    strcmp(disk->dev_node, name) == 0) {
			char s[16];

			sprintf(s, "0:%u\n", disk->slot);
			write(fd, s, strlen(s));
			break;
		}
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