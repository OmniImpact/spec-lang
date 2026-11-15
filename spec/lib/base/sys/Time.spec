#! Package base:sys
#! High-resolution monotonic and wall-clock timing, precision sleep,
#! synchronous deadline-scheduled timers, and asynchronous callback timers.

Class is Time{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Time],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Returns a monotonic high-resolution timestamp in nanoseconds.
	Function of Int is monotonicNs(){
		return base:sysinternal:Time:time_monotonic_ns();
	}

	## Returns a monotonic high-resolution timestamp in microseconds.
	Function of Int is monotonicUs(){
		return base:sysinternal:Time:time_monotonic_us();
	}

	## Returns a monotonic timestamp in milliseconds.
	Function of Int is monotonicMs(){
		return base:sysinternal:Time:time_monotonic_ms();
	}

	## Returns the current Unix epoch wall-clock timestamp in milliseconds.
	Function of Int is nowMs(){
		return base:sysinternal:Time:time_epoch_ms();
	}

	## Returns the current Unix epoch wall-clock timestamp in nanoseconds.
	Function of Int is nowNs(){
		return base:sysinternal:Time:time_epoch_ns();
	}

	## Returns the current Unix epoch wall-clock timestamp in whole seconds.
	Function of Int is nowSec(){
		return base:sysinternal:Time:time_epoch_ms() / 1000;
	}

	## Suspends the current thread for [ms] milliseconds.
	Function is sleepMs(Int is ms){
		base:sysinternal:Time:time_sleep_ms(ms: ms);
	}

	## Suspends the current thread for [us] microseconds.
	Function is sleepUs(Int is us){
		base:sysinternal:Time:time_sleep_us(us: us);
	}

	## Suspends the current thread for [ns] nanoseconds.
	Function is sleepNs(Int is ns){
		base:sysinternal:Time:time_sleep_ns(ns: ns);
	}

	## Suspends the current thread until the monotonic clock reaches [targetNs].
	Function is sleepUntilNs(Int is targetNs){
		local Int is remaining: targetNs - base:sysinternal:Time:time_monotonic_ns();
		if({ remaining > 0 }, {
			base:sysinternal:Time:time_sleep_ns(ns: remaining);
		});
	}

	## Returns the local timezone offset from UTC in seconds at [epochSec].
	Function of Int is localOffsetSec(Int is epochSec){
		return base:sysinternal:Time:time_local_offset_sec(epoch_sec: epochSec);
	}

	## Executes [action] and returns the elapsed monotonic time in nanoseconds.
	Function of Int is measureNs(Function is action){
		local Int is start: base:sysinternal:Time:time_monotonic_ns();
		action();
		return base:sysinternal:Time:time_monotonic_ns() - start;
	}

	## Executes [action] and returns the elapsed monotonic time in microseconds.
	Function of Int is measureUs(Function is action){
		return measureNs(action: action) / 1000;
	}

	## Executes [action] and returns the elapsed monotonic time in milliseconds.
	Function of Int is measureMs(Function is action){
		return measureNs(action: action) / 1000000;
	}

	## Sleeps for [ms] milliseconds and then invokes [callback].
	Function is after(Int is ms, Function is callback){
		base:sysinternal:Time:time_sleep_ms(ms: ms);
		callback();
	}

	## Sleeps for [us] microseconds and then invokes [callback].
	Function is afterUs(Int is us, Function is callback){
		base:sysinternal:Time:time_sleep_us(us: us);
		callback();
	}

	## Invokes [callback] [count] times spaced by [intervalMs] milliseconds using
	## drift-compensated monotonic deadline scheduling.
	Function is interval(Int is intervalMs, Int is count, Function is callback){
		intervalUs(intervalUs: intervalMs * 1000, count: count, callback: callback);
	}

	## Invokes [callback] [count] times spaced by [intervalUs] microseconds using
	## drift-compensated monotonic deadline scheduling.
	Function is intervalUs(Int is intervalUs, Int is count, Function is callback){
		if({ count <= 0 }, {
			return;
		});
		local Int is stepNs: intervalUs * 1000;
		local Int is nextDeadline: base:sysinternal:Time:time_monotonic_ns() + stepNs;
		local Int is i: 0;
		while({ i < count }, {
			local Int is rem: nextDeadline - base:sysinternal:Time:time_monotonic_ns();
			if({ rem > 0 }, {
				base:sysinternal:Time:time_sleep_ns(ns: rem);
			});
			callback();
			nextDeadline: nextDeadline + stepNs;
			i: i + 1;
		});
	}

	## Repeatedly invokes [callback] every [intervalMs] milliseconds using
	## drift-compensated deadlines until [callback] returns `false`.
	Function is every(Int is intervalMs, Function of Boolean is callback){
		local Int is stepNs: intervalMs * 1000000;
		local Int is nextDeadline: base:sysinternal:Time:time_monotonic_ns() + stepNs;
		local Boolean is keepGoing: true;
		while({ keepGoing }, {
			local Int is rem: nextDeadline - base:sysinternal:Time:time_monotonic_ns();
			if({ rem > 0 }, {
				base:sysinternal:Time:time_sleep_ns(ns: rem);
			});
			keepGoing: callback();
			nextDeadline: nextDeadline + stepNs;
		});
	}

	## Schedules [callback] to run asynchronously on a background thread after [ms]
	## milliseconds. Returns a timer ID that can be passed to [cancelTimer].
	Function of Int is setTimeout(Int is ms, Function is callback){
		return base:sysinternal:Time:time_set_timeout(ms: ms, callback: callback);
	}

	## Schedules [callback] to run asynchronously every [ms] milliseconds for [count]
	## invocations (or indefinitely if [count] <= 0). Returns a timer ID.
	Function of Int is setInterval(Int is ms, Int is count, Function is callback){
		return base:sysinternal:Time:time_set_interval(ms: ms, count: count, callback: callback);
	}

	## Cancels an active asynchronous timer created by [setTimeout] or [setInterval].
	## Returns `true` if the timer was found and marked cancelled.
	Function of Boolean is cancelTimer(Int is timerId){
		return base:sysinternal:Time:time_cancel_timer(timer_id: timerId);
	}
}
