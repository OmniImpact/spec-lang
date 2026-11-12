#! SpecUnit sweep (from arc_destruction_test.spec): ARC field
#! reassignment — the initial field reference, a replaced reference, a
#! direct-constructor ownership transfer, and repeated loop reassignment
#! all resolve to the newest resource with no refcount corruption. The
#! Resource/Container instrumentation objects are preserved verbatim.

Class of SpecUnitTest is TestArcDestruction{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];

	## Initial, replaced, and constructor-transfer field references.
	Function is testFieldReferenceReassignment(){
		local Resource is r1: Resource:init(name: 'First');
		local Container is c: Container:init(res: r1);
		Assert:areEqualString('First', c:getRes():getName());

		local Resource is r2: Resource:init(name: 'Second');
		c:setRes(newRes: r2);
		Assert:areEqualString('Second', c:getRes():getName());

		# Reassignment with a direct constructor call (transfer ownership)
		c:setRes(newRes: Resource:init(name: 'Third'));
		Assert:areEqualString('Third', c:getRes():getName());
	}

	## Repeated loop reassignment must leave the reference on the last
	## assigned resource, with no refcount corruption along the way.
	Function is testLoopReassignmentNoCorruption(){
		local Resource is r1: Resource:init(name: 'First');
		local Container is c: Container:init(res: r1);
		local Int is count: 0;
		while(
			evaluate: local Function of Boolean(){ return count < 5; },
			iteration: local Function(){
				c:setRes(newRes: Resource:init(name: 'Loop_' . count));
				count: count + 1;
			}
		);
		Assert:areEqualString('Loop_4', c:getRes():getName());
	}
}

Class is Resource{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];
	local String is name;

	replace Function is init(String is name){
		self:name: name;
	}

	Function of String is getName(){
		return self:name;
	}
}

Class is Container{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];
	local Resource is res;

	replace Function is init(Resource is res){
		self:res: res;
	}

	Function is setRes(Resource is newRes){
		self:res: newRes;
	}

	Function of Resource is getRes(){
		return self:res;
	}
}
