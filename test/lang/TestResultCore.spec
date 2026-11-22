#! base:core:Result — the result-return transport (SPECDEV §8).
#! Generic payload-variant enum `Result of T to E` whose Err variant
#! carries the full error currency (SpecError of E: kind, description,
#! stack trace). Covers construction grounding, when-destructuring,
#! value-yield composition, ref payloads across branches, and the
#! variant identity contract.

Enum is ProbeFailure {
	NOT_FOUND,
	DENIED
}

Class of SpecUnitTest is TestResultCore{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', SpecError],
		['base', 'core', Result],
		['base', 'sys', as Conditional()]
	];

	Function is testOkConstructionAndUnwrap(){
		local Result of Int to ProbeFailure is r: Result:Ok(value: 41 + 1);
		local Int is v: match(on: r, when: [
			Result:Ok:  local Function of Int(Int is val){ return val; },
			Result:Err: local Function of Int(SpecError of ProbeFailure is e){ return 0; }
		]);
		Assert:areEqualInt(42, v);
		Assert:areEqualString('Ok', r:name());
		Assert:areEqualInt(0, r:ordinal());
	}

	Function is testErrCarriesFullCurrency(){
		local SpecError of ProbeFailure is err: SpecError:init(
			kind: ProbeFailure:DENIED,
			description: 'read access denied'
		);
		local Result of Int to ProbeFailure is r: Result:Err(error: err);
		local String is kindSeen: '';
		local String is descSeen: '';
		local Int is framesSeen: 0;
		local Int is v: match(on: r, when: [
			Result:Ok:  local Function of Int(Int is val){ return 0; },
			Result:Err: local Function of Int(SpecError of ProbeFailure is e){
				kindSeen: e:kindName;
				descSeen: e:description;
				framesSeen: e:stackTrace:length();
				return 1;
			}
		]);
		Assert:areEqualInt(1, v);
		Assert:areEqualString('DENIED', kindSeen);
		Assert:areEqualString('read access denied', descSeen);
		Assert:isTrue(framesSeen >= 1);
		Assert:areEqualString('Err', r:name());
		Assert:areEqualInt(1, r:ordinal());
	}

	Function is testValueYieldComposes(){
		# The match expression feeds a binary operand and a return position.
		local Result of Int to ProbeFailure is r: Result:Ok(value: 20);
		local Int is doubled: match(on: r, when: [
			Result:Ok:  local Function of Int(Int is val){ return val; },
			Result:Err: local Function of Int(SpecError of ProbeFailure is e){ return 1; }
		]) * 2;
		Assert:areEqualInt(40, doubled);
	}

	Function is testRefPayloadAcrossBranches(){
		# String payload flows through Ok, then a different instantiation
		# errors: both instantiations coexist and dispatch independently.
		local Result of String to ProbeFailure is ok: Result:Ok(value: 'carried');
		local Result of Int to ProbeFailure is bad: Result:Err(error: SpecError:init(kind: ProbeFailure:NOT_FOUND, description: 'missing'));
		local String is s: match(on: ok, when: [
			Result:Ok:  local Function of String(String is val){ return val; },
			Result:Err: local Function of String(SpecError of ProbeFailure is e){ return e:kindName; }
		]);
		local Int is n: match(on: bad, when: [
			Result:Ok:  local Function of Int(Int is val){ return val; },
			Result:Err: local Function of Int(SpecError of ProbeFailure is e){ return e:description:length(); }
		]);
		Assert:areEqualString('carried', s);
		Assert:areEqualInt(7, n);
	}

	Function is testExhaustivenessApplies(){
		# The Result enum is a plain payload-variant enum: the checker's
		# exhaustiveness and redundant-else rules apply to it like any enum.
		local Result of Int to ProbeFailure is r: Result:Ok(value: 1);
		local Int is v: match(on: r, when: [
			Result:Ok:  local Function of Int(Int is val){ return val; },
			Result:Err: local Function of Int(SpecError of ProbeFailure is e){ return 0; }
		]);
		Assert:areEqualInt(1, v);
	}
}
