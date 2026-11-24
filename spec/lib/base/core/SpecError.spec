#! Package base:core
#! Structured error value carrying a typed enum kind, human-readable description,
#! stringified enum kind name, and Spec stack trace.

Class is SpecError of T{
	replace [String] is namespace: ['base', 'core'];

	replace [[String]] is using: [
		['base', 'sys', StackFrame],
		['base', 'sys', SourceLocation],
		['base', 'sys', as Reflection()],
		['base', 'struct', Array],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Any is frameRecorder: '';
	Any is panicRunner: '';
	String is description: '';
	String is kindName: '';
	Array of StackFrame is stackTrace: Array();
	Array of SpecError is secondaryErrors: Array();
	T is kind;

	local Function of String is resolveKindName(T is k){
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

	replace Function is init(T is kind, String is description: '', String is kindName: '', String is callerClass: Reflection:class(), String is callerMethod: Reflection:method(), String is callerFile: Reflection:file(), Int is callerLine: Reflection:line()){
		:frameRecorder: local Function(Any is errObj, String is cName, String is mName, String is fName, Int is ln){
			local SpecError is se: errObj as SpecError;
			se:addFrameAt(className: cName, methodName: mName, file: fName, line: ln, col: 1);
		};
		Mem:retainAddr(objAddr: Mem:objToAddr(obj: :frameRecorder));
		:panicRunner: local Function(Any is errObj){
			local SpecError is se: errObj as SpecError;
			Mem:panic(msg: se:toString());
		};
		Mem:retainAddr(objAddr: Mem:objToAddr(obj: :panicRunner));
		:kind: kind;
		:description: description;
		if({ kindName != '' }, {
			:kindName: kindName;
		}, {
			:kindName: :resolveKindName(k: kind);
		});
		:stackTrace: Array();
		:secondaryErrors: Array();
		:addFrameAt(className: callerClass, methodName: callerMethod, file: callerFile, line: callerLine, col: 1);
	}

	Function is addSecondary(SpecError is error){
		local Int is eAddr: Mem:objToAddr(obj: error);
		if({ eAddr != 0 && eAddr != Mem:objToAddr(obj: :) }, {
			:secondaryErrors:add(item: error);
		});
	}

	Function of Array of SpecError is getSecondaryErrors(){
		return :secondaryErrors;
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

	Function of Array of StackFrame is getStackTrace(){
		return :stackTrace;
	}

	Function is addFrame(StackFrame is frame){
		:stackTrace:add(item: frame);
	}

	Function is addFrameAt(String is className, String is methodName, String is file: '', Int is line: 0, Int is col: 1){
		:stackTrace:add(item: StackFrame:init(location: SourceLocation:init(file: file, line: line, col: col), className: className, methodName: methodName));
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
		local Int is si: 0;
		while({ si < :secondaryErrors:length() }, {
			local SpecError is sec: :secondaryErrors:get(index: si);
			out: out . "\n  Secondary: " . sec:toString();
			si: si + 1;
		});
		return out;
	}
}
