#! Package base:cleo
#! Target width specification for Cleo surfaces (percent, pixels, or columns).

Class is CleoWidth{
	replace [String] is namespace: ['base', 'cleo'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];

	Int is kind: 0;
	Int is value: 100;
	Int is cellPxFallback: 8;

	replace Function is init(){
	}

	Function of CleoWidth is percent(Int is pct){
		local CleoWidth is w: CleoWidth:init();
		w:kind: 0;
		w:value: pct;
		return w;
	}

	Function of CleoWidth is px(Int is pixels, Int is cellPx: 8){
		local CleoWidth is w: CleoWidth:init();
		w:kind: 1;
		w:value: pixels;
		w:cellPxFallback: if({ cellPx > 0 }, { cellPx }, { 8 });
		return w;
	}

	Function of CleoWidth is cols(Int is count){
		local CleoWidth is w: CleoWidth:init();
		w:kind: 2;
		w:value: count;
		return w;
	}

	Function of Int is resolve(Int is termWidth, Int is minCols: 20, Int is maxCols: 0){
		local Int is tw: if({ termWidth > 0 }, { termWidth }, { 78 });
		local Int is target: tw;
		if({ :kind == 0 }, {
			local Int is pct: :value;
			if({ pct < 1 }, { pct: 1; });
			if({ pct > 100 }, { pct: 100; });
			target: (tw * pct) / 100;
		});
		if({ :kind == 1 }, {
			target: :value / :cellPxFallback;
		});
		if({ :kind == 2 }, {
			target: :value;
		});
		if({ maxCols > 0 && target > maxCols }, { target: maxCols; });
		if({ target > tw }, { target: tw; });
		if({ target < minCols }, {
			target: if({ tw < minCols }, { tw }, { minCols });
		});
		return target;
	}
}
