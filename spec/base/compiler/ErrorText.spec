#! Package base:compiler
#! The error-message wordings shared by compiler passes.
##
## One cohesive, template-built vocabulary: passes own an instance (the
## composition pattern the Lexer uses), so wording changes happen in
## exactly one place.

Class is ErrorText{
	replace Array of String is namespace: ['base', 'compiler'];

	# --- Lexer Diagnostics ---

	## Message for a heredoc whose closing delimiter never appears.
	Function of String is errUnterminatedHeredoc(String is quote){
		return "Unterminated heredoc (missing closing {{quote}})";
	}

	## Message for a digit that does not belong to the literal's base.
	Function of String is errInvalidDigitInBase(Int is base){
		return "Invalid digit in base-{{base}} number literal";
	}

	## Message for a base-prefixed literal with no digits after the prefix.
	Function of String is errMissingDigitsAfterPrefix(){
		return 'Missing digits after base prefix';
	}

	# --- Parser Diagnostics ---

	## Message when an expected token is not found.
	Function of String is errExpectedFound(String is expected, String is found){
		return "Expected '{{expected}}', found '{{found}}'";
	}

	## Message for deprecated class keyword.
	Function of String is errObsoleteClassKeyword(){
		return "The 'class' keyword is no longer valid; declare classes as 'Class of Parent is Name'.";
	}

	## Message when 'as' in using is not followed by class name.
	Function of String is errUsingAsRequiresClass(){
		return "'as' in a using entry must be followed by a class name.";
	}

	## Message when instance-import args are not direct literals.
	Function of String is errInstanceImportLiteralArgs(){
		return 'Instance-import arguments must be direct literal values (E1).';
	}

	## Message when instance-import lacks parentheses.
	Function of String is errInstanceImportParens(String is target){
		return "Instance import requires parentheses: 'as " . target . "()'.";
	}

	## Message when chained 'as' casts are used.
	Function of String is errChainedAsUnsupported(){
		return "Chained 'as' casts are not supported; cast in separate steps.";
	}

	## Message for unexpected token in an expression.
	Function of String is errUnexpectedTokenInExpression(String is token){
		return "Unexpected token '{{token}}' in expression";
	}

	## Message for unterminated string template hole.
	Function of String is errUnterminatedTemplateHole(){
		return 'Unterminated template hole (missing closing }})';
	}

	## Message for empty string template expression.
	Function of String is errEmptyTemplateExpression(){
		return 'Empty expression in string template';
	}

	## Message for invalid string template expression.
	Function of String is errInvalidTemplateExpression(){
		return 'Invalid expression in string template';
	}

	# --- Loader Diagnostics ---

	## Message when a module file cannot be found on disk.
	Function of String is errModuleFileNotFound(String is path){
		return '  [LoadError] Module file not found: ' . path;
	}

	## Message for malformed using declaration array.
	Function of String is errMalformedImport(String is className){
		return '  [LoadError] Malformed import in class \'' . className . '\': using entries are package-segment arrays.';
	}

	## Message when an import package path cannot be resolved.
	Function of String is errCannotResolveImport(String is wanted, String is className){
		return '  [LoadError] Cannot resolve import \'[' . wanted . ']\' declared in class \'' . className . '\'.';
	}

	## Message when a synthetic import field name collides with a declared member.
	Function of String is errSyntheticImportCollision(String is fieldName, String is className){
		return '  [LoadError] \'' . fieldName . '\' collides with a declared member in class \'' . className . '\'; synthetic import fields reserve the name.';
	}

	# --- TypeChecker / Semantic Diagnostics ---

	## Message for argument type mismatch.
	Function of String is errCannotAssignArg(String is label, String is target, String is method, String is fromType, String is toType){
		return 'Argument \'' . label . '\' for \'' . target . '.' . method . '\': cannot assign \'' . fromType . '\' to \'' . toType . '\'.';
	}

	## Message for missing named argument.
	Function of String is errMissingArg(String is paramName, String is target, String is method){
		return 'Missing argument \'' . paramName . '\' for \'' . target . '.' . method . '\'.';
	}

	## Message for undeclared member on class.
	Function of String is errMemberNotDeclared(String is member, String is targetType){
		return 'Member \'' . member . '\' is not declared on class \'' . targetType . '\'.';
	}

	## Message for calling member on Any.
	Function of String is errMemberNotRootContract(String is member){
		return 'Member \'' . member . '\' is not part of the root contract; cast the Any-typed value to a concrete class before calling it (value as ClassName).';
	}

	## Message for mismatched branch types.
	Function of String is errBranchMismatchedTypes(String is thenType, String is elseType){
		return 'Branch yields mismatched types: \'' . thenType . '\' and \'' . elseType . '\'.';
	}

	## Message for value-yielding branch not ending in expression.
	Function of String is errBranchRequiresExpressions(){
		return 'A value-yielding branch requires both branches to end in an expression.';
	}

	## Message for vars loop without inline literal closures.
	Function of String is errLoopVarsClosureLiteral(){
		return 'The loop variables scope their closures at the call site: a [vars] loop form requires inline literal closures.';
	}

	## Message for calling self method from held member.
	Function of String is errHeldNoInstance(String is method){
		return 'A held member body has no instance: \'' . method . '\' cannot be called on \'self\' from it.';
	}

	## Message for calling held function through instance.
	Function of String is errHeldClassScoped(String is className, String is method){
		return 'Held function \'' . className . ':' . method . '\' is class-scoped: call it through the class name, not an instance.';
	}

	## Message for direct sysinternal floor access.
	Function of String is errSysinternalRestricted(String is caller){
		return 'The sysinternal floor is only accessible from base:sys wrappers; call the base:sys wrapper instead (call from \'' . caller . '\').';
	}

	## Message for constructing type not imported.
	Function of String is errTypeNotImported(String is targetType, String is currentClass){
		return '\'' . targetType . '\' is not imported by \'' . currentClass . '\'; add it to the using declaration to construct it (§I.6).';
	}

	## Message for bitwise operator operand type mismatch.
	Function of String is errBitwiseOperandsInt(String is op, String is leftT, String is rightT){
		return 'Bitwise operator \'' . op . '\' requires Int operands (got \'' . leftT . '\' and \'' . rightT . '\').';
	}

	## Message for bitwise complement operand type mismatch.
	Function of String is errBitwiseComplementInt(String is innerT){
		return 'Bitwise complement \'~\' requires an Int operand (got \'' . innerT . '\').';
	}

	## Message for operator requiring Int operand.
	Function of String is errOperatorRequiresInt(String is op, String is innerT){
		return 'Operator \'' . op . '\' requires an Int operand (got \'' . innerT . '\').';
	}

	## Message for closure return type mismatch.
	Function of String is errClosureReturnType(String is actual, String is expected){
		return 'The closure\'s last expression yields \'' . actual . '\', but the closure must return \'' . expected . '\'.';
	}

	## Message for variable declaration type mismatch.
	Function of String is errTypeMismatchDecl(String is varName, String is initType, String is fullType){
		return 'Type mismatch in variable declaration for \'' . varName . '\': cannot assign \'' . initType . '\' to \'' . fullType . '\'.';
	}

	## Message for assignment type mismatch.
	Function of String is errTypeMismatchAssign(String is valType, String is targetType){
		return 'Type mismatch in assignment: cannot assign \'' . valType . '\' to \'' . targetType . '\'.';
	}

	## Message for assigning to read-only held member.
	Function of String is errHeldReadOnly(String is root, String is name){
		return 'Held member \'' . root . ':' . name . '\' is read-only: held members are class-scoped single copies, assigned once by their initializer.';
	}

	## Message for assigning to read-only resolved member.
	Function of String is errResolvedReadOnly(String is root, String is name){
		return 'Resolved member \'' . root . ':' . name . '\' is read-only: resolution-hook values are cached single copies.';
	}

	## Message for method return type mismatch.
	Function of String is errMethodReturnTypeMismatch(String is expected, String is actual, String is details){
		return 'Method declared return type \'' . expected . '\', but returned \'' . actual . '\'' . details . '.';
	}

	## Message for missing return value.
	Function of String is errMethodEmptyReturn(String is expected){
		return 'Method expects return value of type \'' . expected . '\', but found empty return.';
	}

	## Message for forward without merge.
	Function of String is errForwardRequiresMerge(){
		return 'Forward statement `(args...)` requires the enclosing method to declare \'merge\'.';
	}

	## Message for forward inside nested function.
	Function of String is errForwardNestedNotAllowed(){
		return 'Forward statement is not allowed inside a nested function.';
	}

	## Message for multiple forward statements in method.
	Function of String is errForwardMultipleNotAllowed(String is method){
		return 'Multiple forward statements in method \'' . method . '\'; at most one is allowed.';
	}

	## Message for forward with no parent method.
	Function of String is errForwardNoParentMethod(String is method){
		return 'Forward statement in \'' . method . '\': no parent method to delegate to.';
	}

	## Message for forward argument count mismatch.
	Function of String is errForwardArgCountMismatch(String is method, String is parentMethod, Int is passed, Int is accepted){
		return 'Forward statement passes ' . (passed as String) . ' arguments but parent \'' . parentMethod . '\' accepts ' . (accepted as String) . '.';
	}

	## Message for partial forward with unnamed argument.
	Function of String is errForwardNamedRequired(Int is argNum, String is method){
		return 'Partial forward requires named arguments; argument ' . (argNum as String) . ' of \'' . method . '\' is unnamed.';
	}

	## Message for replacing or merging overloaded method.
	Function of String is errCannotOverrideOverload(String is method){
		return 'Cannot replace or merge an overloaded method (\'' . method . '\' has multiple signatures); give each signature a distinct name (§I.3).';
	}

	## Message for merge method without matching parent.
	Function of String is errMergeNoParent(String is method, String is className){
		return 'Method \'' . method . '\' in class \'' . className . '\' declares \'merge\' but no parent declares a method with that name.';
	}

	## Message for merge method lacking forward statement.
	Function of String is errMergeMustForward(String is method, String is className){
		return 'Merge method \'' . method . '\' in class \'' . className . '\' must contain a forward statement `(args...)`.';
	}

	## Message for accessing local member from outside class.
	Function of String is errMemberLocal(String is member, String is ownerClass, String is currentClass){
		return 'Member \'' . member . '\' is local to class \'' . ownerClass . '\' and cannot be accessed from \'' . currentClass . '\'.';
	}

	## Message for accessing contained member from unrelated class.
	Function of String is errMemberContained(String is member, String is ownerClass, String is currentClass){
		return 'Member \'' . member . '\' is contained in class \'' . ownerClass . '\' and cannot be accessed from unrelated class \'' . currentClass . '\'.';
	}

	## Message for combining held with replace/merge.
	Function of String is errHeldCombinesReplaceMerge(String is member, String is className){
		return 'Member \'' . member . '\' in class \'' . className . '\' combines \'held\' with \'replace\'/\'merge\'; held members are single-copy and cannot be overridden.';
	}

	## Message for duplicate held function declaration.
	Function of String is errHeldDuplicate(String is member){
		return 'Held function \'' . member . '\' is declared more than once; held functions do not overload.';
	}

	## Message for held field without initializer.
	Function of String is errHeldFieldRequiresInitializer(String is field, String is className){
		return 'Held field \'' . field . '\' in class \'' . className . '\' requires an initializer; held members construct lazily, once, on first access.';
	}

	## Message for duplicate instance import (E3).
	Function of String is errDuplicateInstanceImport(String is className, String is asName){
		return 'Class \'' . className . '\' instance-imports \'' . asName . '\' more than once (E3).';
	}

	## Message for instance-importing an enum (E2).
	Function of String is errCannotInstanceImportEnum(String is asName){
		return 'Cannot instance-import enum \'' . asName . '\'; enums are type-level (E2).';
	}

	## Message for instance import cycle (E4).
	Function of String is errInstanceImportCycle(String is cycle){
		return 'Instance import cycle: ' . cycle . ' (E4); construction would recurse forever.';
	}

	## Message for inheriting conflicting method implementations.
	Function of String is errConflictingInheritedMethods(String is className, String is method, String is classA, String is classB){
		return 'ClassInfo \'' . className . '\' inherits conflicting implementations of \'' . method . '\' from \'' . classA . '\' and \'' . classB . '\'; declare the method (replace or merge) to resolve the conflict.';
	}

	## Message for unimplemented abstract member.
	Function of String is errUnimplementedAbstract(String is className, String is member, String is parentClass){
		return 'ClassInfo \'' . className . '\' does not implement abstract member \'' . member . '\' required by parent \'' . parentClass . '\'.';
	}
}
