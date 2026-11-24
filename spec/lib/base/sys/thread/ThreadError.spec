#! Package base:sys:thread
#! The threading error kinds: the variant set for
#! `SpecError of ThreadError` payloads on ThreadScope/Task/Channel
#! surfaces.
##
## Variants mirror the failure modes the thread floor actually
## reports: spawn refusal from the OS and scope/task cancellation.

Enum is ThreadError {
	replace [String] is namespace: ['base', 'sys', 'thread'];
	SPAWN_FAILED,
	CANCELLED
}
