#! specunit: suite
#! Unit tests for base:sys:Time (high-res timing and callback timers)
#! and base:sys:DateTime (calendar date/time, arithmetic, ISO-8601 formatting).

Class of SpecUnitTest is TestTime{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Time()],
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Function is testMonotonicClocks(){
		local Int is ns1: Time:monotonicNs();
		local Int is us1: Time:monotonicUs();
		local Int is ms1: Time:monotonicMs();
		Assert:isTrue(ns1 > 0);
		Assert:isTrue(us1 > 0);
		Assert:isTrue(ms1 >= 0);

		Time:sleepMs(ms: 5);

		local Int is ns2: Time:monotonicNs();
		local Int is us2: Time:monotonicUs();
		local Int is ms2: Time:monotonicMs();
		Assert:isTrue(ns2 > ns1);
		Assert:isTrue(us2 > us1);
		Assert:isTrue(ms2 >= ms1);
		Assert:isTrue((ns2 - ns1) >= 3000000);
	}

	Function is testEpochWallClock(){
		local Int is ms: Time:nowMs();
		local Int is ns: Time:nowNs();
		local Int is sec: Time:nowSec();
		# Sanity: after 2020-01-01T00:00:00Z (1577836800s)
		Assert:isTrue(sec > 1577836800);
		Assert:isTrue(ms > 1577836800000);
		Assert:isTrue(ns > 1577836800000000000);
	}

	Function is testPrecisionSleepAndMeasure(){
		local Int is elapsedUs: Time:measureUs(action: {
			Time:sleepUs(us: 5000);
		});
		Assert:isTrue(elapsedUs >= 3000);

		local Int is elapsedNs: Time:measureNs(action: {
			Time:sleepNs(ns: 2000000);
		});
		Assert:isTrue(elapsedNs >= 1000000);

		local Int is target: Time:monotonicNs() + 4000000;
		Time:sleepUntilNs(targetNs: target);
		Assert:isTrue(Time:monotonicNs() >= target);
	}

	Function is testSynchronousCallbackTimers(){
		local Int is fired: 0;
		local Int is elapsedMs: Time:measureMs(action: {
			Time:after(ms: 5, callback: {
				fired: fired + 1;
			});
		});
		Assert:areEqualInt(1, fired);
		Assert:isTrue(elapsedMs >= 3);

		local Int is ticks: 0;
		Time:interval(intervalMs: 3, count: 4, callback: {
			ticks: ticks + 1;
		});
		Assert:areEqualInt(4, ticks);

		local Int is everyCount: 0;
		Time:every(intervalMs: 2, callback: {
			everyCount: everyCount + 1;
			return everyCount < 3;
		});
		Assert:areEqualInt(3, everyCount);
	}

	Function is testAsyncTimersAndCancellation(){
		local Int is timeoutHits: 0;
		local Int is t1: Time:setTimeout(ms: 15, callback: {
			timeoutHits: timeoutHits + 1;
		});
		Assert:isTrue(t1 > 0);

		local Int is intervalHits: 0;
		local Int is t2: Time:setInterval(ms: 10, count: 3, callback: {
			intervalHits: intervalHits + 1;
		});
		Assert:isTrue(t2 > t1);

		local Int is cancelledHits: 0;
		local Int is t3: Time:setTimeout(ms: 500, callback: {
			cancelledHits: cancelledHits + 1;
		});
		Assert:isTrue(Time:cancelTimer(timerId: t3));

		# Wait for t1 and t2 to finish
		Time:sleepMs(ms: 80);
		Assert:areEqualInt(1, timeoutHits);
		Assert:areEqualInt(3, intervalHits);
		Assert:areEqualInt(0, cancelledHits);
	}

	Function is testDateTimeEpochAndComponents(){
		local DateTime is epoch: DateTime:fromEpochMs(epochMs: 0, offsetSec: 0);
		Assert:areEqualInt(1970, epoch:getYear());
		Assert:areEqualInt(1, epoch:getMonth());
		Assert:areEqualInt(1, epoch:getDay());
		Assert:areEqualInt(0, epoch:getHour());
		Assert:areEqualInt(0, epoch:getMinute());
		Assert:areEqualInt(0, epoch:getSecond());
		Assert:areEqualInt(0, epoch:getMillisecond());
		Assert:areEqualInt(4, epoch:getDayOfWeek());
		Assert:areEqualInt(1, epoch:getDayOfYear());
		Assert:areEqualString('1970-01-01', epoch:formatDate());
		Assert:areEqualString('00:00:00', epoch:formatTime());
		Assert:areEqualString('1970-01-01T00:00:00.000Z', epoch:formatIso());
		Assert:areEqualString('1970-01-01T00:00:00.000Z', epoch:toString());
	}

	Function is testDateTimeLeapYearsAndCalendar(){
		Assert:isTrue(DateTime:isLeap(y: 2000));
		Assert:isTrue(DateTime:isLeap(y: 2024));
		Assert:isFalse(DateTime:isLeap(y: 1900));
		Assert:isFalse(DateTime:isLeap(y: 2023));
		Assert:areEqualInt(29, DateTime:daysInMonth(y: 2024, m: 2));
		Assert:areEqualInt(28, DateTime:daysInMonth(y: 2023, m: 2));
		Assert:areEqualInt(30, DateTime:daysInMonth(y: 2024, m: 4));

		local DateTime is leapDay: DateTime:of(year: 2024, month: 2, day: 29, hour: 14, minute: 30, second: 45, millisecond: 123, offsetSec: 0);
		Assert:areEqualString('2024-02-29T14:30:45.123Z', leapDay:formatIso());
		Assert:isTrue(leapDay:isLeapYear());
		Assert:areEqualInt(60, leapDay:getDayOfYear());
		Assert:areEqualInt(4, leapDay:getDayOfWeek());
	}

	Function is testDateTimeArithmeticAndOffsets(){
		local DateTime is dt: DateTime:of(year: 2026, month: 11, day: 14, hour: 20, minute: 0, second: 0, millisecond: 500, offsetSec: -18000);
		Assert:areEqualString('2026-11-14T20:00:00.500-05:00', dt:formatIso());

		local DateTime is utc: dt:toUtc();
		Assert:areEqualString('2026-11-15T01:00:00.500Z', utc:formatIso());
		Assert:areEqualInt(0, dt:diffMs(other: utc));

		local DateTime is nextDay: utc:addDays(days: 1):addHours(hours: 2):addMinutes(minutes: 15):addSeconds(seconds: 10):addMs(ms: 250);
		Assert:areEqualString('2026-11-16T03:15:10.750Z', nextDay:formatIso());
		Assert:areEqualInt(94510250, nextDay:diffMs(other: utc));
	}

	Function is testDateTimeNow(){
		local DateTime is nowUtc: DateTime:utcNow();
		local DateTime is nowLocal: DateTime:now();
		Assert:isTrue(nowUtc:getYear() >= 2024);
		Assert:isTrue(nowLocal:getYear() >= 2024);
		Assert:isTrue(nowUtc:getMonth() >= 1 && nowUtc:getMonth() <= 12);
		Assert:isTrue(nowUtc:getDay() >= 1 && nowUtc:getDay() <= 31);
	}
}
