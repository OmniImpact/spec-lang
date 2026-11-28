#! Package base:struct
#! General-purpose N-ary tree node (`TreeNode of T`) with cycle-guarded child management
#! and non-owning parent references (no ARC retain cycles).

Class is TreeNode of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	T is value;
	local Array of TreeNode of T is children: Array();
	local Int is parentAddr: 0;

	replace Function is init(T is value){
		:value: value;
		:children: Array();
		:parentAddr: 0;
	}

	Function of T is getValue(){ :value }

	Function is setValue(T is value){
		:value: value;
	}

	Function of Int is childCount(){ :children:length() }

	Function of Boolean is isLeaf(){ :children:length() == 0 }

	Function of Boolean is isRoot(){ :parentAddr == 0 }

	Function of Boolean is hasParent(){ :parentAddr != 0 }

	Function of Int is parentAddress(){ :parentAddr }

	Function is clearParent(){
		:parentAddr: 0;
	}

	Function is setParentAddress(Int is addr){
		:parentAddr: addr;
	}

	Function of TreeNode of T is childAt(Int is index, TreeNode of T is default){
		return :children:get(index: index, default: default);
	}

	Function of Array of TreeNode of T is getChildren(){
		return :children;
	}

	local Function of Boolean is wouldCycle(TreeNode of T is candidate){
		local Int is candAddr: Mem:objToAddr(obj: candidate);
		if({ candAddr == 0 }, { return true; });
		local Int is selfAddr: Mem:objToAddr(obj: :);
		if({ candAddr == selfAddr }, { return true; });
		local Map of Int to Boolean is visited: Map();
		local Int is curAddr: :parentAddr;
		while({ curAddr != 0 }, {
			if({ curAddr == candAddr }, { return true; });
			if({ visited:get(key: curAddr, default: false) }, { return true; });
			visited:set(key: curAddr, value: true);
			local TreeNode of T is curNode: Mem:addrToObj(addr: curAddr) as TreeNode;
			curAddr: curNode:parentAddress();
		});
		return false;
	}

	## Attaches [child] to this node if doing so does not introduce a cycle.
	## Detaches [child] from its previous parent if already attached elsewhere.
	Function of Boolean is addChild(TreeNode of T is child){
		if({ :wouldCycle(candidate: child) }, { return false; });
		local Int is prevParentAddr: child:parentAddress();
		local Int is selfAddr: Mem:objToAddr(obj: :);
		if({ prevParentAddr == selfAddr }, { return false; });
		if({ prevParentAddr != 0 }, {
			local TreeNode of T is prevParent: Mem:addrToObj(addr: prevParentAddr) as TreeNode;
			prevParent:removeChild(child: child);
		});
		child:setParentAddress(addr: selfAddr);
		:children:add(item: child);
		return true;
	}

	## Removes [child] from this node's children; returns `true` if found.
	Function of Boolean is removeChild(TreeNode of T is child){
		local Int is targetAddr: Mem:objToAddr(obj: child);
		local Int is i: 0;
		while({ i < :children:length() }, {
			local TreeNode of T is cur: :children:get(index: i, default: child);
			if({ Mem:objToAddr(obj: cur) == targetAddr }, {
				cur:clearParent();
				:children:removeAt(index: i, default: child);
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## Removes the child at [index]; returns `true` if [index] was valid.
	Function of Boolean is removeChildAt(Int is index){
		if({ index < 0 || index >= :children:length() }, { return false; });
		local TreeNode of T is cur: :children:get(index: index, default: :);
		cur:clearParent();
		:children:removeAt(index: index, default: :);
		return true;
	}
}
