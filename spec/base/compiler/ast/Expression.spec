#! Package base:compiler:ast
#! One expression node, modeled as a sum type.
##
## Expressions are represented as an enhanced enum (sum type): each variant
## carries only the payload fields relevant to its variant type, while shared
## product members (source line and resolved type) are defined once on the
## base enum.

Enum is Expression {
	namespace: ['base', 'compiler', 'ast'],

	using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', CallData],
		['base', 'sys', as Conditional()]
	],

	StringLit(String is value),
	NumberLit(Int is value, String is text),
	FloatLit(String is text),
	BoolLit(Boolean is value),
	Ident(String is name),
	Path(Array of String is segments),
	ArrayLit(Array of Expression is items),
	MapLit(Array of Expression is keys, Array of Expression is values),
	Cast(Expression is inner, String is target, Array of Expression is args),
	FieldAccess(Expression is target, String is fieldName),
	Index(Expression is target, Expression is index),
	Call(CallData is call),
	Binary(String is op, Expression is left, Expression is right),
	Unary(String is op, Expression is operand),
	AnonFn(Type is returnType, Array of Parameter is params, Array of Statement is body),
	UsingAs(String is className, Array of NamedArg is args),
	Unknown,

	## One-based source line where the expression starts.
	Int is line: 0;

	## Type resolved by the checker (its canonical name).
	String is resolvedType: '';

	## Structured [Type] node resolved by the checker (base name + generic `Array of Type` params).
	Type is resolvedTypeNode;
	Boolean is hasResolvedTypeNode: false;

	## Optional alias for `UsingAs` (`as ClassName(args) is alias`).
	String is usingAsAlias: '';

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function of Expression is setLine(Int is line){
		:line: line;
		return :;
	}

	## Sets the checker-resolved type name.
	##
	## @param t: Resolved type name.
	Function is setResolvedType(String is t){
		:resolvedType: t;
	}

	## Sets the structured checker-resolved [Type] node together with its canonical string name.
	Function is setResolvedTypeNode(Type is tn, String is t){
		:resolvedTypeNode: tn;
		:hasResolvedTypeNode: true;
		:resolvedType: t;
	}

	## Returns the structured checker-resolved [Type] node, or an empty [Type] if unset.
	Function of Type is getResolvedTypeNode(){
		if({ !:hasResolvedTypeNode }, {
			return Type:EMPTY;
		});
		return :resolvedTypeNode;
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
