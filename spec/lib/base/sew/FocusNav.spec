#! Package base:sew
#! Shared keyboard-focus traversal (`Tab`/`Shift+Tab`) and click-focus synchronization helpers.

Class is FocusNav{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode]
	];

	held FocusNav is shared: FocusNav();

	## Advances keyboard focus across [focusables] (forward or [reverse]). Returns `true` if focus moved.
	Function of Boolean is stepTab(Array of SewNode is focusables, Boolean is reverse){
		local Int is n: focusables:length();
		if({ n == 0 }, { return false; });
		local Int is curIdx: -1;
		local Int is i: 0;
		while({ i < n }, {
			if({ focusables:get(index: i):isFocused() }, {
				if({ curIdx < 0 }, { curIdx: i; });
				focusables:get(index: i):setFocused(next: false);
			});
			i: i + 1;
		});
		local Int is nextIdx: 0;
		if({ reverse }, {
			nextIdx: if({ curIdx <= 0 }, { n - 1 }, { curIdx - 1 });
		}, {
			nextIdx: if({ curIdx < 0 || curIdx + 1 >= n }, { 0 }, { curIdx + 1 });
		});
		focusables:get(index: nextIdx):setFocused(next: true);
		return true;
	}

	## Synchronizes focus across [focusables] after a pointer click at ([x], [y]). Returns `true` if any state changed.
	Function of Boolean is syncClick(Array of SewNode is focusables, Int is x, Int is y){
		local Boolean is changed: false;
		local Int is n: focusables:length();
		local Int is i: 0;
		while({ i < n }, {
			local SewNode is node: focusables:get(index: i);
			local Boolean is hit: node:containsPoint(x: x, y: y) || node:blocksPointerAt(x: x, y: y);
			if({ node:isFocused() != hit }, {
				node:setFocused(next: hit);
				changed: true;
			});
			i: i + 1;
		});
		return changed;
	}
}
