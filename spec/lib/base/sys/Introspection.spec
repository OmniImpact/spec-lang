#! Package base:sys
#! Public wrapper over the sysinternal introspection floor.

## Object introspection: identity hashes and runtime type queries.
## The ONLY class allowed to call base:sysinternal:Introspection is the
## same-name wrapper (the sysinternal discipline).

Class is Introspection{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Introspection]
	];

	## The identity hash of an object: a stable per-object value derived
	## from its address (mixed so neighboring allocations differ).
	##
	## @param obj: The object.
	## @return: The hash.
	Function of Int is objectHash(Any is obj){
		return base:sysinternal:Introspection:objectHash(obj: obj);
	}

	## Reference identity: whether [a] and [b] are the same object.
	## Pointer equality — the runtime's identity notion (the held
	## singletons and the enum variants are distinct live instances, so
	## address equality is the identity test).
	##
	## @param a: The first reference.
	## @param b: The second reference.
	## @return: true when both refer to the same object.
	Function of Boolean is sameRef(Any is a, Any is b){
		return base:sysinternal:Introspection:sameRef(a: a, b: b);
	}

	## The number of HELD members the object's class declares
	## The declaring class's own held surface, in
	## declaration order (the ordinal index).
	##
	## @param obj: The object.
	## @return: The held-member count.
	Function of Int is heldCount(Any is obj){
		return base:sysinternal:Introspection:heldCount(obj: obj);
	}

	## The name of the object's class's held member at the ordinal
	## index (declaration order); an empty string when the index is out
	## of range or the class holds none.
	##
	## @param obj: The object.
	## @param index: The ordinal index.
	## @return: The member name.
	Function of String is heldName(Any is obj, Int is index){
		return base:sysinternal:Introspection:heldName(obj: obj, index: index);
	}

	## Whether the name is a held member of the object's class.
	##
	## @param obj: The object.
	## @param name: The member name.
	## @return: true when held.
	Function of Boolean is hasHeld(Any is obj, String is name){
		return base:sysinternal:Introspection:hasHeld(obj: obj, name: name);
	}

	## The ordinal scan: the first held-FIELD index whose lazily
	## constructed instance is the object itself. The desugared enum
	## variants are held singletons in declaration order, so this is
	## the variant's ordinal (the Enum root's name/ordinal call it).
	## The scan initializes the class's held singletons (the
	## once-guards are idempotent); a class with no held fields
	## yields -1.
	##
	## @param obj: The object.
	## @return: The held-field index, -1 when the object is not one.
	Function of Int is heldIndexOf(Any is obj){
		return base:sysinternal:Introspection:heldIndexOf(obj: obj);
	}

	## --- The class registry (see SPECUNIT.md). The floor's panics are
	## the contract: unknown classes and signature-incompatible invokes
	## are loud, never silent. ---

	## Every registered class name, in class order. Sysinternal floors
	## are excluded; enum-model and transparent classes register with
	## no constructor.
	##
	## @return: The class names.
	Function of Array of String is classNames(){
		return base:sysinternal:Introspection:classNames();
	}

	## The method names of a class --- own plus inherited through the base
	## lattice, duplicates collapsed (a child override supersedes).
	##
	## @param className: The class name.
	## @return: The method names.
	Function of Array of String is methodNames(String is className){
		return base:sysinternal:Introspection:methodNames(className: className);
	}

	## The declaring source file's basename for a class (the basename
	## only: full paths vary with the invocation directory).
	##
	## @param className: The class name.
	## @return: The basename, empty when unknown.
	Function of String is classSourceFile(String is className){
		return base:sysinternal:Introspection:classSourceFile(className: className);
	}

	## Whether the class declares or inherits a method of the name.
	##
	## @param className: The class name.
	## @param methodName: The method name.
	## @return: true when present.
	Function of Boolean is hasMethod(String is className, String is methodName){
		return base:sysinternal:Introspection:hasMethod(className: className, methodName: methodName);
	}

	## Constructs an instance of the class through its registered
	## zero-argument constructor. Panics for unknown classes and
	## classes whose init requires arguments.
	##
	## @param className: The class name.
	## @return: The new instance.
	Function of Any is instantiate(String is className){
		return base:sysinternal:Introspection:instantiate(className: className);
	}

	## Invokes a void zero-parameter method on the instance, resolved
	## through the instance's own class. Panics when the method is
	## absent or its signature is not void/zero-params.
	##
	## @param instance: The receiver.
	## @param methodName: The method name.
	Function of void is invokeVoid(Any is instance, String is methodName){
		base:sysinternal:Introspection:invokeVoidByName(instance: instance, methodName: methodName);
	}
}
