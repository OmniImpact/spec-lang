#! Package base:sysinternal
#! The time floor: high-resolution monotonic and wall-clock primitives,
#! sub-millisecond sleep, timezone offset lookup, and async timer tasks
#! bound to C by the naming convention.

Class is Time{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Returns monotonic clock reading in nanoseconds. Bound to `spec_time_monotonic_ns`.
	Function of Int is time_monotonic_ns();

	## Returns monotonic clock reading in microseconds. Bound to `spec_time_monotonic_us`.
	Function of Int is time_monotonic_us();

	## Returns monotonic clock reading in milliseconds. Bound to `spec_time_monotonic_ms`.
	Function of Int is time_monotonic_ms();

	## Returns Unix epoch wall-clock time in milliseconds. Bound to `spec_time_epoch_ms`.
	Function of Int is time_epoch_ms();

	## Returns Unix epoch wall-clock time in nanoseconds. Bound to `spec_time_epoch_ns`.
	Function of Int is time_epoch_ns();

	## Sleeps for [ms] milliseconds. Bound to `spec_time_sleep_ms`.
	Function is time_sleep_ms(Int is ms);

	## Sleeps for [us] microseconds. Bound to `spec_time_sleep_us`.
	Function is time_sleep_us(Int is us);

	## Sleeps for [ns] nanoseconds. Bound to `spec_time_sleep_ns`.
	Function is time_sleep_ns(Int is ns);

	## Returns local UTC offset in seconds at [epoch_sec]. Bound to `spec_time_local_offset_sec`.
	Function of Int is time_local_offset_sec(Int is epoch_sec);
}
