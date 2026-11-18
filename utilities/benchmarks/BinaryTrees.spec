#! Binary-trees benchmark (Benchmarks Game style) — Spec implementation.
#!
#! Allocates, traverses, and drops binary trees of increasing depth across
#! optional thread fan-out, exercising ARC object allocation/deallocation and
#! recursive traversal.
#!
#! Usage: binary_trees [threads] [max_depth]
#! Output: checksum=<N> threads=<T> depth=<D> ms=<ms> rate=<nodes/sec>

Class is BinaryTrees{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Parallel()]
	];

	replace Function is init(Map of String to String is args){
		local Array of String is argv: rawArgs();
		local Int is threads: 1;
		local Int is maxDepth: 18;
		if({ argv:length() > 0 }, {
			threads: argv:get(index: 0, default: '1'):parseInt(base: 10, default: 1);
		});
		if({ argv:length() > 1 }, {
			maxDepth: argv:get(index: 1, default: '18'):parseInt(base: 10, default: 18);
		});
		if({ threads < 1 }, { threads: 1; });
		local Int is minDepth: 4;
		if({ maxDepth < minDepth + 2 }, { maxDepth: minDepth + 2; });

		local Int is t0: clockMs();
		local Int is totalChecks: 0;

		local Int is stretchDepth: maxDepth + 1;
		local TreeNode is stretchTree: :makeTree(depth: stretchDepth);
		totalChecks: totalChecks + :checkTree(node: stretchTree);

		local TreeNode is longLived: :makeTree(depth: maxDepth);

		local Int is d: minDepth;
		while({ d <= maxDepth }, {
			local Int is iterations: 1 << (maxDepth - d + minDepth);
			local Int is depthSum: 0;
			if({ threads <= 1 }, {
				local Int is i: 0;
				while({ i < iterations }, {
					local TreeNode is t: :makeTree(depth: d);
					depthSum: depthSum + :checkTree(node: t);
					i++;
				});
			}, {
				atomicPut(slot: 0, value: 0);
				local Int is depthVal: d;
				Parallel:run(threads: threads, iterations: iterations, worker: local Function(Int is start, Int is count){
					local Int is localSum: 0;
					local Int is k: 0;
					while({ k < count }, {
						local TreeNode is t: :makeTree(depth: depthVal);
						localSum: localSum + :checkTree(node: t);
						k++;
					});
					atomicAdd(slot: 0, value: localSum);
				});
				depthSum: atomicGet(slot: 0);
			});
			totalChecks: totalChecks + depthSum;
			d: d + 2;
		});

		totalChecks: totalChecks + :checkTree(node: longLived);

		local Int is ms: clockMs() - t0;
		if({ ms < 1 }, { ms: 1; });
		local Float is rate: (totalChecks as Float) / ((ms as Float) / 1000.0);
		line('checksum=' . totalChecks . ' threads=' . threads . ' depth=' . maxDepth . ' ms=' . ms . ' rate=' . rate);
	}

	Function of TreeNode is makeTree(Int is depth){
		if({ depth <= 0 }, {
			return TreeNode:init();
		});
		return TreeNode:init(left: :makeTree(depth: depth - 1), right: :makeTree(depth: depth - 1));
	}

	Function of Int is checkTree(TreeNode is node){
		if({ node:hasChildren }, {
			return 1 + :checkTree(node: node:left) + :checkTree(node: node:right);
		});
		return 1;
	}
}

Class is TreeNode{

	Boolean is hasChildren: false;
	TreeNode is left;
	TreeNode is right;

	replace Function is init(){
		:hasChildren: false;
	}

	Function is init(TreeNode is left, TreeNode is right){
		:hasChildren: true;
		:left: left;
		:right: right;
	}
}
