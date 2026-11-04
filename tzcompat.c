#include "timezone.h"

/* Compose existing Wine APIs instead of calling its unimplemented Ex export. */
__declspec(dllexport) int SystemTimeToTzSpecificLocalTimeEx(
    const DYNAMIC_TIME_ZONE_INFORMATION *dynamic,
    const SYSTEMTIME *utc, SYSTEMTIME *local
) {
    if (!utc || !local) { SetLastError(87); return 0; }
    DYNAMIC_TIME_ZONE_INFORMATION current;
    if (!dynamic) {
        if (GetDynamicTimeZoneInformation(&current) == 0xffffffffu) return 0;
        dynamic = &current;
    }
    int historical = dynamic->key[0] && !dynamic->dynamic_disabled;
    TIME_ZONE_INFORMATION rules = {0};
    if (historical) {
        if (!GetTimeZoneInformationForYear(utc->year, dynamic, &rules)) return 0;
    } else {
        rules.bias = dynamic->base.bias;
        rules.standard_bias = dynamic->base.standard_bias;
        rules.daylight_bias = dynamic->base.daylight_bias;
        rules.standard_date = dynamic->base.standard_date;
        rules.daylight_date = dynamic->base.daylight_date;
    }
    /* Keep utc intact when caller passes the same input and output buffer. */
    SYSTEMTIME result;
    if (!SystemTimeToTzSpecificLocalTime(&rules, utc, &result)) return 0;
    if (historical && result.year != utc->year) {
        if (!GetTimeZoneInformationForYear(result.year, dynamic, &rules)) return 0;
        if (!SystemTimeToTzSpecificLocalTime(&rules, utc, &result)) return 0;
    }
    *local = result;
    return 1;
}
