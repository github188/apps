#include <libudev.h>
#include <stdint.h>
#include <regex.h>
#include <errno.h>
#include <string.h>

#include "clog.h"
#include "us_ev.h"
#include "types.h"
#include "disk_utils.h"
#include "us_disk.h"
#include "us_mon.h"

struct us_disk {
	int		ref;
	int		slot;
	int             is_exist :1;
	int             is_raid : 1;
	char            dev_node[64];
	struct disk_info di;
	char            raid_uuid[64];

};

struct us_disk_pool {
	struct us_disk disks[MAX_SLOT];
};

extern regex_t udev_sd_regex;
extern regex_t udev_usb_regex;

static struct us_disk_pool us_dp;

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

static void dump_sd(struct us_disk *disk)
{
	struct disk_info *di;

	if (!disk->is_exist)
		return;
	di = &disk->di;
	printf("    %u - %s - %llu\n",
	       disk->slot,
	       disk->dev_node,
	       (unsigned long long)disk->di.size);

	printf("      Model: [%s]\n", di->model);
	printf("      Serial: [%s]\n", di->serial);
	printf("      Firmware: [%s]\n", di->firmware);

	if (di->is_smart_avail) {

		printf("      S.M.A.R.T:\n");
		printf("        Status: %s\n",
		       di->si.health_good?
		       (di->si.bad_sectors ? "Bad Sectors" : "Good") : "BAD");
		printf("        Bad Sectors: %llu\n",
		       (unsigned long long)di->si.bad_sectors);
		printf("        Power on hours: %llu\n",
		       (unsigned long long)(di->si.power_on / 1000 / 3600));
		printf("        Temperatur: %.1f C\n",
		       ((double)di->si.temperature) / 1000);
	}

	if (disk->is_raid)
		printf("        RAID: %s\n", disk->raid_uuid);
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

static void do_update_disk(struct us_disk *disk, const char *dev)
{
	if (disk_get_info(dev, &disk->di) < 0) {
		clog(LOG_ERR, "%s: get disk info failed\n", __func__);
	}
	if (disk_get_raid_info(dev, &disk->raid_uuid[0],
	                       sizeof(disk->raid_uuid)) == 0) {
		disk->is_raid = 1;
	} else {
		disk->is_raid = 0;
	}
	dump_sd(disk);
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
	do_update_disk(disk, dev);
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
	do_update_disk(disk, dev);
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
	if (!is_sata_sas(path))
		return MA_NONE;

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
