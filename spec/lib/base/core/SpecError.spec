#! Package base:core
#! Structured error value carrying a typed enum kind, human-readable description,
#! stringified enum kind name, and Spec stack trace.

Class is SpecError of T{
	namespace: ['base', 'core'];

	replace Array of Array of String is using: [
		['base', 'sys', StackFrame],
		['base', 'sys', SourceLocation],
		['base', 'struct', Array],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is description: '';
	String is kindName: '';
	T is kind;
	Any is kindBox: '';
	Array of StackFrame is stackTrace: [];

	local Function of String is resolveKindName(Any is k){
		local Int is addr: Mem:objToAddr(obj: k);
		if({ addr < 4096 }, {
			return 'Unknown';
		});
		local Int is idx: Introspection:heldIndexOf(obj: k);
		if({ idx >= 0 }, {
			return Introspection:heldName(obj: k, index: idx);
		});
		local String is ti: Introspection:typeIdentity(obj: k);
		if({ ti == 'String' || ti == 'Str' }, {
			return k as String;
		});
		local Int is us: ti:indexOf(search: '_', default: -1);
		if({ us >= 0 && us + 1 < ti:length() }, {
			return ti:substring(start: us + 1, end: ti:length());
		});
		return ti;
	}

	replace Function is init(T is kind, String is description: '', String is kindName: ''){
		:kind: kind;
		local Int is kAddr: Mem:objToAddr(obj: kind);
		if({ kAddr >= 4096 }, {
			:kindBox: Mem:addrToObj(addr: kAddr);
		});
		:description: description;
		if({ kindName != '' }, {
			:kindName: kindName;
		}, {
			:kindName: :resolveKindName(k: :kindBox);
		});
		:stackTrace: [];
	}

	Function of String is getDescription(){
		return :description;
	}

	Function of String is getKindName(){
		return :kindName;
	}

	Function of T is getKind(){
		return :kind;
	}

	Function of Any is getKindBox(){
		return :kindBox;
	}

	Function of Array of StackFrame is getStackTrace(){
		return :stackTrace;
	}

	Function is addFrame(StackFrame is frame){
		:stackTrace:add(item: frame);
	}

	Function is addFrameAt(String is className, String is methodName, String is file: '', Int is line: 0, Int is col: 1){
		:stackTrace:add(item: StackFrame:init(location: SourceLocation:init(file: file, line: line, col: col), className: className, methodName: methodName));
	}

	## Appends a [StackFrame] to the currently pending TLS [SpecError] (if any).
	Function is recordPendingFrame(String is className, String is methodName, String is file, Int is line){
		local Int is errAddr: Mem:tlsGetI64(slot: 15);
		if({ errAddr == 0 }, { return; });
		Mem:tlsSetI64(slot: 15, val: 0);
		Mem:retainAddr(objAddr: errAddr);
		local SpecError is err: Mem:addrToObj(addr: errAddr) as SpecError;
		err:addFrameAt(className: className, methodName: methodName, file: file, line: line, col: 1);
		Mem:tlsSetI64(slot: 15, val: errAddr);
	}

	## Invokes the root fallback handler on the currently pending TLS [SpecError] (if any).
	Function is panicPending(){
		local Int is errAddr: Mem:tlsGetI64(slot: 15);
		if({ errAddr == 0 }, { return; });
		Mem:tlsSetI64(slot: 15, val: 0);
		Mem:retainAddr(objAddr: errAddr);
		local SpecError is err: Mem:addrToObj(addr: errAddr) as SpecError;
		Mem:panic(msg: err:toString());
	}

	replace Function of String is toString(){
		local String is head: '[' . :kindName . ']';
		if({ :description != '' }, {
			head: head . ' ' . :description;
		});
		local String is out: head;
		local Int is i: 0;
		while({ i < :stackTrace:length() }, {
			local StackFrame is f: :stackTrace:get(index: i);
			out: out . "\n  at " . f:toString();
			i: i + 1;
		});
		return out;
	}
}
