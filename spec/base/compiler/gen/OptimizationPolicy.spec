#! Package base:compiler:gen
#! Structural, AST-based optimization predicates for the C11 code generator.
##
## Every optimization here must be purely structural (derived from AST shape
## and resolved types, never from hardcoded class or method names) and
## read-only so parallel code generation remains deterministic and race-free.

Class is OptimizationPolicy{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## True when [typeName] is a stack-only scalar primitive (or Void) that
	## never allocates into or claims from the thread-local ARC claim pool.
	## Empty/unresolved type names return false (conservative).
	Function of Boolean is isPrimitiveScalarType(String is typeName){
		return typeName == 'Int' || typeName == 'Float' || typeName == 'Boolean' || typeName == 'Byte' || typeName == 'Void';
	}

	## True when any parameter in [params] has a non-primitive type.
	Function of Boolean is paramsNeedPoolFrame(Array of Parameter is params){
		local Boolean is needed: false;
		params:each(action: local Function(Parameter is p){
			if({ !needed && !self:isPrimitiveScalarType(typeName: p:paramType:name) }, {
				needed: true;
			});
		});
		return needed;
	}

	## True when [m] (method) requires a SPEC_POOL_AUTO claim-pool frame.
	## Pure-primitive methods with no managed locals, calls, or allocations
	## do not touch the claim pool and can safely omit SPEC_POOL_AUTO.
	Function of Boolean is methodNeedsPoolFrame(Member is m){
		if({ self:paramsNeedPoolFrame(params: m:params) }, {
			return true;
		});
		return self:stmtsNeedPoolFrame(stmts: m:body);
	}

	## True when any statement in [stmts] may allocate or claim into the
	## current scope's ARC claim pool.
	Function of Boolean is stmtsNeedPoolFrame(Array of Statement is stmts){
		local Boolean is needed: false;
		stmts:each(action: local Function(Statement is s){
			if({ !needed && self:stmtNeedsPoolFrame(stmt: s) }, {
				needed: true;
			});
		});
		return needed;
	}

	## True when [stmt] may allocate or claim into the current scope's ARC
	## claim pool.
	Function of Boolean is stmtNeedsPoolFrame(Statement is stmt){
		return match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				if({ !self:isPrimitiveScalarType(typeName: varType:name) }, {
					return true;
				});
				if({ hasInit }, {
					return self:exprNeedsPoolFrame(expr: initExpr);
				});
				return false;
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				return self:exprNeedsPoolFrame(expr: assignTarget) || self:exprNeedsPoolFrame(expr: assignValue);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					return self:exprNeedsPoolFrame(expr: returnExpr);
				});
				return false;
			},
			Statement:Expr: local Function(Expression is exprStmt){
				return self:exprNeedsPoolFrame(expr: exprStmt);
			},
			else: { true }
		]);
	}

	## True when [call] is a control-flow call whose AnonFn arguments are
	## inlined into the enclosing C scope rather than heap-allocated.
	Function of Boolean is isInlinedControlFlowCall(CallData is call){
		local String is name: call:name;
		return name == 'if' || name == 'match' || name == 'while' || name == 'until' || name == 'repeat';
	}

	## True when [expr] may allocate or claim into the current scope's ARC
	## claim pool.
	Function of Boolean is exprNeedsPoolFrame(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){ return false; },
			Expression:FloatLit: local Function(String is text){ return false; },
			Expression:BoolLit: local Function(Boolean is value){ return false; },
			Expression:Ident: local Function(String is name){ return false; },
			Expression:Path: local Function(Array of String is segments){ return false; },
			Expression:Unary: local Function(String is op, Expression is operand){
				return self:exprNeedsPoolFrame(expr: operand);
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				if({ !self:isPrimitiveScalarType(typeName: expr:resolvedType) }, {
					return true;
				});
				return self:exprNeedsPoolFrame(expr: left) || self:exprNeedsPoolFrame(expr: right);
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				if({ !self:isPrimitiveScalarType(typeName: target) }, {
					return true;
				});
				if({ self:exprNeedsPoolFrame(expr: inner) }, {
					return true;
				});
				local Boolean is needed: false;
				args:each(action: local Function(Expression is a){
					if({ !needed && self:exprNeedsPoolFrame(expr: a) }, {
						needed: true;
					});
				});
				return needed;
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				if({ !self:isPrimitiveScalarType(typeName: expr:resolvedType) }, {
					return true;
				});
				return self:exprNeedsPoolFrame(expr: target);
			},
			Expression:Call: local Function(CallData is call){
				if({ !self:isPrimitiveScalarType(typeName: expr:resolvedType) }, {
					return true;
				});
				if({ self:exprNeedsPoolFrame(expr: call:target) }, {
					return true;
				});
				local Boolean is inlinedCf: self:isInlinedControlFlowCall(call: call);
				local Boolean is needed: false;
				call:args:each(action: local Function(NamedArg is arg){
					if({ !needed }, {
						local Expression is val: arg:value;
						if({ inlinedCf }, {
							match(on: val, when: [
								Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
									if({ self:paramsNeedPoolFrame(params: params) || self:stmtsNeedPoolFrame(stmts: body) }, {
										needed: true;
									});
								},
								else: {
									if({ self:exprNeedsPoolFrame(expr: val) }, {
										needed: true;
									});
								}
							]);
						}, {
							if({ self:exprNeedsPoolFrame(expr: val) }, {
								needed: true;
							});
						});
					});
				});
				return needed;
			},
			else: { true }
		]);
	}

}
