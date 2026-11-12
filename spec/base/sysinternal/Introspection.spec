#! Package base:sysinternal
#! The introspection floor: runtime identity and type queries.

## Floor bindings for object introspection. Methods bind to their C
## implementations per the naming convention (`spec_<snake_case>`); only
## the same-name base:sys wrapper may call them.

Class is Introspection{
	namespace: ['base', 'sysinternal'];

	## The identity hash of an object: a stable per-object value derived
	## from its address (mixed so neighboring allocations differ).
	##
	## @param obj: The object.
	## @return: The hash.
	Function of Int is objectHash(Any is obj);

	## Reference identity: whether [a] and [b] are the same object.
	## Pointer equality — the runtime's identity notion (the held
	## singletons and the enum variants are distinct live instances, so
	## address equality is the identity test).
	##
	## @param a: The first reference.
	## @param b: The second reference.
	## @return: true when both refer to the same object.
	Function of Boolean is sameRef(Any is a, Any is b);

	## The number of HELD members the object's class declares
	## The declaring class's own held surface, in
	## declaration order (the ordinal index).
	##
	## @param obj: The object.
	## @return: The held-member count.
	Function of Int is heldCount(Any is obj);

	## The name of the object's class's held member at the ordinal
	## index (declaration order); an empty string when the index is out
	## of range or the class holds none.
	##
	## @param obj: The object.
	## @param index: The ordinal index.
	## @return: The member name.
	Function of String is heldName(Any is obj, Int is index);

	## Whether the name is a held member of the object's class.
	##
	## @param obj: The object.
	## @param name: The member name.
	## @return: true when held.
	Function of Boolean is hasHeld(Any is obj, String is name);

	## The ordinal scan: the first held-FIELD index whose lazily
	## constructed instance is the object itself. The desugared enum
	## variants are held singletons in declaration order, so this is
	## the variant's ordinal (the reflective identity contract's
	## runtime half — the Enum root's name/ordinal call it). The scan
	## initializes the class's held singletons (the once-guards are
	## idempotent); a class with no held fields yields -1.
	##
	## @param obj: The object.
	## @return: The held-field index, -1 when the object is not one.
	Function of Int is heldIndexOf(Any is obj);

	## --- The class registry (the reflection floor's query surface).
	## Bindings: spec_class_names, spec_method_names,
	## spec_class_source_file, spec_has_method, spec_instantiate,
	## spec_invoke_void_by_name. Loud panics on unknown classes and
	## signature-incompatible invokes --- never silent zeros. ---

	## Every registered class name (class order; sysinternal floors
	## excluded).
	##
	## @return: The class names.
	Function of Array of String is classNames();

	## The method names of a class --- own plus inherited through the base
	## lattice, duplicates collapsed (a child override supersedes).
	##
	## @param className: The class name.
	## @return: The method names.
	Function of Array of String is methodNames(String is className);

	## The declaring source file's basename for a class.
	##
	## @param className: The class name.
	## @return: The basename, empty when unknown.
	Function of String is classSourceFile(String is className);

	## Whether the class declares or inherits a method of the name.
	##
	## @param className: The class name.
	## @param methodName: The method name.
	## @return: true when present.
	Function of Boolean is hasMethod(String is className, String is methodName);

	## Constructs an instance of the class through its registered
	## zero-argument constructor. Panics for unknown classes and classes
	## whose init requires arguments.
	##
	## @param className: The class name.
	## @return: The new instance.
	Function of Any is instantiate(String is className);

	## Invokes a void zero-parameter method on the instance, resolved
	## through the instance's own class. Panics when the method is
	## absent or its signature is not void/zero-params.
	##
	## @param instance: The receiver.
	## @param methodName: The method name.
	Function of Void is invokeVoidByName(Any is instance, String is methodName);

	## --- Lattice membership and type identity: the
	## discovery surface for runners and frameworks. Bindings:
	## spec_type_name, spec_class_extends. ---

	## The runtime class name of [obj]'s own class (the registry's
	## qualified identity, e.g. 'TestByte'). Binds spec_type_identity —
	## the 'typeName' surface name collides with the instance builtin.
	##
	## @param obj: The object.
	## @return: The class name.
	Function of String is typeIdentity(Any is obj);

	## Whether [className] inherits [baseName] anywhere up its base
	## lattice --- the MI-based discovery: a class is a framework test
	## iff it extends the framework's base class. Binds
	## spec_class_extends.
	##
	## @param className: The class name.
	## @param baseName: The base class name.
	## @return: true when the lattice contains the base.
	Function of Boolean is classExtends(String is className, String is baseName);
}
