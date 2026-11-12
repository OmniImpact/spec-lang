#! Package specunit
#! One assertion's record: the branch-free assertion pattern. Held
#! bodies cannot branch (no instance, no import surface), so Assert
#! appends records UNCONDITIONALLY — the ok flag carries the outcome —
#! and the runner interprets them in endTest, where branching is
#! available. Assertions are data; the runner is the interpreter.

Class is CheckRecord{
	namespace: ['specunit'];

	## Whether the assertion held.
	Boolean is ok: true;

	## The failure message (meaningful only when ok is false).
	String is msg: '';

	## Creates a record for one assertion.
	##
	## @param ok: Whether the assertion held.
	## @param msg: The failure message.
	replace Function is init(Boolean is ok, String is msg){
		self:ok: ok;
		self:msg: msg;
	}
}
