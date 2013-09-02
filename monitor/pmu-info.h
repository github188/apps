
#ifndef _PMU_INFO_H
#define _PMU_INFO_H

#define PMU_DEV1 "/proc/smbus-power/module1"
#define PMU_DEV2 "/proc/smbus-power/module2"

struct pmu_info {
	float	vin;
	float	vout;
	float	fan_speed;
	float	temp;

	int	is_vin_fault : 1,
		is_vout_fault : 1,
		is_fan_fault : 1,
		is_temp_fault : 1;
};

int pmu_get_info(const char *dev, struct pmu_info *info1, int check_temp);

#endif/*_PMU_INFO_H*/
