typedef unsigned short WORD;
typedef unsigned int DWORD;
typedef int LONG;
typedef struct { WORD year, month, weekday, day, hour, minute, second, milliseconds; } SYSTEMTIME;
typedef struct {
    LONG bias;
    WORD standard_name[32];
    SYSTEMTIME standard_date;
    LONG standard_bias;
    WORD daylight_name[32];
    SYSTEMTIME daylight_date;
    LONG daylight_bias;
} TIME_ZONE_INFORMATION;
typedef struct {
    TIME_ZONE_INFORMATION base;
    WORD key[128];
    unsigned char dynamic_disabled;
} DYNAMIC_TIME_ZONE_INFORMATION;
_Static_assert(sizeof(TIME_ZONE_INFORMATION) == 172, "Windows timezone ABI");
_Static_assert(sizeof(DYNAMIC_TIME_ZONE_INFORMATION) == 432, "Windows dynamic timezone ABI");
__declspec(dllimport) void *GetModuleHandleA(const char *);
__declspec(dllimport) void *GetProcAddress(void *, const char *);
__declspec(dllimport) void GetSystemTime(SYSTEMTIME *);
__declspec(dllimport) DWORD GetDynamicTimeZoneInformation(DYNAMIC_TIME_ZONE_INFORMATION *);
__declspec(dllimport) int GetTimeZoneInformationForYear(WORD, const DYNAMIC_TIME_ZONE_INFORMATION *, TIME_ZONE_INFORMATION *);
__declspec(dllimport) int SystemTimeToTzSpecificLocalTime(const TIME_ZONE_INFORMATION *, const SYSTEMTIME *, SYSTEMTIME *);
__declspec(dllimport) void SetLastError(DWORD);
__declspec(dllimport) __declspec(noreturn) void ExitProcess(unsigned int);
typedef int (*convert_time)(const DYNAMIC_TIME_ZONE_INFORMATION *, const SYSTEMTIME *, SYSTEMTIME *);
