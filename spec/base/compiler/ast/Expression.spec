#! Package base:compiler:ast
#! One expression node, modeled as a sum type.
##
## Expressions are represented as an enhanced enum (sum type): each variant
## carries only the payload fields relevant to its variant type, while shared
## product members (source line and resolved type) are defined once on the
## base enum.

Enum is Expression {
	replace [String] is namespace: ['base', 'compiler', 'ast'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', SemType],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', CallData],
		['base', 'sys', as Conditional()]
	];

	StringLit(String is value),
	NumberLit(Int is value, String is text),
	FloatLit(String is text),
	BoolLit(Boolean is value),
	Ident(String is name),
	Path([String] is segments),
	ArrayLit([Expression] is items),
	MapLit([Expression] is keys, [Expression] is values),
	Cast(Expression is inner, String is target, [Expression] is args),
	FieldAccess(Expression is target, String is fieldName),
	Index(Expression is target, Expression is index),
	Call(CallData is call),
	Binary(String is op, Expression is left, Expression is right),
	Unary(String is op, Expression is operand),
	AnonFn(Type is returnType, [Parameter] is params, [Statement] is body),
	UsingAs(String is className, [NamedArg] is args),
	Unknown,

	## One-based source line where the expression starts.
	Int is line: 0;

	## Semantic [SemType] sum-type node resolved by the checker.
	SemType is semType: SemType:Empty;

	## Optional alias for `UsingAs` (`as ClassName(args) is alias`).
	String is usingAsAlias: '';

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function of Expression is setLine(Int is line){
		:line: line;
		return :;
	}

	## Sets the semantic [SemType] sum-type resolved by the checker.
	Function is setSemType(SemType is st){
		:semType: st;
	}

	## Returns the semantic [SemType] resolved by the checker ([SemType:Empty] if unset).
	Function of SemType is getSemType(){
		return :semType;
	}

	## Returns the value expression of the call argument at [index].
	##
	## @param index: The argument index.
	## @return: The argument's value expression.
	Function of Expression is argValue(Int is index){
		return match(on: :, when: [
			Expression:Call: local Function of Expression(CallData is call){
				local NamedArg is arg: call:args:get(index: index);
				return arg:value;
			},
			else: { Expression:Unknown }
		]);
	}

	## Returns the name of the call argument at [index].
	##
	## @param index: The argument index.
	## @return: The argument's name (empty for positional).
	Function of String is argName(Int is index){
		return match(on: :, when: [
			Expression:Call: local Function of String(CallData is call){
				local NamedArg is arg: call:args:get(index: index);
				return arg:name;
			},
			else: { '' }
		]);
	}

	## Returns the number of call arguments.
	##
	## @return: The argument count.
	Function of Int is argCount(){
		return match(on: :, when: [
			Expression:Call: local Function of Int(CallData is call){
				return call:args:length();
			},
			else: { 0 }
		]);
	}
}
