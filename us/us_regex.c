#include <regex.h>

/* udev PATH */
#define REG_UDEV_DISK	"/block/sd[a-z]+$"
#define REG_UDEV_MD	"/block/md[[:digit:]]+$"
#define REG_UDEV_USB	"/usb[0-9]+/"

#define REG_MD_DISK_INFO 	\
	"\\s*Array UUID \\s*:\\s*(([[:xdigit:]]+:)+[[:xdigit:]]+).*"	\
	"\\s*Device Role\\s*:\\s*([[:alpha:]]+)\\s*"

/*
 * 处理电子盘的匹配，可以适用下面的设备信息

   P: /devices/pci0000:00/0000:00:11.0/host0/target0:0:0/0:0:0:0/block/sda
   S: disk/by-id/ata-SanDisk_SSD_P4_8GB_110338302186
   S: disk/by-id/scsi-SATA_SanDisk_SSD_P4_110338302186
*/
#define REG_DOM_DISK	"host0/target0:0:0/.*/block/sd[a-z]+$"


regex_t udev_sd_regex;
regex_t udev_usb_regex;
regex_t udev_md_regex;
regex_t md_disk_info_regex;
regex_t udev_dom_disk_regex;

int us_regex_init(void)
{
	regcomp(&udev_sd_regex, REG_UDEV_DISK, REG_EXTENDED);
	regcomp(&udev_usb_regex, REG_UDEV_USB, REG_EXTENDED);
	regcomp(&udev_md_regex, REG_UDEV_MD, REG_EXTENDED);
	regcomp(&md_disk_info_regex, REG_MD_DISK_INFO, REG_EXTENDED);
	regcomp(&udev_dom_disk_regex, REG_DOM_DISK, REG_EXTENDED);

	return 0;
}

void us_regex_release(void)
{
	regfree(&udev_usb_regex);
	regfree(&udev_sd_regex);
	regfree(&udev_md_regex);
	regfree(&md_disk_info_regex);
}

