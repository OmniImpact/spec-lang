#! Package compiler
#! Prelude emission, class/field/method lookup helpers, and when-condition C generation.
#! Group fragment merged into CodeGenerator at load time (see Loader).

## Prelude emission, class/field/method lookup helpers, and when-condition C generation.
Class is CodeGeneratorLookups{

	## Load-time grouping: members merge into CodeGenerator.
	local Array of String is group: [CodeGenerator];

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*
	];

	local Function of String is generatePrelude(){
		return self:prelude:emitRuntime();
	}

	Class is ClassSearchLoop extends Loop{
		local Array of ClassInfo is list;
		local String is target;
		local Int is idx: 0;
		local ClassInfo is res;
		local Boolean is found: false;

		replace local Function is init(Array of ClassInfo is list, String is target){
			self:list: list;
			self:target: target;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local ClassInfo is cand: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (cand:getName() == self:target) {
				self:res: cand;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	local Function of ClassInfo is findClass(String is name){
		local ClassSearchLoop is s: ClassSearchLoop:init(list: self:programClasses, target: name);
		While:run(loop: s);
		if (s:found) {
			return s:res;
		}
		return ClassInfo:init(name: "", baseClass: "", members: []);
	}

	Class is FieldMemberLoop extends Loop{
		local Array of Member is members;
		local String is fieldName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace local Function is init(Array of Member is members, String is fieldName){
			self:members: members;
			self:fieldName: fieldName;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:getKind() == "FIELD" && m:getName() == self:fieldName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	local Function of String is lookupFieldType(String is className, String is fieldName){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:getMembers(), fieldName: fieldName);
		While:run(loop: fl);
		if (fl:found) {
			local Member is foundM: fl:res;
			local String is rawT: self:formatTypeString(t: foundM:getType());
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:lookupFieldType(className: baseName, fieldName: fieldName);
			}
		});
		return inherited;
	}

	Class is MethodMemberLoop extends Loop{
		local Array of Member is members;
		local String is methodName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace local Function is init(Array of Member is members, String is methodName){
			self:members: members;
			self:methodName: methodName;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:getKind() == "METHOD" && m:getName() == self:methodName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	local Function of Member is lookupEnumVariant(String is enumName, String is variantName){
		local ClassInfo is cls: self:findClass(name: enumName);
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:getMembers(), fieldName: variantName);
		While:run(loop: fl);
		if (fl:found) {
			return fl:res;
		}
		return Member:init(kind: "");
	}

	local Function of String is generateWhenCondition(Expression is subjExpr, String is subjC, Expression is c){
		if (c:getKind() == "CALL" && self:allEnumVariants:has(key: c:methodName)) {
			local String is eName: self:allEnumVariants:getString(key: c:methodName, default: "");
			if (self:allTaggedEnums:has(key: eName)) {
				return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: c:methodName) . ")";
			}
		}
		if (c:getKind() == "IDENT" && self:allEnumVariants:has(key: c:stringValue)) {
			local String is eName: self:allEnumVariants:getString(key: c:stringValue, default: "");
			if (self:allTaggedEnums:has(key: eName)) {
				return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: c:stringValue) . ")";
			}
		}
		if (c:getKind() == "PATH" && c:pathSegments:length() >= 2 && self:allTaggedEnums:has(key: c:pathSegments:get(index: 0))) {
			local String is eName: c:pathSegments:get(index: 0);
			local String is vName: c:pathSegments:get(index: 1);
			return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: vName) . ")";
		}
		local String is cVal: self:generateExpression(expr: c);
		if (self:isStringExpr(expr: subjExpr)) {
			return "spec_str_equals(" . subjC . ", " . cVal . ")";
		}
		return "((" . subjC . ") == (" . cVal . "))";
	}

	local Function of String is generateWhenBindings(String is subjC, WhenArm is arm){
		local String is binds: "";
		arm:conditions:each(action: local Function(Expression is c){
			if (c:getKind() == "CALL" && self:allEnumVariants:has(key: c:methodName)) {
				local String is eName: self:allEnumVariants:getString(key: c:methodName, default: "");
				if (self:allTaggedEnums:has(key: eName)) {
					local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: c:methodName);
					local String is vNameC: self:cIdent(name: c:methodName);
					local Int is idx: 0;
					c:methodArgs:each(action: local Function(NamedArg is arg){
						if (idx < vMem:getParameters():length()) {
							local Expression is av: arg:getValue();
							if (av:getKind() == "IDENT") {
								local Parameter is pDef: vMem:getParameters():get(index: idx);
								local String is bindName: av:stringValue;
								self:localVars:set(key: bindName, value: self:formatVarTypeString(t: pDef:getType()));
								local String is pCType: self:cTypeFor(typeName: pDef:getType():getName());
								binds: binds . "        " . pCType . " " . self:cIdent(name: bindName) . " = (" . subjC . ")->" . vNameC . "_" . self:cIdent(name: pDef:getName()) . ";\n";
							}
						}
						idx: idx + 1;
					});
				}
			}
		});
		return binds;
	}

	local Function of String is findMethodImplementingClass(String is className, String is methodName, Int is paramCount){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is subM: ml:res;
			if (subM:getBody():length() > 0 && (paramCount < 0 || subM:getParameters():length() == paramCount)) {
				return baseClassName;
			}
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:findMethodImplementingClass(className: baseName, methodName: methodName, paramCount: paramCount);
			}
		});
		return inherited;
	}

	local Function of Member is lookupMethodMember(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return Member:init(kind: "");
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return Member:init(kind: "");
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			return ml:res;
		}
		local Member is inherited: Member:init(kind: "");
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited:getKind() == "") {
				inherited: self:lookupMethodMember(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

	local Function of String is formatCallArguments(String is className, String is methodName, Array of NamedArg is args){
		local Member is m: self:lookupMethodMember(className: className, methodName: methodName);
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		local Array of String is tps: cls:getTypeParams();
		if (m:getKind() == "METHOD") {
			local Array of Parameter is params: m:getParameters();
			if (params:length() > 0) {
				local String is joined: "";
				local Int is pIdx: 0;
				params:each(action: local Function(Parameter is p){
					local String is pName: p:getName();
					local Boolean is matched: false;
					local String is argC: "0";
					args:each(action: local Function(NamedArg is a){
						if (!matched && a:getName() == pName && pName != "") {
							argC: self:generateExpression(expr: a:getValue());
							matched: true;
						}
					});
					if (!matched && pIdx < args:length()) {
						local NamedArg is posArg: args:get(index: pIdx);
						if (posArg:getName() == "") {
							argC: self:generateExpression(expr: posArg:getValue());
							matched: true;
						}
					}
					if (!matched && p:getHasDefault()) {
						argC: self:generateExpression(expr: p:getDefaultExpr());
						matched: true;
					}
					if (tps:indexOf(search: p:getType():getName(), default: -1) >= 0) {
						argC: "(void*)(intptr_t)(" . argC . ")";
					}
					joined: joined . ", " . argC;
					pIdx: pIdx + 1;
				});
				return joined;
			}
		}
		local String is fallbackJoined: "";
		args:each(action: local Function(NamedArg is arg){
			fallbackJoined: fallbackJoined . ", " . self:generateExpression(expr: arg:getValue());
		});
		return fallbackJoined;
	}

	local Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		if (methodName == "init" && self:allClassNames:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName)) {
			return className;
		}
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is foundM: ml:res;
			local String is rawT: self:formatTypeString(t: foundM:getType());
			if (rawT == "" || rawT == "void" || rawT == "Void") {
				return className;
			}
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:lookupMethodReturnType(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

}
