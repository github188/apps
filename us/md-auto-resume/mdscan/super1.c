/**
 * Super1 format support. Copy from mdadm.
 */
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/ioctl.h>

#include <sys/mount.h>


#include "ktypes.h"
#include "util.h"
#include "md_super.h"

#define SB_BLK_SZ (1024)

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

struct misc_dev_info {
	u64 device_size;
};

static void super1_free(struct super_type *st)
{
	if (st->superblock) {
		free(st->superblock);
		st->superblock = NULL;
	}
}

/**
 * load super block from disk. We only support 1.02 format.
 */
static int super1_load(struct super_type *st, int fd, const char *name)
{
	unsigned long long sb_offset;
	struct mdp_superblock_1 *super;

	super1_free(st);
	/**
	 * 4K from start of device.
	 */
	sb_offset = 8;
	ioctl(fd, BLKFLSBUF, 0);
	if (lseek64(fd, sb_offset * 512, 0) < 0LL) {
		fprintf(stderr, "Cannot seek to superblock on %s: %s\n",
		        name, strerror(errno));
		return -1;
	}

	/**
	 * We only use SB_BLK_SZ bytes, but for extension, we allocate all
	 * the memory according to mdadm.
	 */
	super = xmalloc(SB_BLK_SZ + sizeof(struct bitmap_super) +
	               sizeof(struct misc_dev_info));
	if (read(fd, super, SB_BLK_SZ) != SB_BLK_SZ) {
		fprintf(stderr, "Cannot read superblock on %s\n",
		        name);
		xfree(super);
		return -EIO;
	}
	if (le32_to_cpu(super->magic) != MD_SB_MAGIC) {
		fprintf(stderr, "No super block found on %s (Expected magic %08x, got %08x)\n",
		        name, MD_SB_MAGIC, le32_to_cpu(super->magic));
		xfree(super);
		return -EINVAL;
	}
	if (le32_to_cpu(super->major_version) != 1) {
		fprintf(stderr, "Invalidate version %d on %s\n",
		        le32_to_cpu(super->major_version), name);
		xfree(super);
		return -EINVAL;
	}
	if (le64_to_cpu(super->super_offset) != sb_offset) {
		fprintf(stderr, "No superblock found on %s (super_offset is wrong)\n",
		        name);
		xfree(super);
		return -EINVAL;
	}
/*
	if ((super->feature_map & MD_FEATURE_BITMAP_OFFSET) != 0) {
		fprintf(stderr, "%s: Cannot support bitmap.\n",
		        name);
		xfree(super);
		return -EINVAL;
	}
*/
	st->major = 1;
	st->minor = 2;
	st->superblock = super;
	st->data_offset = le64_to_cpu(super->data_offset);
	memcpy(st->device_uuid, super->device_uuid, sizeof(st->device_uuid));
	
	return 0;
}

/**
 * return:
 * 0	same.
 * -1	failed.
 */
static int super1_compare(struct super_type *st, struct super_type *tst)
{
	struct mdp_superblock_1 *first = st->superblock;
	struct mdp_superblock_1 *second = tst->superblock;

	if (memcmp(first->set_uuid, second->set_uuid,
	           sizeof(first->set_uuid)) != 0)
		return -1;

	if (first->ctime 	!= second->ctime	||
	    first->level	!= second->level	||
	    first->layout	!= second->layout	||
	    first->size		!= second->size		||
	    first->chunksize	!= second->chunksize	||
	    first->raid_disks	!= second->raid_disks)
		return -1;

	return 0;
}

static int super1_compare_info(struct md_info *info, struct super_type *tst)
{
	struct mdp_superblock_1 *sb = tst->superblock;
	if (memcmp(info->uuid, sb->set_uuid,16) != 0)
		return -1;
	if(strcmp(info->md_name, sb->set_name) != 0)
		return -1;
	if(info->level != le32_to_cpu(sb->level))
		return -1;
	if(info->raid_disks != le32_to_cpu(sb->raid_disks))
		return -1;
	return 0;
}

static void super1_get_info(struct super_type *st, struct md_info *info)
{
	struct mdp_superblock_1 *sb = st->superblock;

	info->major = 1;
	info->minor = 2;
	info->level = le32_to_cpu(sb->level);
	memcpy(info->uuid, sb->set_uuid, sizeof(info->uuid));
	strncpy(info->md_name, sb->set_name, sizeof(info->md_name));
	info->raid_disks = le32_to_cpu(sb->raid_disks);
}

struct super_ops super1 = {
	.load_super = super1_load,
	.free_super = super1_free,
	.compare_super = super1_compare,
	.compare_super_info = super1_compare_info,
	.get_info = super1_get_info,
};
