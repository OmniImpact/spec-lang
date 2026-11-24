#! Generic tagged enums (post-name type params, the class grammar):
#! `Enum is Maybe of T { ... }` and `Enum is Result of T to E { ... }`.
#! Covers single- and two-parameter declarations, scalar and ref
#! payloads, bare-path payload-less construction, match binding of the
#! grounded payload types, and the variant identity contract (name/
#! ordinal) on instantiations.

Enum is Maybe of T {
	Some(T is value),
	None
}

Enum is Result of T to E {
	Ok(T is value),
	Err(E is error)
}

Class of SpecUnitTest is TestGenericEnum{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
	];

	Function is testSingleParamIntPayload(){
		local Maybe of Int is m: Maybe:Some(value: 42);
		local Int is v: match(on: m, when: [
			Maybe:Some: local Function of Int(Int is val){ return val; },
			Maybe:None: { 0 }
		]);
		Assert:areEqualInt(42, v);
		local Maybe of Int is n: Maybe:None;
		local Int is w: match(on: n, when: [
			Maybe:Some: local Function of Int(Int is val){ return val; },
			Maybe:None: { 0 }
		]);
		Assert:areEqualInt(0, w);
	}

	Function is testSingleParamFloatPayload(){
		# f64 payload proves the concrete layout (a T-fallback ptr field
		# would round-trip only by width coincidence).
		local Maybe of Float is m: Maybe:Some(value: 3.5);
		local Float is v: match(on: m, when: [
			Maybe:Some: local Function of Float(Float is val){ return val; },
			Maybe:None: { 0.0 }
		]);
		Assert:isTrue(v == 3.5);
	}

	Function is testRefPayloadAndIdentity(){
		local Maybe of String is m: Maybe:Some(value: 'carried');
		local String is v: match(on: m, when: [
			Maybe:Some: local Function of String(String is val){ return val; },
			Maybe:None: { '' }
		]);
		Assert:areEqualString('carried', v);
		Assert:areEqualString('Some', m:name());
		Assert:areEqualInt(0, m:ordinal());
		local Maybe of String is n: Maybe:None;
		Assert:areEqualString('None', n:name());
		Assert:areEqualInt(1, n:ordinal());
	}

	Function is testTwoParamResultShape(){
		local Result of String to Int is ok: Result:Ok(value: 'fine');
		local String is a: match(on: ok, when: [
			Result:Ok:  local Function of String(String is v){ return v; },
			Result:Err: local Function of String(Int is c){ return 'err' . (c as String); }
		]);
		Assert:areEqualString('fine', a);
		local Result of String to Int is bad: Result:Err(error: 7);
		local String is b: match(on: bad, when: [
			Result:Ok:  local Function of String(String is v){ return v; },
			Result:Err: local Function of String(Int is c){ return 'err:' . (c as String); }
		]);
		Assert:areEqualString('err:7', b);
		Assert:areEqualString('Ok', ok:name());
		Assert:areEqualString('Err', bad:name());
	}

	Function is testTwoInstantiationsCoexist(){
		# Two instantiations of one generic enum in one function keep
		# distinct layouts and dispatch tables.
		local Maybe of Int is mi: Maybe:Some(value: 5);
		local Maybe of String is ms: Maybe:Some(value: 'five');
		local Int is a: match(on: mi, when: [
			Maybe:Some: local Function of Int(Int is v){ return v; },
			Maybe:None: { 0 }
		]);
		local String is b: match(on: ms, when: [
			Maybe:Some: local Function of String(String is v){ return v; },
			Maybe:None: { '' }
		]);
		Assert:areEqualInt(5, a);
		Assert:areEqualString('five', b);
	}
}
