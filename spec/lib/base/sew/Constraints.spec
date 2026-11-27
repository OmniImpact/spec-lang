#! Package base:sew
#! Min/max layout constraints passed down during the Sew measure pass.

Class is Constraints{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];

	Int is minW: 0;
	Int is maxW: 0;
	Int is minH: 0;
	Int is maxH: 0;

	replace Function is init(Int is minW: 0, Int is maxW: 0, Int is minH: 0, Int is maxH: 0){
		:minW: minW;
		:maxW: maxW;
		:minH: minH;
		:maxH: maxH;
	}

	Function of Boolean is isBoundedW(){
		return maxW > 0 && maxW < 500000;
	}

	Function of Boolean is isBoundedH(){
		return maxH > 0 && maxH < 500000;
	}

	Function of Int is clampW(Int is w){
		if({ w < minW }, { return minW; });
		if({ maxW > 0 && w > maxW }, { return maxW; });
		return w;
	}

	Function of Int is clampH(Int is h){
		if({ h < minH }, { return minH; });
		if({ maxH > 0 && h > maxH }, { return maxH; });
		return h;
	}

	Function of Constraints is deflate(Int is dw, Int is dh){
		local Int is nMinW: if({ minW > dw }, { minW - dw }, { 0 });
		local Int is nMaxW: if({ maxW > dw }, { maxW - dw }, { 0 });
		local Int is nMinH: if({ minH > dh }, { minH - dh }, { 0 });
		local Int is nMaxH: if({ maxH > dh }, { maxH - dh }, { 0 });
		return Constraints(minW: nMinW, maxW: nMaxW, minH: nMinH, maxH: nMaxH);
	}
}
