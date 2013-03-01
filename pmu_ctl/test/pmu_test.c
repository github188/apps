#include <stdio.h>
#include "../pmu_ctl.h"

static void dump_info(struct pmu_info *info)
{
	printf("vout:    %.2f\n", info->vout);
	printf("vin:     %.2f\n", info->vin);
	printf("temp:    %.2f\n", info->temp);
	printf("fan:     %.2f\n", info->fan_speed);
	printf("FAULT:   ");
	if (info->is_vout_fault)
		printf(" VOUT");
	if (info->is_vin_fault)
		printf(" VIN");
	if (info->is_temp_fault)
		printf(" TEMP");
	if (info->is_fan_fault)
		printf(" FAN");
}

int main(int argc, char *argv[])
{
	int ret;
	struct pmu_info info;

	ret = pmu_get_info(PMU1_DEV, &info);
	printf("ret = %d\n", ret);
	if (ret < 0) {
		fprintf(stderr, "Get pm information failed\n");
		return -1;
	} else {
		dump_info(&info);
	}

	return 0;
}
