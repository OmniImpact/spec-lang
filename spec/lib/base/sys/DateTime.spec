#! Package base:sys
#! Calendar date and time representation with UTC/local timezone support,
#! duration arithmetic, and ISO-8601 formatting.

Class is DateTime{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Time()],
		['base', 'sys', as Conditional()]
	];

	local Int is epochMs: 0;
	local Int is offsetSec: 0;
	local Int is year: 1970;
	local Int is month: 1;
	local Int is day: 1;
	local Int is hour: 0;
	local Int is minute: 0;
	local Int is second: 0;
	local Int is millisecond: 0;
	local Int is dayOfWeek: 4;
	local Int is dayOfYear: 1;

	local Function of Int is floorDiv(Int is a, Int is b){
		local Int is q: a / b;
		local Int is r: a % b;
		if({ r != 0 && ((r < 0) != (b < 0)) }, {
			q: q - 1;
		});
		return q;
	}

	local Function of Int is floorMod(Int is a, Int is b){
		return a - floorDiv(a: a, b: b) * b;
	}

	local Function of Int is daysFromCivil(Int is y, Int is m, Int is d){
		local Int is adjY: y - if({ m <= 2 }, { 1 }, { 0 });
		local Int is era: floorDiv(a: adjY, b: 400);
		local Int is yoe: adjY - era * 400;
		local Int is adjM: m + if({ m > 2 }, { -3 }, { 9 });
		local Int is doy: (153 * adjM + 2) / 5 + d - 1;
		local Int is doe: yoe * 365 + (yoe / 4) - (yoe / 100) + doy;
		return era * 146097 + doe - 719468;
	}

	## Returns true if [y] is a Gregorian leap year.
	Function of Boolean is isLeap(Int is y){
		return ((y % 4 == 0) && (y % 100 != 0)) || (y % 400 == 0);
	}

	## Returns the number of days in [m] (1..12) for year [y].
	Function of Int is daysInMonth(Int is y, Int is m){
		if({ m == 2 }, {
			return if({ isLeap(y: y) }, { 29 }, { 28 });
		});
		if({ m == 4 || m == 6 || m == 9 || m == 11 }, {
			return 30;
		});
		return 31;
	}

	local Function is populateFromEpoch(DateTime is dt, Int is ms, Int is offset){
		dt:epochMs: ms;
		dt:offsetSec: offset;
		local Int is shiftedMs: ms + offset * 1000;
		local Int is totalSec: floorDiv(a: shiftedMs, b: 1000);
		local Int is remMs: shiftedMs - totalSec * 1000;
		local Int is z: floorDiv(a: totalSec, b: 86400);
		local Int is secOfDay: totalSec - z * 86400;

		dt:hour: secOfDay / 3600;
		local Int is remSec: secOfDay % 3600;
		dt:minute: remSec / 60;
		dt:second: remSec % 60;
		dt:millisecond: remMs;

		local Int is z2: z + 719468;
		local Int is era: floorDiv(a: z2, b: 146097);
		local Int is doe: z2 - era * 146097;
		local Int is yoe: (doe - (doe / 1460) + (doe / 36524) - (doe / 146096)) / 365;
		local Int is y: yoe + era * 400;
		local Int is doy: doe - (365 * yoe + (yoe / 4) - (yoe / 100));
		local Int is mp: (5 * doy + 2) / 153;
		local Int is d: doy - (153 * mp + 2) / 5 + 1;
		local Int is m: mp + if({ mp < 10 }, { 3 }, { -9 });
		if({ m <= 2 }, {
			y: y + 1;
		});

		dt:year: y;
		dt:month: m;
		dt:day: d;
		dt:dayOfWeek: floorMod(a: z + 4, b: 7);
		dt:dayOfYear: z - daysFromCivil(y: y, m: 1, d: 1) + 1;
	}

	## Returns the current local date and time.
	Function of DateTime is now(){
		local Int is ms: Time:nowMs();
		local Int is offset: Time:localOffsetSec(epochSec: ms / 1000);
		return fromEpochMs(epochMs: ms, offsetSec: offset);
	}

	## Returns the current UTC date and time.
	Function of DateTime is utcNow(){
		return fromEpochMs(epochMs: Time:nowMs(), offsetSec: 0);
	}

	## Constructs a DateTime from [epochMs] milliseconds since 1970-01-01T00:00:00Z
	## with an explicit timezone offset [offsetSec] in seconds.
	Function of DateTime is fromEpochMs(Int is epochMs, Int is offsetSec: 0){
		local DateTime is dt: DateTime:init();
		populateFromEpoch(dt: dt, ms: epochMs, offset: offsetSec);
		return dt;
	}

	## Constructs a DateTime from [epochMs] using the system's local timezone offset.
	Function of DateTime is fromLocalEpochMs(Int is epochMs){
		local Int is offset: Time:localOffsetSec(epochSec: epochMs / 1000);
		return fromEpochMs(epochMs: epochMs, offsetSec: offset);
	}

	## Constructs a DateTime from explicit calendar components.
	Function of DateTime is of(Int is year, Int is month, Int is day, Int is hour: 0, Int is minute: 0, Int is second: 0, Int is millisecond: 0, Int is offsetSec: 0){
		local Int is z: daysFromCivil(y: year, m: month, d: day);
		local Int is localSec: z * 86400 + hour * 3600 + minute * 60 + second;
		local Int is utcSec: localSec - offsetSec;
		local Int is ms: utcSec * 1000 + millisecond;
		return fromEpochMs(epochMs: ms, offsetSec: offsetSec);
	}

	Function of Int is getYear(){ return :year; }
	Function of Int is getMonth(){ return :month; }
	Function of Int is getDay(){ return :day; }
	Function of Int is getHour(){ return :hour; }
	Function of Int is getMinute(){ return :minute; }
	Function of Int is getSecond(){ return :second; }
	Function of Int is getMillisecond(){ return :millisecond; }
	Function of Int is getDayOfWeek(){ return :dayOfWeek; }
	Function of Int is getDayOfYear(){ return :dayOfYear; }
	Function of Int is getEpochMs(){ return :epochMs; }
	Function of Int is getEpochSec(){ return floorDiv(a: :epochMs, b: 1000); }
	Function of Int is getOffsetSec(){ return :offsetSec; }

	Function of Boolean is isLeapYear(){
		return isLeap(y: :year);
	}

	## Returns a new DateTime shifted by [ms] milliseconds.
	Function of DateTime is addMs(Int is ms){
		return fromEpochMs(epochMs: :epochMs + ms, offsetSec: :offsetSec);
	}

	## Returns a new DateTime shifted by [seconds] seconds.
	Function of DateTime is addSeconds(Int is seconds){
		return addMs(ms: seconds * 1000);
	}

	## Returns a new DateTime shifted by [minutes] minutes.
	Function of DateTime is addMinutes(Int is minutes){
		return addMs(ms: minutes * 60000);
	}

	## Returns a new DateTime shifted by [hours] hours.
	Function of DateTime is addHours(Int is hours){
		return addMs(ms: hours * 3600000);
	}

	## Returns a new DateTime shifted by [days] days.
	Function of DateTime is addDays(Int is days){
		return addMs(ms: days * 86400000);
	}

	## Returns the signed difference in milliseconds (`self - other`).
	Function of Int is diffMs(DateTime is other){
		return :epochMs - other:epochMs;
	}

	## Returns an equivalent DateTime in UTC (offset 0).
	Function of DateTime is toUtc(){
		return fromEpochMs(epochMs: :epochMs, offsetSec: 0);
	}

	## Returns an equivalent DateTime in the system's local timezone.
	Function of DateTime is toLocal(){
		return fromLocalEpochMs(epochMs: :epochMs);
	}

	local Function of String is pad2(Int is n){
		return if({ n < 10 }, { "0" . (n as String) }, { n as String });
	}

	local Function of String is pad3(Int is n){
		if({ n < 10 }, {
			return "00" . (n as String);
		});
		if({ n < 100 }, {
			return "0" . (n as String);
		});
		return n as String;
	}

	local Function of String is pad4(Int is n){
		if({ n < 0 }, {
			return "-" . pad4(n: -n);
		});
		if({ n < 10 }, {
			return "000" . (n as String);
		});
		if({ n < 100 }, {
			return "00" . (n as String);
		});
		if({ n < 1000 }, {
			return "0" . (n as String);
		});
		return n as String;
	}

	## Formats the calendar date as `YYYY-MM-DD`.
	Function of String is formatDate(){
		return pad4(n: :year) . "-" . pad2(n: :month) . "-" . pad2(n: :day);
	}

	## Formats the wall-clock time as `HH:MM:SS`.
	Function of String is formatTime(){
		return pad2(n: :hour) . ":" . pad2(n: :minute) . ":" . pad2(n: :second);
	}

	## Formats the date and time in ISO-8601 format (`YYYY-MM-DDTHH:MM:SS.mmmZ` or `±HH:MM`).
	Function of String is formatIso(){
		local String is base: formatDate() . "T" . formatTime() . "." . pad3(n: :millisecond);
		if({ :offsetSec == 0 }, {
			return base . "Z";
		});
		local String is sign: if({ :offsetSec >= 0 }, { "+" }, { "-" });
		local Int is absOff: if({ :offsetSec >= 0 }, { :offsetSec }, { -:offsetSec });
		local Int is offH: absOff / 3600;
		local Int is offM: (absOff % 3600) / 60;
		return base . sign . pad2(n: offH) . ":" . pad2(n: offM);
	}

	replace Function of String is toString(){
		return formatIso();
	}
}
