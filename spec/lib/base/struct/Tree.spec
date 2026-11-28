#! Package base:struct
#! General-purpose N-ary tree (`Tree of T`) with iterative, cycle-guarded
#! pre-order, post-order, and breadth-first traversals.

Class is Tree of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'struct', TreeNode],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of TreeNode of T is rootSlot: Array();

	replace Function is init(){
		:rootSlot: Array();
	}

	replace Function is init(T is rootValue){
		:rootSlot: Array();
		:rootSlot:add(item: TreeNode(value: rootValue));
	}

	Function of Boolean is isEmpty(){ :rootSlot:length() == 0 }

	Function of TreeNode of T is getRoot(TreeNode of T is default){
		if({ :rootSlot:length() == 0 }, { return default; });
		return :rootSlot:get(index: 0, default: default);
	}

	Function is setRoot(TreeNode of T is node){
		node:clearParent();
		:rootSlot:clear();
		:rootSlot:add(item: node);
	}

	Function is clear(){
		:rootSlot:clear();
	}

	## Iterative pre-order traversal calling `action(node)`.
	Function is eachPreOrder(Function is action){
		if({ :rootSlot:length() == 0 }, { return; });
		local TreeNode of T is rootNode: :rootSlot:get(index: 0, default: :getRoot(default: :rootSlot:get(index: 0)));
		local Array of TreeNode of T is stack: Array();
		local Map of Int to Boolean is visited: Map();
		stack:add(item: rootNode);
		while({ stack:length() > 0 }, {
			local TreeNode of T is cur: stack:pop(default: rootNode);
			local Int is addr: Mem:objToAddr(obj: cur);
			if({ !visited:get(key: addr, default: false) }, {
				visited:set(key: addr, value: true);
				action(cur);
				local Int is cc: cur:childCount();
				local Int is i: cc - 1;
				while({ i >= 0 }, {
					stack:add(item: cur:childAt(index: i, default: cur));
					i: i - 1;
				});
			});
		});
	}

	## Iterative post-order traversal calling `action(node)`.
	Function is eachPostOrder(Function is action){
		if({ :rootSlot:length() == 0 }, { return; });
		local TreeNode of T is rootNode: :rootSlot:get(index: 0, default: :getRoot(default: :rootSlot:get(index: 0)));
		local Array of TreeNode of T is stack: Array();
		local Array of TreeNode of T is order: Array();
		local Map of Int to Boolean is visited: Map();
		stack:add(item: rootNode);
		while({ stack:length() > 0 }, {
			local TreeNode of T is cur: stack:pop(default: rootNode);
			local Int is addr: Mem:objToAddr(obj: cur);
			if({ !visited:get(key: addr, default: false) }, {
				visited:set(key: addr, value: true);
				order:add(item: cur);
				local Int is cc: cur:childCount();
				local Int is i: 0;
				while({ i < cc }, {
					stack:add(item: cur:childAt(index: i, default: cur));
					i: i + 1;
				});
			});
		});
		while({ order:length() > 0 }, {
			action(order:pop(default: rootNode));
		});
	}

	## Iterative breadth-first traversal calling `action(node)`.
	Function is eachBreadthFirst(Function is action){
		if({ :rootSlot:length() == 0 }, { return; });
		local TreeNode of T is rootNode: :rootSlot:get(index: 0, default: :getRoot(default: :rootSlot:get(index: 0)));
		local Array of TreeNode of T is queue: Array();
		local Map of Int to Boolean is visited: Map();
		local Int is head: 0;
		queue:add(item: rootNode);
		while({ head < queue:length() }, {
			local TreeNode of T is cur: queue:get(index: head, default: rootNode);
			head: head + 1;
			local Int is addr: Mem:objToAddr(obj: cur);
			if({ !visited:get(key: addr, default: false) }, {
				visited:set(key: addr, value: true);
				action(cur);
				local Int is cc: cur:childCount();
				local Int is i: 0;
				while({ i < cc }, {
					queue:add(item: cur:childAt(index: i, default: cur));
					i: i + 1;
				});
			});
		});
	}

	## Returns all node values in pre-order.
	Function of Array of T is toArrayPreOrder(){
		local Array of T is out: Array();
		:eachPreOrder(action: local Function(TreeNode of T is n){
			out:add(item: n:getValue());
		});
		return out;
	}

	## Returns all node values in breadth-first order.
	Function of Array of T is toArrayBreadthFirst(){
		local Array of T is out: Array();
		:eachBreadthFirst(action: local Function(TreeNode of T is n){
			out:add(item: n:getValue());
		});
		return out;
	}

	## Returns total number of nodes reachable from the root.
	Function of Int is size(){
		local Int is count: 0;
		:eachPreOrder(action: local Function(TreeNode of T is _n){
			count: count + 1;
		});
		return count;
	}

	## Returns the height of the tree (0 if empty, 1 for root-only).
	Function of Int is height(){
		if({ :rootSlot:length() == 0 }, { return 0; });
		local TreeNode of T is rootNode: :rootSlot:get(index: 0, default: :getRoot(default: :rootSlot:get(index: 0)));
		local Array of TreeNode of T is queue: Array();
		local Map of Int to Boolean is visited: Map();
		local Int is head: 0;
		local Int is levels: 0;
		queue:add(item: rootNode);
		while({ head < queue:length() }, {
			local Int is levelEnd: queue:length();
			local Boolean is anyInLevel: false;
			while({ head < levelEnd }, {
				local TreeNode of T is cur: queue:get(index: head, default: rootNode);
				head: head + 1;
				local Int is addr: Mem:objToAddr(obj: cur);
				if({ !visited:get(key: addr, default: false) }, {
					visited:set(key: addr, value: true);
					anyInLevel: true;
					local Int is cc: cur:childCount();
					local Int is i: 0;
					while({ i < cc }, {
						queue:add(item: cur:childAt(index: i, default: cur));
						i: i + 1;
					});
				});
			});
			if({ anyInLevel }, { levels: levels + 1; });
		});
		return levels;
	}
}
