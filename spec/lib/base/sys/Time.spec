#! Package base:sys
#! High-resolution monotonic and wall-clock timing, precision sleep,
#! synchronous deadline-scheduled timers, and asynchronous callback timers.

Class is Time{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Time],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'struct', Array],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	held Array of Int is activeTimers: [];

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

	## Schedules [callback] to run asynchronously inside [scope] after [ms]
	## milliseconds. Returns a timer ID that can be passed to [cancelTimer].
	Function of Int is setTimeout(ThreadScope is scope, Int is ms, Function is callback){
		return setInterval(scope: scope, ms: ms, count: 1, callback: callback);
	}

	## Schedules [callback] to run asynchronously inside [scope] every [ms] milliseconds
	## for [count] invocations (or indefinitely until cancelled if [count] <= 0). Returns a timer ID.
	Function of Int is setInterval(ThreadScope is scope, Int is ms, Int is count, Function is callback){
		local Int is tid: 0;
		Parallel:syncWith(lock: 78, action: {
			Time:activeTimers:add(item: 0);
			tid: Time:activeTimers:length();
		});
		scope:spawn(task: local Function(){
			local Int is intervalNs: if({ ms > 0 }, { ms * 1000000 }, { 0 });
			local Int is targetNs: base:sysinternal:Time:time_monotonic_ns() + intervalNs;
			local Int is executed: 0;
			local Boolean is keepGoing: true;
			while({ keepGoing && (count <= 0 || executed < count) }, {
				local Boolean is waiting: true;
				while({ waiting }, {
					local Boolean is isCancelled: scope:isCancelled();
					if({ !isCancelled }, {
						Parallel:syncWith(lock: 78, action: {
							if({ Time:activeTimers:get(index: tid - 1, default: 1) != 0 }, {
								isCancelled: true;
							});
						});
					});
					if({ isCancelled }, {
						waiting: false;
						keepGoing: false;
					}, {
						local Int is remNs: targetNs - base:sysinternal:Time:time_monotonic_ns();
						if({ remNs <= 0 }, {
							waiting: false;
						}, {
							local Int is chunkNs: if({ remNs > 5000000 }, { 5000000 }, { remNs });
							base:sysinternal:Time:time_sleep_ns(ns: chunkNs);
						});
					});
				});
				if({ keepGoing }, {
					local Boolean is isCancelledNow: scope:isCancelled();
					if({ !isCancelledNow }, {
						Parallel:syncWith(lock: 78, action: {
							if({ Time:activeTimers:get(index: tid - 1, default: 1) != 0 }, {
								isCancelledNow: true;
							});
						});
					});
					if({ !isCancelledNow }, {
						callback();
						executed: executed + 1;
						targetNs: targetNs + intervalNs;
					}, {
						keepGoing: false;
					});
				});
			});
			Parallel:syncWith(lock: 78, action: {
				Time:activeTimers:set(index: tid - 1, item: 2);
			});
		});
		return tid;
	}

	## Cancels an active asynchronous timer created by [setTimeout] or [setInterval].
	## Returns `true` if the timer was found and marked cancelled.
	Function of Boolean is cancelTimer(Int is timerId){
		local Boolean is found: false;
		Parallel:syncWith(lock: 78, action: {
			if({ timerId >= 1 && timerId <= Time:activeTimers:length() && Time:activeTimers:get(index: timerId - 1, default: 1) == 0 }, {
				Time:activeTimers:set(index: timerId - 1, item: 1);
				found: true;
			});
		});
		return found;
	}
}
