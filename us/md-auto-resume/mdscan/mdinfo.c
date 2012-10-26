#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include "md_super.h"
#include "dev_manage.h"

struct mdp_superblock_1 {
	le32	magic;		/* MD_SB_MAGIC: 0xa92b4efc - le */
	le32	major_version;	/* 1 */
	le32	feature_map;	/* 0 */
	le32	pad0;		/* 0 */

	u8	set_uuid[16];	/* user-space generated */
	char	set_name[32];	/* set and interpreted by user-space */
	le64	ctime;		/* lo 40 bits are seconds,
				 * top 24 are microseconds */
	le32	level;		/* -4 (multipath), -1 (linear),
				   0, 1, 4, 5 */
	le32	layout;		/* for raid5 */
	le64	size;		/* used size of component devices,
				 * in 512byte sectors */
	le32	chunksize;	/* in 512 byte sectors */
	le32	raid_disks;	/* number of raid disks */
	le32	bitmap_offset;
	le32	new_level;
	le64	reshape_position;
	le32	delta_disks;	/* change in number of raid_disks */
	le32	new_layout;
	le32	new_chunk;
	u8	pad1[128-124];

	/* constant this-device information - 64 bytes */
	le64	data_offset;	/* sector start of data, often 0 */
	le64	data_size;	/* sectors in this device for data */
	le64	super_offset;	/* sector start of this superblock */
	le64	recovery_offset;/* sectors before this offset have been
		                 * recovered */
	le32	dev_number;	/* permanent identifier of this device */
	le32	cnt_corrected_read; /* number of read errors that were corrected
		                     * by re-writing */
	u8	device_uuid[16]; /* set by user-space */
	u8	devflags;
	u8	pad2[64 - 57];

	/* array state information - 64 bytes */
	le64	utime;		/* lo 40 bites second, hi 24 bits microseconds
				 * */
	le64	events;		/* incremented when superblock updated. */
	le64	resync_offset;	/* data before this offset is in sync. */
	le32	sb_csum;	/* checksum upto devs[max_dev] */
	le32	max_dev;	/* sizeof devs[] array */
	u8	pad3[64 - 32];

	/* device state information. Indexed by dev_number.
	 * 2 bytes per device.
	 */

	le16	dev_roles[0];
} PACKED;


static void show_info(struct md_ident *id)
{
	struct md_info *info = &id->info;
	struct list *pos;

	printf("Get md: %.32s, level=%d, disks=%u, md_num: %u\n",
	       info->md_name,
	       info->level, info->raid_disks, id->md_num);
	list_for_each(pos, &id->dev_list) {
		struct md_dev *dev;

		dev = list_entry(pos, struct md_dev, dev_list);
		printf("\t%s\n", dev->name);
	}
}

int main(int argc, char *argv[])
{
	LIST(dlist);
	struct list *pos;

	load_md_devs(&dlist);
	list_for_each(pos, &dlist) {
		struct md_ident *id = list_entry(pos, struct md_ident, list);

		show_info(id);
	}
	free_md_devs(&dlist);

	return 0;
}

