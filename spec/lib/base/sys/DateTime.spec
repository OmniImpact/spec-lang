#! Package base:sys
#! Calendar date and time representation with UTC/local timezone support,
#! duration arithmetic, and ISO-8601 formatting.

Class is DateTime{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
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

	## Returns the number of days in this DateTime's month.
	Function of Int is daysInCurrentMonth(){
		return daysInMonth(y: :year, m: :month);
	}

	## Returns the day of week (0=Sunday .. 6=Saturday) for the 1st of [month] in [year].
	Function of Int is firstDayOfMonthDow(Int is year, Int is month){
		local Int is z: daysFromCivil(y: year, m: month, d: 1);
		return floorMod(a: z + 4, b: 7);
	}

	## Returns true if [year], [month] (1..12), [day] (1..daysInMonth) is a valid calendar date.
	Function of Boolean is isValidDate(Int is year, Int is month, Int is day){
		if({ month < 1 || month > 12 }, { return false; });
		return day >= 1 && day <= daysInMonth(y: year, m: month);
	}

	## Returns true if [hour] (0..23), [minute] (0..59), [second] (0..59) is a valid wall-clock time.
	Function of Boolean is isValidTime(Int is hour, Int is minute, Int is second: 0){
		return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59 && second >= 0 && second <= 59;
	}

	## Clamps [day] into 1..daysInMonth(year, month).
	Function of Int is clampDay(Int is year, Int is month, Int is day){
		local Int is dim: daysInMonth(y: year, m: month);
		if({ day < 1 }, { return 1; });
		if({ day > dim }, { return dim; });
		return day;
	}

	## Returns a new DateTime with calendar date replaced, preserving time of day and offset.
	Function of DateTime is withDate(Int is year, Int is month, Int is day){
		local Int is m: if({ month < 1 }, { 1 }, { if({ month > 12 }, { 12 }, { month }) });
		local Int is d: clampDay(year: year, month: m, day: day);
		return :of(year: year, month: m, day: d, hour: :hour, minute: :minute, second: :second, millisecond: :millisecond, offsetSec: :offsetSec);
	}

	## Returns a new DateTime with wall-clock time replaced, preserving calendar date and offset.
	Function of DateTime is withTime(Int is hour, Int is minute, Int is second: 0, Int is millisecond: 0){
		local Int is h: if({ hour < 0 }, { 0 }, { if({ hour > 23 }, { 23 }, { hour }) });
		local Int is mn: if({ minute < 0 }, { 0 }, { if({ minute > 59 }, { 59 }, { minute }) });
		local Int is s: if({ second < 0 }, { 0 }, { if({ second > 59 }, { 59 }, { second }) });
		local Int is ms: if({ millisecond < 0 }, { 0 }, { if({ millisecond > 999 }, { 999 }, { millisecond }) });
		return :of(year: :year, month: :month, day: :day, hour: h, minute: mn, second: s, millisecond: ms, offsetSec: :offsetSec);
	}

	## Returns a new DateTime at 00:00:00.000 of the same date.
	Function of DateTime is startOfDay(){
		return withTime(hour: 0, minute: 0, second: 0, millisecond: 0);
	}

	## Returns a new DateTime on the 1st of the same month at 00:00:00.000.
	Function of DateTime is startOfMonth(){
		return :of(year: :year, month: :month, day: 1, hour: 0, minute: 0, second: 0, millisecond: 0, offsetSec: :offsetSec);
	}

	## Returns a new DateTime shifted by [months] calendar months (clamping day to month length).
	Function of DateTime is addMonths(Int is months){
		local Int is totalM: (:year * 12 + (:month - 1)) + months;
		local Int is ny: floorDiv(a: totalM, b: 12);
		local Int is nm: floorMod(a: totalM, b: 12) + 1;
		local Int is nd: clampDay(year: ny, month: nm, day: :day);
		return :of(year: ny, month: nm, day: nd, hour: :hour, minute: :minute, second: :second, millisecond: :millisecond, offsetSec: :offsetSec);
	}

	## Returns a new DateTime shifted by [years] calendar years (clamping Feb 29 if needed).
	Function of DateTime is addYears(Int is years){
		return addMonths(months: years * 12);
	}

	## Returns true if this DateTime has the same calendar year, month, and day as [other].
	Function of Boolean is isSameDate(DateTime is other){
		return :year == other:year && :month == other:month && :day == other:day;
	}

	## Returns 12-hour clock hour (1..12).
	Function of Int is hour12(){
		local Int is h: :hour % 12;
		return if({ h == 0 }, { 12 }, { h });
	}

	## Returns true if the hour is PM (12..23).
	Function of Boolean is isPm(){
		return :hour >= 12;
	}

	## Returns the full English month name for [month] (1..12).
	Function of String is monthName(Int is month){
		if({ month == 1 }, { return "January"; });
		if({ month == 2 }, { return "February"; });
		if({ month == 3 }, { return "March"; });
		if({ month == 4 }, { return "April"; });
		if({ month == 5 }, { return "May"; });
		if({ month == 6 }, { return "June"; });
		if({ month == 7 }, { return "July"; });
		if({ month == 8 }, { return "August"; });
		if({ month == 9 }, { return "September"; });
		if({ month == 10 }, { return "October"; });
		if({ month == 11 }, { return "November"; });
		if({ month == 12 }, { return "December"; });
		return "";
	}

	## Returns the 3-letter English month abbreviation for [month] (1..12).
	Function of String is monthShortName(Int is month){
		if({ month == 1 }, { return "Jan"; });
		if({ month == 2 }, { return "Feb"; });
		if({ month == 3 }, { return "Mar"; });
		if({ month == 4 }, { return "Apr"; });
		if({ month == 5 }, { return "May"; });
		if({ month == 6 }, { return "Jun"; });
		if({ month == 7 }, { return "Jul"; });
		if({ month == 8 }, { return "Aug"; });
		if({ month == 9 }, { return "Sep"; });
		if({ month == 10 }, { return "Oct"; });
		if({ month == 11 }, { return "Nov"; });
		if({ month == 12 }, { return "Dec"; });
		return "";
	}

	## Returns the 2-letter weekday header for [dow] (0=Sun .. 6=Sat).
	Function of String is weekdayShortName(Int is dow){
		if({ dow == 0 }, { return "Su"; });
		if({ dow == 1 }, { return "Mo"; });
		if({ dow == 2 }, { return "Tu"; });
		if({ dow == 3 }, { return "We"; });
		if({ dow == 4 }, { return "Th"; });
		if({ dow == 5 }, { return "Fr"; });
		if({ dow == 6 }, { return "Sa"; });
		return "";
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

	## Formats the wall-clock time as `HH:MM`.
	Function of String is formatTimeShort(){
		return pad2(n: :hour) . ":" . pad2(n: :minute);
	}

	## Formats the wall-clock time in 12-hour format (`hh:MM AM/PM`, optionally with seconds).
	Function of String is formatTime12(Boolean is includeSeconds: false){
		local String is suffix: if({ isPm() }, { "PM" }, { "AM" });
		local String is base: pad2(n: hour12()) . ":" . pad2(n: :minute);
		if({ includeSeconds }, {
			base: base . ":" . pad2(n: :second);
		});
		return base . " " . suffix;
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

	## Parses an ISO-8601 timestamp (`YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS[.mmm][Z|±HH:MM]`).
	## Returns [default] when [text] is malformed.
	Function of DateTime is parseIso(String is text, DateTime is default){
		local String is s: text:trim();
		if({ s:length() < 10 }, { return default; });
		if({ s:substring(start: 4, end: 5) != '-' || s:substring(start: 7, end: 8) != '-' }, { return default; });
		local Int is y: s:substring(start: 0, end: 4):parseInt(default: -1);
		local Int is mo: s:substring(start: 5, end: 7):parseInt(default: -1);
		local Int is d: s:substring(start: 8, end: 10):parseInt(default: -1);
		if({ y < 0 || !:isValidDate(year: y, month: mo, day: d) }, { return default; });
		local Int is h: 0;
		local Int is mi: 0;
		local Int is sec: 0;
		local Int is ms: 0;
		local Int is offSec: 0;
		local Int is pos: 10;
		local Int is n: s:length();
		if({ pos < n }, {
			local String is sep: s:substring(start: pos, end: pos + 1);
			if({ sep != 'T' && sep != 't' && sep != ' ' }, { return default; });
			pos: pos + 1;
			if({ pos + 5 > n }, { return default; });
			h: s:substring(start: pos, end: pos + 2):parseInt(default: -1);
			if({ s:substring(start: pos + 2, end: pos + 3) != ':' }, { return default; });
			mi: s:substring(start: pos + 3, end: pos + 5):parseInt(default: -1);
			pos: pos + 5;
			if({ pos + 3 <= n && s:substring(start: pos, end: pos + 1) == ':' }, {
				sec: s:substring(start: pos + 1, end: pos + 3):parseInt(default: -1);
				pos: pos + 3;
			});
			if({ !:isValidTime(hour: h, minute: mi, second: sec) }, { return default; });
			if({ pos < n && s:substring(start: pos, end: pos + 1) == '.' }, {
				pos: pos + 1;
				local Int is fStart: pos;
				local Boolean is readingFrac: true;
				while({ readingFrac && pos < n }, {
					local Int is ch: s:byteAt(index: pos, default: 0);
					if({ ch >= 48 && ch <= 57 }, { pos: pos + 1; }, { readingFrac: false; });
				});
				local String is frac: s:substring(start: fStart, end: pos);
				if({ frac:length() == 1 }, { ms: frac:parseInt(default: 0) * 100; });
				if({ frac:length() == 2 }, { ms: frac:parseInt(default: 0) * 10; });
				if({ frac:length() >= 3 }, { ms: frac:substring(start: 0, end: 3):parseInt(default: 0); });
			});
			if({ pos < n }, {
				local String is tz: s:substring(start: pos, end: pos + 1);
				if({ tz == 'Z' || tz == 'z' }, {
					offSec: 0;
				}, {
					if({ (tz == '+' || tz == '-') && pos + 6 <= n && s:substring(start: pos + 3, end: pos + 4) == ':' }, {
						local Int is oh: s:substring(start: pos + 1, end: pos + 3):parseInt(default: -1);
						local Int is om: s:substring(start: pos + 4, end: pos + 6):parseInt(default: -1);
						if({ oh < 0 || oh > 23 || om < 0 || om > 59 }, { return default; });
						offSec: oh * 3600 + om * 60;
						if({ tz == '-' }, { offSec: 0 - offSec; });
					}, {
						return default;
					});
				});
			});
		});
		return :of(year: y, month: mo, day: d, hour: h, minute: mi, second: sec, millisecond: ms, offsetSec: offSec);
	}

	replace Function of String is toString(){
		return formatIso();
	}
}
