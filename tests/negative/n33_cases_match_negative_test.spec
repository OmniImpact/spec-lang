#! specunit: negative
#! expect: is not a held member of 'N33Sink'
#! expect: Duplicate match key 'file'
#! expect: Non-exhaustive match: missing arm(s) N33Mode:off
#! expect: A value-yielding match requires an else arm
#! expect: The match arms mix value-yielding and void closures
#! expect: Match arms after else are unreachable
#! expect: 'Int' cannot be matched

#! N33 (PLAN-ENUM Stage 3): the Cases:match walls.
#! - keys resolve against the subject's class only
#! - duplicate keys are rejected
#! - Enum-rooted subjects require full coverage or else
#! - value-yielding matches over other classes require else
#! - arms must not mix value-yielding and void closures
#! - arms after else are unreachable

Class of Enum is N33Mode{
	namespace: ['test'];

	held N33Mode is on: N33Mode:init();
	held N33Mode is off: N33Mode:init();
}

Class is N33Sink{
	namespace: ['test'];

	held String is file: 'file.log';
	held Int is level: 2;
}

Class is N33CasesWalls{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		# 1. a key from another class is not a held member of the subject.
		local N33Sink is s: N33Sink:file;
		local String is wrong: Conditional:match(on: s, when: [
			N33Mode:on: { 'x' },
			else: { 'y' }
		]);

		# 2. duplicate keys.
		local String is dup: Conditional:match(on: s, when: [
			N33Sink:file: { 'a' },
			file: { 'b' },
			else: { 'c' }
		]);

		# 3. Enum-rooted subjects must be exhaustive without else.
		local String is partial: Conditional:match(on: N33Mode:on, when: [
			N33Mode:on: { 'on' }
		]);

		# 4. value-yielding match over a non-Enum class requires else.
		local String is needsElse: Conditional:match(on: s, when: [
			N33Sink:file: { 'f' }
		]);

		# 5. mixed arm bodies.
		local String is mixed: Conditional:match(on: s, when: [
			N33Sink:file: { 'f' },
			N33Sink:level: { },
			else: { 'e' }
		]);

		# 6. arms after else are unreachable.
		local String is late: Conditional:match(on: s, when: [
			else: { 'e' },
			N33Sink:file: { 'f' }
		]);

		# 7. match is identity dispatch over class instances: a
		#    primitive-typed subject carries no owner association.
		local String is prim: Conditional:match(on: 5, when: [
			else: { 'e' }
		]);
	}

	replace Array of Array of String is using: [

	];
}
