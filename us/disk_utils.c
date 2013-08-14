#include <sys/types.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdint.h>
#include <unistd.h>
#include <linux/fs.h> /*for BLKGETSIZE64 */
#include <atasmart.h>
#include <string.h>
#include <regex.h>
#include "disk_utils.h"
#include "clog.h"
#include "script.h"
#include "types.h"

static inline void set_value(uint64_t *dst, uint64_t src)
{
	if (src > *dst)
		*dst = src;
}


static void smart_cb(SkDisk *d, const SkSmartAttributeParsedData *a, void *arg)
{
	struct disk_smart_info *attr = arg;

	switch (a->pretty_unit) {
	case SK_SMART_ATTRIBUTE_UNIT_MKELVIN:
		if (strstr(a->name, "temperature") != NULL) {
			attr->temperature = a->pretty_value - 273150;
		}
		break;
	case SK_SMART_ATTRIBUTE_UNIT_MSECONDS:
		if (!strcmp(a->name, "spin-up-time"))
			set_value(&attr->spin_up, a->pretty_value);

		else if (strstr(a->name, "power-on") != NULL)
			set_value(&attr->power_on, a->pretty_value);

		break;
	case SK_SMART_ATTRIBUTE_UNIT_SECTORS:
		if (!strcmp(a->name, "reallocate-sector-count"))
			set_value(&attr->reallocate_sectors, a->pretty_value);

		else if (!strcmp(a->name, "current-pending-sector"))
			set_value(&attr->pending_sectors, a->pretty_value);

		else if (!strcmp(a->name, "offline-uncorrectable"))
			set_value(&attr->uncorrectable_sectors, a->pretty_value);
		break;
	case SK_SMART_ATTRIBUTE_UNIT_NONE:
		if (!strcmp(a->name, "raw-read-error-rate"))
			attr->read_error = a->current_value;
	default:
		break;
	}
}

void disk_get_smart_info(const char *dev, struct disk_info *info)
{
	SkDisk *d = NULL;
	int ret;
	SkBool avail;
	SkBool good;

	info->is_smart_avail = 0;
	memset(&info->si, 0, sizeof(info->si));

	ret = sk_disk_open(dev, &d);
	if (ret < 0)
		return;
	ret = sk_disk_smart_is_available(d, &avail);
	if (ret < 0 || avail == 0)
		goto finish;

	ret = sk_disk_smart_read_data(d);
	if (ret < 0)
		goto finish;

	info->is_smart_avail = 1;
	if ((ret = sk_disk_smart_status(d, &good)) < 0 ||
	    good == 0)
		info->si.health_good = 0;
	else
		info->si.health_good = 1;
	sk_disk_smart_parse_attributes(d, smart_cb, &info->si);
finish:
	sk_disk_free(d);
}

int disk_get_info(const char *dev, struct disk_info *info)
{
	SkDisk *d = NULL;
	int ret;
	const SkIdentifyParsedData *ipd;

	ret = sk_disk_open(dev, &d);
	if (ret < 0)
		return ret;

	if ((ret = sk_disk_get_size(d, &info->size)) < 0)
		goto out;

	if (info->size > 0)
		info->wi.max_map_cnt = info->size/1000000/512;

	if (sk_disk_identify_parse(d, &ipd) >= 0) {
		strncpy(info->serial, ipd->serial, sizeof(info->serial));
		info->serial[sizeof(info->serial) - 1] = '\0';
		strncpy(info->model, ipd->model, sizeof(info->model));
		info->model[sizeof(info->model) - 1] = '\0';
		strncpy(info->firmware, ipd->firmware, sizeof(info->firmware));
		info->firmware[sizeof(info->firmware) - 1] = '\0';
	} else {
		memset(info->serial, 0, sizeof(info->serial));
		memset(info->model, 0, sizeof(info->model));
		memset(info->firmware, 0, sizeof(info->firmware));
	}
out:
	sk_disk_free(d);
	return ret;
}

extern regex_t md_disk_info_regex;

extern int child_read(const char *cmd, char *buf, size_t *len);

static void disk_read_role(struct disk_md_info *mi, const char *dev)
{
	char cmd[128];
	char buf[1024];
	size_t len = sizeof(buf) - 1;
	int ret;
	char *s;
	const char *base;

	base = strrchr(dev, '/');
	if (base == NULL)
		base = dev;
	else
		base++;

	snprintf(cmd, sizeof(cmd),
	         "cat /proc/mdstat |grep %s", base);
	ret = child_read(cmd, buf, &len);

	if (ret || len == 0)
		return;

	buf[len] = '\0';

	s = strstr(buf, base);
	if (s == NULL)
		return;
	mi->is_in_raid = 1;
	s += strlen(base);

	/* format: dev[slot](F/S) */
	if (s >= &buf[len] || *s != '[') {
		mi->is_spare = 0;
		mi->is_fault = 0;
		return;
	}

	while (*s && *s != ']')
		s++;

	if (!*s) {
		mi->is_fault = 1;
		return;
	}
	s++;
	if (*s != '(') {
		mi->is_fault = 0;
		mi->is_spare = 0;
		return;
	}
	s++;

	switch (*s) {
	case 'S':
		mi->is_fault = 0;
		mi->is_spare = 1;
		return;
	default:
	case 'F':
		mi->is_fault = 1;
		mi->is_spare = 0;
		return;
	}
}

static void disk_update_uuid(struct disk_md_info *mi,
                             const char *buf, regmatch_t *p)
{
	int l = p->rm_eo - p->rm_so;
	if (l > sizeof(mi->uuid) - 1)
		l = sizeof(mi->uuid) - 1;
	strncpy(mi->uuid, &buf[p->rm_so], l);
	mi->uuid[l] = '\0';
}

static int disk_read_mdinfo(const char *cmd, struct disk_md_info *mi)
{
	FILE *fp;
	char buf[4096];
	int r;
	regmatch_t pmatch[5];
	int ret = -1;

	memset(pmatch, 0, sizeof(pmatch));
	fp = popen(cmd, "r");
	if (fp == NULL)
		return -1;

	r = fread(buf, 1, sizeof(buf) - 1, fp);
	if (r <= 0) {
		memset(mi, 0, sizeof(*mi));
		goto out;
	}

	buf[r] = '\0';
	if (regexec(&md_disk_info_regex, buf,
	            ARRAY_SIZE(pmatch), pmatch, 0) == 0) {
		mi->is_raid = 1;
		disk_update_uuid(mi, buf, &pmatch[1]);
		ret = 0;
	} else {
		memset(mi, 0, sizeof(*mi));
	}

out:
	pclose(fp);
	return ret;
}

int disk_get_raid_info(const char *dev, struct disk_md_info *mi)
{
	char cmd[128];
	int ret;

	snprintf(cmd, sizeof(cmd), SH_GET_MD_DISK, dev);
	mi->is_raid = 0;
	mi->is_in_raid = 0;
	ret = disk_read_mdinfo(cmd, mi);
	if (ret == 0)
		disk_read_role(mi, dev);

	return 0;
}

#define DISK_FAIL_FLAG		"624938716_FAIL_364996698"
void disk_set_fail(const char *dev)
{
	FILE *fp;
	
	fp = fopen(dev, "w");
	if (!fp)
		return;

	fwrite(DISK_FAIL_FLAG, strlen(DISK_FAIL_FLAG), 1, fp);
	fclose(fp);
}

int disk_get_fail(const char *dev)
{
	char buf[strlen(DISK_FAIL_FLAG)+1];
	FILE *fp;

	fp = fopen(dev, "r");
	if (!fp)
		return 0;

	memset(buf, 0x0, sizeof(buf));
	fread(buf, strlen(DISK_FAIL_FLAG), 1, fp);
	fclose(fp);

	return !strcmp(buf, DISK_FAIL_FLAG);
}

