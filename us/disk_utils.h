#ifndef __DISK_UTILS_H
#define __DISK_UTILS_H

#include <stdint.h>

struct disk_smart_info {
	int		health_good;	/* 0: bad, 1: good */
	uint8_t		read_error;
	uint64_t	spin_up;
	uint64_t	reallocate_sectors;
	uint64_t	pending_sectors;
	uint64_t	uncorrectable_sectors;
	uint64_t	power_on;
	uint64_t	temperature;
};

struct disk_info {
	char		serial[21];
	char		firmware[9];
	char		model[41];
	uint64_t	size;
	int		is_smart_avail;
	struct disk_smart_info si;
};

struct disk_md_info {
	int		is_raid : 1;
	int		is_in_raid: 1;
	int		is_spare : 1;
	int		is_fault : 1;

	char            uuid[64];
};

void disk_get_smart_info(const char *dev, struct disk_info *info);
int disk_get_info(const char *dev, struct disk_info *info);
int disk_get_raid_info(const char *dev, struct disk_md_info *i);

static inline const char *disk_get_smart_status(const struct disk_info *info)
{
	if (!info->is_smart_avail)
		return "Nan";
	if (!info->si.health_good)
		return "BAD";
	if (info->si.pending_sectors || info->si.uncorrectable_sectors)
		return "BAD Sectors";
	return "GOOD";
}

static inline const char *disk_get_state(const struct disk_md_info *mi)
{
	const char *stat;

	if (mi->is_raid == 0)
		stat =  "Free";
	else if (!mi->is_in_raid)
		stat = "Inval";
	else if (mi->is_fault)
		stat = "Fault";
	else if (mi->is_spare)
		stat = "Spare";
	else
		stat = "Active";

	return stat;
}


#endif
