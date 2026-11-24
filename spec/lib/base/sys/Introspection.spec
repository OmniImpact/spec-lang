#! Package base:sys
#! Pure-Spec runtime reflection and introspection over base:sys:Mem.

## Object introspection: identity hashes, held-member queries, and runtime class/method
## reflection over the module-level @spec_class_registry and @spec_held_registry tables.

Class of Any is Introspection{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is heldEntryOf(Any is obj){
		local Int is objAddr: Mem:objToAddr(obj: obj);
		if({ objAddr < 4096 }, { return 0; });
		local Int is tnCstr: Mem:loadI64(ptr: objAddr, byteOffset: 0);
		if({ tnCstr == 0 }, { return 0; });
		local String is objTn: Mem:cstrToStr(cstrAddr: tnCstr);
		local Int is reg: Mem:heldRegistryAddr();
		local Int is i: 0;
		while({ true }, {
			local Int is entryAddr: reg + (i * 32);
			local Int is eTnCstr: Mem:loadI64(ptr: entryAddr, byteOffset: 0);
			if({ eTnCstr == 0 }, { return 0; });
			if({ Mem:cstrToStr(cstrAddr: eTnCstr) == objTn }, {
				return entryAddr;
			});
			i: i + 1;
		});
		return 0;
	}

	local Function of Int is findClassMeta(String is className){
		local Int is reg: Mem:classRegistryAddr();
		local Int is cnt: Mem:classRegistryCount();
		local Int is i: 0;
		while({ i < cnt }, {
			local Int is metaAddr: Mem:loadI64(ptr: reg, byteOffset: i * 8);
			if({ metaAddr != 0 }, {
				local Int is nmCstr: Mem:loadI64(ptr: metaAddr, byteOffset: 0);
				if({ nmCstr != 0 && Mem:cstrToStr(cstrAddr: nmCstr) == className }, {
					return metaAddr;
				});
			});
			i: i + 1;
		});
		return 0;
	}

	local Function of Int is findMethodMeta(Int is clsMeta, String is methodName){
		if({ clsMeta == 0 }, { return 0; });
		local Int is mCount: Mem:loadI32(ptr: clsMeta, byteOffset: 48);
		local Int is mArr: Mem:loadI64(ptr: clsMeta, byteOffset: 40);
		local Int is i: 0;
		while({ i < mCount }, {
			local Int is mAddr: mArr + (i * 24);
			local Int is mNameCstr: Mem:loadI64(ptr: mAddr, byteOffset: 0);
			if({ mNameCstr != 0 && Mem:cstrToStr(cstrAddr: mNameCstr) == methodName }, {
				return mAddr;
			});
			i: i + 1;
		});
		local Int is bCount: Mem:loadI32(ptr: clsMeta, byteOffset: 24);
		local Int is bArr: Mem:loadI64(ptr: clsMeta, byteOffset: 16);
		local Int is b: 0;
		while({ b < bCount }, {
			local String is bName: Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: bArr, byteOffset: b * 8));
			local Int is found: :findMethodMeta(clsMeta: :findClassMeta(className: bName), methodName: methodName);
			if({ found != 0 }, { return found; });
			b: b + 1;
		});
		return 0;
	}

	local Function is collectMethodNames(Array of String is out, Int is clsMeta){
		if({ clsMeta == 0 }, { return; });
		local Int is bCount: Mem:loadI32(ptr: clsMeta, byteOffset: 24);
		local Int is bArr: Mem:loadI64(ptr: clsMeta, byteOffset: 16);
		local Int is b: bCount - 1;
		while({ b >= 0 }, {
			local String is bName: Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: bArr, byteOffset: b * 8));
			:collectMethodNames(out: out, clsMeta: :findClassMeta(className: bName));
			b: b - 1;
		});
		local Int is mCount: Mem:loadI32(ptr: clsMeta, byteOffset: 48);
		local Int is mArr: Mem:loadI64(ptr: clsMeta, byteOffset: 40);
		local Int is i: 0;
		while({ i < mCount }, {
			local Int is mAddr: mArr + (i * 24);
			local String is nm: Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: mAddr, byteOffset: 0));
			local Boolean is dup: false;
			local Int is j: 0;
			while({ j < out:length() && !dup }, {
				if({ out:get(index: j, default: '') == nm }, { dup: true; });
				j: j + 1;
			});
			if({ !dup }, { out:add(item: nm); });
			i: i + 1;
		});
	}

	local Function of Boolean is extendsWalk(Int is clsMeta, String is baseName, Int is depth){
		if({ clsMeta == 0 || depth > 64 }, { return false; });
		local Int is bCount: Mem:loadI32(ptr: clsMeta, byteOffset: 24);
		local Int is bArr: Mem:loadI64(ptr: clsMeta, byteOffset: 16);
		local Int is b: 0;
		while({ b < bCount }, {
			local String is bn: Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: bArr, byteOffset: b * 8));
			if({ bn == baseName }, { return true; });
			if({ :extendsWalk(clsMeta: :findClassMeta(className: bn), baseName: baseName, depth: depth + 1) }, {
				return true;
			});
			b: b + 1;
		});
		return false;
	}

	## The identity hash of an object: a stable per-object value derived
	## from its address (mixed so neighboring allocations differ).
	Function of Int is objectHash(Any is obj){
		local Int is h: Mem:objToAddr(obj: obj);
		if({ h == 0 }, { return 0; });
		h: h ^ ((h >> 33) & 2147483647);
		h: h * 1099511628211;
		h: h ^ ((h >> 33) & 2147483647);
		return h;
	}

	## Reference identity: whether [a] and [b] are the same object.
	Function of Boolean is sameRef(Any is a, Any is b){
		return Mem:objToAddr(obj: a) == Mem:objToAddr(obj: b);
	}

	## The number of HELD members the object's class declares.
	Function of Int is heldCount(Any is obj){
		local Int is e: :heldEntryOf(obj: obj);
		if({ e == 0 }, { return 0; });
		return Mem:loadI32(ptr: e, byteOffset: 16);
	}

	## The name of the object's class's held member at the ordinal index.
	Function of String is heldName(Any is obj, Int is index){
		local Int is e: :heldEntryOf(obj: obj);
		if({ e == 0 || index < 0 }, { return ''; });
		local Int is cnt: Mem:loadI32(ptr: e, byteOffset: 16);
		if({ index >= cnt }, { return ''; });
		local Int is namesArr: Mem:loadI64(ptr: e, byteOffset: 8);
		return Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: namesArr, byteOffset: index * 8));
	}

	## Whether the name is a held member of the object's class.
	Function of Boolean is hasHeld(Any is obj, String is name){
		local Int is e: :heldEntryOf(obj: obj);
		if({ e == 0 }, { return false; });
		local Int is cnt: Mem:loadI32(ptr: e, byteOffset: 16);
		local Int is namesArr: Mem:loadI64(ptr: e, byteOffset: 8);
		local Int is i: 0;
		while({ i < cnt }, {
			if({ Mem:cstrToStr(cstrAddr: Mem:loadI64(ptr: namesArr, byteOffset: i * 8)) == name }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## The ordinal scan: the first held-FIELD index whose lazily
	## constructed instance is the object itself.
	Function of Int is heldIndexOf(Any is obj){
		local Int is e: :heldEntryOf(obj: obj);
		if({ e == 0 }, { return -1; });
		local Int is gettersArr: Mem:loadI64(ptr: e, byteOffset: 24);
		if({ gettersArr == 0 }, { return -1; });
		local Int is cnt: Mem:loadI32(ptr: e, byteOffset: 16);
		local Int is objAddr: Mem:objToAddr(obj: obj);
		local Int is i: 0;
		while({ i < cnt }, {
			local Int is gFn: Mem:loadI64(ptr: gettersArr, byteOffset: i * 8);
			if({ gFn != 0 }, {
				local Any is inst: Mem:callConstruct(fnAddr: gFn);
				local Int is instAddr: Mem:objToAddr(obj: inst);
				Mem:releaseAddr(objAddr: instAddr);
				if({ instAddr == objAddr }, { return i; });
			});
			i: i + 1;
		});
		return -1;
	}

	## Every registered class name, in class order.
	Function of Array of String is classNames(){
		local Array of String is out: Array();
		local Int is reg: Mem:classRegistryAddr();
		local Int is cnt: Mem:classRegistryCount();
		local Int is i: 0;
		while({ i < cnt }, {
			local Int is metaAddr: Mem:loadI64(ptr: reg, byteOffset: i * 8);
			if({ metaAddr != 0 }, {
				local Int is nmCstr: Mem:loadI64(ptr: metaAddr, byteOffset: 0);
				if({ nmCstr != 0 }, {
					out:add(item: Mem:cstrToStr(cstrAddr: nmCstr));
				});
			});
			i: i + 1;
		});
		return out;
	}

	## The functions of a class --- own plus inherited through the base lattice.
	Function of Array of Array of String is functions(String is className){
		local Array of Array of String is out: Array();
		local Array of String is names: Array();
		:collectMethodNames(out: names, clsMeta: :findClassMeta(className: className));
		names:each(action: local Function(String is m){
			local Array of String is path: Array();
			path:add(item: className);
			path:add(item: m);
			out:add(item: path);
		});
		return out;
	}

	## The declaring source file's basename for a class.
	Function of String is classSourceFile(String is className){
		local Int is m: :findClassMeta(className: className);
		if({ m == 0 }, { return ''; });
		local Int is sfCstr: Mem:loadI64(ptr: m, byteOffset: 8);
		if({ sfCstr == 0 }, { return ''; });
		return Mem:cstrToStr(cstrAddr: sfCstr);
	}

	## Whether the class declares or inherits a method of the name.
	Function of Boolean is hasMethod(String is className, String is methodName){
		return :findMethodMeta(clsMeta: :findClassMeta(className: className), methodName: methodName) != 0;
	}

	## Constructs an instance of the class through its registered zero-argument constructor.
	Function of Any is instantiate(String is className){
		local Int is m: :findClassMeta(className: className);
		if({ m == 0 }, {
			Mem:panic(msg: 'Introspection:instantiate — unknown class');
			return Mem:addrToObj(addr: 0);
		});
		local Int is ctorFn: Mem:loadI64(ptr: m, byteOffset: 32);
		if({ ctorFn == 0 }, {
			Mem:panic(msg: 'Introspection:instantiate — class init requires arguments');
			return Mem:addrToObj(addr: 0);
		});
		return Mem:callConstruct(fnAddr: ctorFn);
	}

	## Invokes a void zero-parameter method on the instance.
	Function of Void is invokeVoid(Any is instance, String is methodName){
		local Int is instAddr: Mem:objToAddr(obj: instance);
		if({ instAddr == 0 }, {
			Mem:panic(msg: 'Introspection:invoke on a null instance');
			return;
		});
		local Int is tnCstr: Mem:loadI64(ptr: instAddr, byteOffset: 0);
		local Int is m: :findClassMeta(className: Mem:cstrToStr(cstrAddr: tnCstr));
		if({ m == 0 }, {
			Mem:panic(msg: 'Introspection:invoke — instance of an unregistered class');
			return;
		});
		local Int is mm: :findMethodMeta(clsMeta: m, methodName: methodName);
		if({ mm == 0 }, {
			Mem:panic(msg: 'Introspection:invoke — no such method');
			return;
		});
		local Int is fnAddr: Mem:loadI64(ptr: mm, byteOffset: 8);
		local Int is flags: Mem:loadI32(ptr: mm, byteOffset: 16);
		if({ fnAddr == 0 || (flags & 2) == 0 || (flags & 5) == 0 }, {
			Mem:panic(msg: 'Introspection:invoke supports void zero-parameter methods only');
			return;
		});
		Mem:callDestroy(fnPtr: fnAddr, objPtr: instAddr);
	}

	## The runtime class name of [obj]'s own class.
	Function of String is typeIdentity(Any is obj){
		return Mem:typeNameOf(obj: obj);
	}

	## Whether [className] inherits [baseName] anywhere up its base lattice.
	Function of Boolean is extendsClass(String is className, String is baseName){
		return :extendsWalk(clsMeta: :findClassMeta(className: className), baseName: baseName, depth: 0);
	}

	## Discovers every registered strict subclass of [baseName] and instantiates each.
	Function of Array of Any is instantiateSubclasses(String is baseName){
		local Array of String is names: :classNames();
		local Array of Any is found: Array();
		local Int is i: 0;
		while({ i < names:length() }, {
			local String is cname: names:get(index: i, default: '');
			if({ cname != baseName && :extendsClass(className: cname, baseName: baseName) }, {
				found:add(item: :instantiate(className: cname));
			});
			i++;
		});
		return found;
	}

	local Function of Int is findFieldMeta(Any is obj, String is name){
		local Int is objAddr: Mem:objToAddr(obj: obj);
		if({ objAddr < 4096 }, { return 0; });
		local Int is tnCstr: Mem:loadI64(ptr: objAddr, byteOffset: 0);
		if({ tnCstr == 0 }, { return 0; });
		local Int is clsMeta: :findClassMeta(className: Mem:cstrToStr(cstrAddr: tnCstr));
		if({ clsMeta == 0 }, { return 0; });
		local Int is fCount: Mem:loadI32(ptr: clsMeta, byteOffset: 64);
		local Int is fArr: Mem:loadI64(ptr: clsMeta, byteOffset: 56);
		if({ fArr == 0 || fCount <= 0 }, { return 0; });
		local Int is i: 0;
		while({ i < fCount }, {
			local Int is fAddr: fArr + (i * 24);
			local Int is fnCstr: Mem:loadI64(ptr: fAddr, byteOffset: 0);
			if({ fnCstr != 0 && Mem:cstrToStr(cstrAddr: fnCstr) == name }, {
				return fAddr;
			});
			i: i + 1;
		});
		return 0;
	}

	## Whether [obj]'s class has an instance field named [name].
	Function of Boolean is hasField(Any is obj, String is name){
		return :findFieldMeta(obj: obj, name: name) != 0;
	}

	## Declared Spec type name of field [name] on [obj], or '' when absent.
	Function of String is fieldType(Any is obj, String is name){
		local Int is fm: :findFieldMeta(obj: obj, name: name);
		if({ fm == 0 }, { return ''; });
		local Int is ftCstr: Mem:loadI64(ptr: fm, byteOffset: 8);
		if({ ftCstr == 0 }, { return ''; });
		return Mem:cstrToStr(cstrAddr: ftCstr);
	}

	## Reads field [name] on [obj] as [Any].
	Function of Any is getField(Any is obj, String is name){
		local Int is fm: :findFieldMeta(obj: obj, name: name);
		if({ fm == 0 }, { return Mem:addrToObj(addr: 0); });
		local Int is objAddr: Mem:objToAddr(obj: obj);
		local Int is off: Mem:loadI32(ptr: fm, byteOffset: 16);
		local Int is flags: Mem:loadI32(ptr: fm, byteOffset: 20);
		if({ (flags & 16) != 0 }, {
			return Mem:loadPtr(ptr: objAddr, byteOffset: off);
		});
		if({ (flags & 2) != 0 || (flags & 32) != 0 }, {
			return Mem:addrToObj(addr: Mem:loadByte(ptr: objAddr, byteOffset: off));
		});
		if({ (flags & 64) != 0 }, {
			return Mem:addrToObj(addr: Mem:loadI32(ptr: objAddr, byteOffset: off));
		});
		return Mem:addrToObj(addr: Mem:loadI64(ptr: objAddr, byteOffset: off));
	}

	## Assigns [value] into field [name] on [obj] (handling ARC retain/release for pointer fields).
	Function is setField(Any is obj, String is name, Any is value){
		local Int is fm: :findFieldMeta(obj: obj, name: name);
		if({ fm == 0 }, { return; });
		local Int is objAddr: Mem:objToAddr(obj: obj);
		local Int is off: Mem:loadI32(ptr: fm, byteOffset: 16);
		local Int is flags: Mem:loadI32(ptr: fm, byteOffset: 20);
		if({ (flags & 16) != 0 }, {
			local Int is newAddr: Mem:objToAddr(obj: value);
			if({ (flags & 1) != 0 }, {
				local Int is oldAddr: Mem:loadI64(ptr: objAddr, byteOffset: off);
				if({ newAddr != oldAddr }, {
					if({ newAddr != 0 }, { Mem:retainAddr(objAddr: newAddr); });
					if({ oldAddr != 0 }, { Mem:releaseAddr(objAddr: oldAddr); });
				});
			});
			Mem:storePtr(ptr: objAddr, byteOffset: off, val: value);
			return;
		});
		if({ (flags & 2) != 0 || (flags & 32) != 0 }, {
			Mem:storeByte(ptr: objAddr, byteOffset: off, val: Mem:objToAddr(obj: value));
			return;
		});
		if({ (flags & 64) != 0 }, {
			Mem:storeI32(ptr: objAddr, byteOffset: off, val: Mem:objToAddr(obj: value));
			return;
		});
		Mem:storeI64(ptr: objAddr, byteOffset: off, val: Mem:objToAddr(obj: value));
	}
}
