/* Exit 41 means missing export. Other nonzero codes identify a failed assertion. */
#include "timezone.h"

static DYNAMIC_TIME_ZONE_INFORMATION zone;
static void key(const char *name) {
    unsigned int i = 0;
    for (; name[i] && i < 127; i++) zone.key[i] = (unsigned char)name[i];
    zone.key[i] = 0;
}
static void check(convert_time convert, WORD year, WORD month, WORD hour, unsigned int failure) {
    SYSTEMTIME utc = {year, month, 0, 15, 12, 0, 0, 0}, local;
    if (!convert(&zone, &utc, &local) || local.year != year || local.month != month ||
        local.day != 15 || local.hour != hour || local.minute || local.second) ExitProcess(failure);
}
void mainCRTStartup(void) {
    convert_time convert = (convert_time)GetProcAddress(GetModuleHandleA("kernel32.dll"), "SystemTimeToTzSpecificLocalTimeEx");
    if (!convert) ExitProcess(41);
    key("Eastern Standard Time");
    check(convert, 2026, 1, 7, 51);
    check(convert, 2026, 7, 8, 52);
    check(convert, 2006, 3, 7, 53);
    check(convert, 2007, 3, 8, 54);
    key("AUS Eastern Standard Time");
    check(convert, 2026, 1, 23, 55);
    check(convert, 2026, 7, 22, 56);
    zone.key[0] = 0;
    zone.base.bias = -840; /* UTC+14, crossing into the next year. */
    SYSTEMTIME boundary = {2026, 12, 0, 31, 12, 0, 0, 0};
    if (!convert(&zone, &boundary, &boundary) || boundary.year != 2027 ||
        boundary.month != 1 || boundary.day != 1 || boundary.hour != 2) ExitProcess(57);
    zone.dynamic_disabled = 1;
    key("Eastern Standard Time"); /* Disabled dynamic rules must use the supplied fixed offset. */
    zone.base.bias = 0;
    check(convert, 2026, 1, 12, 58);
    SYSTEMTIME utc, actual, expected;
    GetSystemTime(&utc);
    if (!convert(0, &utc, &actual) || !SystemTimeToTzSpecificLocalTime(0, &utc, &expected)) ExitProcess(59);
    const WORD *a = (const WORD *)&actual, *b = (const WORD *)&expected;
    for (unsigned int i = 0; i < 8; i++) if (a[i] != b[i]) ExitProcess(60);
    if (convert(0, 0, &actual) || convert(0, &utc, 0)) ExitProcess(61);
    zone.dynamic_disabled = 0;
    key("Nonexistent test timezone");
    if (convert(&zone, &utc, &actual)) ExitProcess(62);
    ExitProcess(0);
}
