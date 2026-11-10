#! Package base:compiler:checker:loops
#! Resolves a field-access path segment by segment, walking field types
## through the class hierarchy. Stops when the current type is an enum
## (variants are not fields) or a segment resolves to nothing.
#! PLAN-ENUM Stage 1: when the root was a class name, the FIRST segment
## resolves as a held member (the class-name prefix reaches exactly the
## held members); later segments chain as instance fields on its value.

Class of Loop is PathResolveLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'sys', as Conditional()]
	];

	local TypeChecker is tc;
	local Array of String is segs;
	local Int is idx: 1;
	local String is currType: '';

	## Whether the root was a class name and segment 1 resolves as a
	## held member (never for self/local/field roots — an instance
	## reference reaches exactly the instance members).
	local Boolean is resolveHeldFirst: false;

	replace Function is init(TypeChecker is tc, Array of String is segs, String is rootType, Boolean is resolveHeldFirst: false){
		self:tc: tc;
		self:segs: segs;
		self:currType: rootType;
		self:idx: 1;
		self:resolveHeldFirst: resolveHeldFirst;
	}

	replace Function of Boolean is evaluate(){
		return self:currType != '' && self:idx < self:segs:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local String is seg: self:segs:get(index: self:idx);
		self:idx: self:idx + 1;
		Conditional:if(check: { self:tc:allEnumNames:has(key: self:currType) }, then: {
			return true;
		});
		# Segment 1 after a class-name root: the held-member lookup.
		Conditional:if(check: { self:resolveHeldFirst && self:idx == 2 }, then: {
			self:currType: self:tc:lookupHeldFieldType(className: self:currType, fieldName: seg);
			return true;
		});
		self:currType: self:tc:lookupFieldType(className: self:currType, fieldName: seg);
		return true;
	}
}
