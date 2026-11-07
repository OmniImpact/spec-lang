Class is Resource{

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'iterator', as While()]
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
		['base', 'io', as Output()],
		['base', 'iterator', as While()]
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

Class is ArcDestructionTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'iterator', as While()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== ARC Destruction Test ===');

		local Resource is r1: Resource:init(name: 'First');
		local Container is c: Container:init(res: r1);

		if (c:getRes():getName() == 'First') {
			Output:line('[PASS] initial field reference verified');
		} else {
			Output:line('[FAIL] initial field reference mismatch');
		}

		local Resource is r2: Resource:init(name: 'Second');
		c:setRes(newRes: r2);

		if (c:getRes():getName() == 'Second') {
			Output:line('[PASS] reassigned field reference verified');
		} else {
			Output:line('[FAIL] reassigned field reference mismatch');
		}

		# Case 3: Reassignment with a direct constructor call (transfer ownership)
		c:setRes(newRes: Resource:init(name: 'Third'));
		if (c:getRes():getName() == 'Third') {
			Output:line('[PASS] transfer field assignment verified');
		} else {
			Output:line('[FAIL] transfer field assignment mismatch');
		}

		# Case 4: Multiple loop reassignment ensuring no refcount corruptions
		local Int is count: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return count < 5; },
			iteration: local Function(){
				c:setRes(newRes: Resource:init(name: 'Loop_' . count));
				count: count + 1;
			}
		);
		if (c:getRes():getName() == 'Loop_4') {
			Output:line('[PASS] loop repeated field assignment verified');
		} else {
			Output:line('[FAIL] loop repeated field assignment mismatch');
		}

		Output:line('=== End ARC Destruction Test ===');
	}
}
