#include <regex.h>

/* udev PATH */
#define REG_UDEV_MD	"/block/md[[:digit:]]+$"
#define REG_MD_DISK_INFO 	\
	"Array UUID : (([[:xdigit:]]+:)+[[:xdigit:]]+).*"	\
	"Device Role : ([[:alpha:]]+)"

regex_t udev_md_regex;
regex_t md_disk_info_regex;

int us_regex_init(void)
{
	regcomp(&udev_md_regex, REG_UDEV_MD, REG_EXTENDED);
	regcomp(&md_disk_info_regex, REG_MD_DISK_INFO, REG_EXTENDED);

	return 0;
}

void us_regex_release(void)
{
	regfree(&udev_md_regex);
	regfree(&md_disk_info_regex);
}

