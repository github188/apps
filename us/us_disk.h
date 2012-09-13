#ifndef US_DISK_H
#define US_DISK_H

#define MAX_SLOT	(128)
void us_disk_update_slot(char *slot, const char *op);
void us_disk_name_to_slot(int fd, char *name);
void us_disk_slot_to_name(int fd, char *slots);
void us_disk_dump(int fd, char *slot, int detail);

enum {
	DISK_UPDATE_SMART	= (1 << 0),
	DISK_UPDATE_RAID	= (1 << 1),

	DISK_UPDATE_ALL		= 0xff,
};

#endif