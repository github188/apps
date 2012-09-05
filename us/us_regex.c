#include <regex.h>

/* udev PATH */
#define REG_UDEV_DISK	"/block/sd[a-z]+$"
#define REG_UDEV_MD	"/block/md[[:digit:]]+$"
#define REG_UDEV_USB	"/usb[0-9]+/"

#define REG_MD_DISK_INFO 	\
	"\\s*Array UUID \\s*:\\s*(([[:xdigit:]]+:)+[[:xdigit:]]+).*"	\
	"\\s*Device Role\\s*:\\s*([[:alpha:]]+)\\s*"



regex_t udev_sd_regex;
regex_t udev_usb_regex;
regex_t udev_md_regex;
regex_t md_disk_info_regex;

int us_regex_init(void)
{
	regcomp(&udev_sd_regex, REG_UDEV_DISK, REG_EXTENDED);
	regcomp(&udev_usb_regex, REG_UDEV_USB, REG_EXTENDED);
	regcomp(&udev_md_regex, REG_UDEV_MD, REG_EXTENDED);
	regcomp(&md_disk_info_regex, REG_MD_DISK_INFO, REG_EXTENDED);

	return 0;
}

void us_regex_release(void)
{
	regfree(&udev_usb_regex);
	regfree(&udev_sd_regex);
	regfree(&udev_md_regex);
	regfree(&md_disk_info_regex);
}

