#ifndef _VSD_NETLINK_H
#define _VSD_NETLINK_H

/* netlink protocol type */
#define NETLINK_VSD				31

/* warning area bit pos */
#define WARNING_AREA_SUPER 		0	/* super block io error */
#define WARNING_AREA_SECT_MAP	1	/* sector map io error */
#define WARNING_AREA_NEW_SECT	2	/* mapped new sector io error */
#define WARNING_AREA_BAD_SECT	3	/* bad sector map occur */

/* warning level for bad sector, other area alway warning */
#define WARNING_LEVEL_1			1	/* always warning */
#define WARNING_LEVEL_2			2	/* 10 bad sectors warning once */
#define WARNING_LEVEL_3			3	/* 100 bad sectors warning once */

struct vsd_warning_info {
	char disk_name[8];
	unsigned long warning_area;
	unsigned int mapped_cnt;
	unsigned int max_map_cnt;
};
#endif

