#include <sys/types.h>
#include "list.h"

#ifndef US_DISK_H
#define US_DISK_H

void us_disk_update_slot(char *slot, const char *op);
void us_disk_name_to_slot(int fd, char *name);
void us_disk_slot_to_name(int fd, char *slots);
void us_disk_dump(int fd, char *slot, int detail);

ssize_t disk_name2slot(const char *name, char *slot);

enum {
	DISK_UPDATE_SMART	= (1 << 0),
	DISK_UPDATE_RAID	= (1 << 1),
	DISK_UPDATE_STATE	= (1 << 2),

	DISK_UPDATE_ALL		= 0xff,
};

typedef struct slot_map slot_map_t;
struct slot_map {
	struct list slot_map_list;
	int ata_lower;
	int ata_upper;
	int slot_lower;
};
#endif
