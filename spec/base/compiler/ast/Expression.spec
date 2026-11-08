#! Package base:compiler:ast
#! One expression node.
##
## Spec has no sum types, so a node carries the fields of every kind; the
## fields below are grouped by [ExpressionKind] and only the group for the
## node's kind is meaningful. The kind enum drives exhaustive `when`
## dispatch in every pass.
##
## AST nodes are transparent data records: fields are public because the
## compiler passes read and write them directly.

Class is Expression{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', WhenArm],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter]
	];

	## Node category for enum dispatch.
	ExpressionKind is kind: ExpressionKind:IDENT;

	## One-based source line where the expression starts.
	Int is line: 0;

	## Type resolved by the checker (its canonical name).
	String is resolvedType: '';

	## All literal kinds: the literal's text (numbers keep their scanned,
	## normalized text; strings carry processed content).
	String is stringValue: '';

	## NUMBER: the integer value.
	Int is intValue: 0;

	## FLOAT: the floating-point value.
	Float is floatValue: 0.0;

	## BOOL: the boolean value.
	Boolean is boolValue: false;

	## PATH: the colon-delimited segments.
	Array of String is pathSegments: [];

	## ARRAY: the element expressions.
	Array of Expression is arrayItems: [];

	## MAP: the key and value expressions (parallel arrays).
	Array of Expression is mapKeys: [];
	Array of Expression is mapValues: [];

	## CAST: the cast operand, target type name, and optional width args
	## (e.g. the digit width of Hex(8)).
	Expression is leftExpr;
	String is castTarget: '';
	Array of Expression is castArgs: [];

	## CALL: the receiver, method name, and arguments.
	Expression is methodTarget;
	String is methodName: '';
	Array of NamedArg is methodArgs: [];

	## CALL: for a bare (self-receiver) call resolved against the bare
	## scope, the as-imported class providing the member (INSTANCE.md
	## §2.3); '' when the call is an ordinary own-member dispatch.
	String is bareProvider: '';

	## CALL: the scoped-region desugarer appended the remainder as the
	## last argument (FUNCTIONS.md §as). The remainder never participates
	## in overload selection — it binds to the selected overload's
	## declared-but-unbound last Function parameter.
	Boolean is scopedRemainder: false;

	## CALL: the checker-selected overload's position within the owning
	## class's same-name member group (FUNCTIONS.md §I.2); -1 when
	## unstamped (single-member names resolve as index 0).
	Int is overloadIndex: -1;

	## BINARY: the operator and the right operand (the left operand shares
	## leftExpr with CAST).
	String is binaryOp: '';
	Expression is rightExpr;

	## UNARY: the operator and inner operand.
	String is unaryOp: '';
	Expression is unaryExpr;

	## IF_ELSE: condition and branches.

	## WHEN: the subject and arms.
	Expression is whenSubject;
	Array of WhenArm is whenArms: [];

	## ANON_FN: return type, parameters, and body.
	Type is anonReturnType;
	Array of Parameter is anonParams: [];
	Array of Statement is anonBody: [];

	## Initializes an expression node with its kind.
	##
	## @param kind: Node category.
	replace Function is init(ExpressionKind is kind){
		self:kind: kind;
	}

	## Configures this node as an identifier reference.
	##
	## @param name: Identifier name.
	Function is makeIdent(String is name){
		self:kind: ExpressionKind:IDENT;
		self:stringValue: name;
	}

	## Configures this node as a colon-delimited path.
	##
	## @param segments: Path segment identifiers.
	Function is makePath(Array of String is segments){
		self:kind: ExpressionKind:PATH;
		self:pathSegments: segments;
	}

	## Configures this node as a map literal.
	##
	## @param keys: Key expressions.
	## @param values: Value expressions (parallel to [keys]).
	Function is makeMap(Array of Expression is keys, Array of Expression is values){
		self:kind: ExpressionKind:MAP;
		self:mapKeys: keys;
		self:mapValues: values;
	}

	## Configures this node as a type cast (value as Target).
	##
	## @param inner: The cast operand.
	## @param target: Target type name.
	## @param args: Optional arguments (e.g. digit width for Hex(8)).
	Function is makeCast(Expression is inner, String is target, Array of Expression is args){
		self:kind: ExpressionKind:CAST;
		self:leftExpr: inner;
		self:castTarget: target;
		self:castArgs: args;
	}

	## Configures this node as a `when` matching expression.
	##
	## @param subject: Subject being matched.
	## @param arms: The branches.
	Function is makeWhen(Expression is subject, Array of WhenArm is arms){
		self:kind: ExpressionKind:WHEN;
		self:whenSubject: subject;
		self:whenArms: arms;
	}

	## Sets the checker-resolved type name.
	##
	## @param t: Resolved type name.
	Function is setResolvedType(String is t){
		self:resolvedType: t;
	}

	## Returns the value expression of the call argument at [index].
	## Typed accessor: avoids the Array.get->Any limitation.
	##
	## @param index: The argument index.
	## @return: The argument's value expression.
	Function of Expression is argValue(Int is index){
		local NamedArg is arg: self:methodArgs:get(index: index);
		return arg:value;
	}

	## Returns the name of the call argument at [index].
	##
	## @param index: The argument index.
	## @return: The argument's name (empty for positional).
	Function of String is argName(Int is index){
		local NamedArg is arg: self:methodArgs:get(index: index);
		return arg:name;
	}

	## Returns the number of call arguments.
	##
	## @return: The argument count.
	Function of Int is argCount(){
		return self:methodArgs:length();
	}
}
