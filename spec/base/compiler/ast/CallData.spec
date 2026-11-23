#! Package base:compiler:ast
#! Mutable call-expression payload shared between parser, checker, and codegen.

Class is CallData{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', NamedArg]
	];

	## Receiver expression.
	Expression is target;

	## Method or function name.
	String is name: '';

	## Call arguments.
	[NamedArg] is args;

	## For a bare (self-receiver) call resolved against the bare scope,
	## the as-imported class providing the member; '' for ordinary dispatch.
	String is bareProvider: '';

	## True when the call was written bare (`foo(...)`) rather than with an
	## explicit receiver (`:foo(...)` or `obj:foo(...)`).
	Boolean is isBareCall: false;

	## True when the scoped-region desugarer appended the remainder as the
	## last argument.
	Boolean is scopedRemainder: false;

	## Checker-selected overload index within the owning class's same-name
	## member group; 0 when unstamped.
	Int is overloadIndex: 0;

	## Initializes a call payload.
	##
	## @param target: Receiver expression.
	## @param name: Method name.
	## @param args: Call arguments.
	replace Function is init(Expression is target, String is name, [NamedArg] is args){
		:target: target;
		:name: name;
		:args: args;
	}
}
