#! Package base:fabric:svg
#! Basic SVG parser and 4x4 subpixel supersampled rasterizer with smart size-keyed caching.

Class is SvgRenderer{
	replace [String] is namespace: ['base', 'fabric', 'svg'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'math', as Math()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'data', Xml],
		['base', 'data', XmlNode],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgShape],
		['base', 'fabric', 'svg', SvgDoc],
		['base', 'fabric', 'svg', SvgBitmap]
	];

	held SvgRenderer is shared: SvgRenderer();

	Map of String to SvgDoc is docCache: Map:init();
	Map of String to SvgBitmap is bitmapCache: Map:init();

	replace Function is init(){
		:docCache: Map:init();
		:bitmapCache: Map:init();
	}

	local Function of Float is parseFloatStr(String is s, Float is def: 0.0){
		local String is t: s:trim();
		if({ t == '' }, { return def; });
		local Int is len: t:length();
		local Int is i: 0;
		local Boolean is neg: false;
		local Int is b0: t:byteAt(index: 0) & 255;
		if({ b0 == 45 }, { neg: true; i: 1; }, { if({ b0 == 43 }, { i: 1; }); });
		local Float is val: 0.0;
		local Boolean is anyDigit: false;
		local Boolean is stopInt: false;
		while({ i < len && !stopInt }, {
			local Int is b: t:byteAt(index: i) & 255;
			if({ b >= 48 && b <= 57 }, {
				val: val * 10.0 + ((b - 48) as Float);
				anyDigit: true;
				i: i + 1;
			}, {
				stopInt: true;
			});
		});
		if({ i < len && (t:byteAt(index: i) & 255) == 46 }, {
			i: i + 1;
			local Float is div: 10.0;
			local Boolean is stopFrac: false;
			while({ i < len && !stopFrac }, {
				local Int is b: t:byteAt(index: i) & 255;
				if({ b >= 48 && b <= 57 }, {
					val: val + (((b - 48) as Float) / div);
					div: div * 10.0;
					anyDigit: true;
					i: i + 1;
				}, {
					stopFrac: true;
				});
			});
		});
		if({ !anyDigit }, { return def; });
		return if({ neg }, { 0.0 - val }, { val });
	}

	local Function of Array of Float is parseNumberList(String is text){
		local Array of Float is out: Array();
		local Int is len: text:length();
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: text:byteAt(index: i) & 255;
			local Boolean is isNumStart: (b >= 48 && b <= 57) || b == 45 || b == 43 || b == 46;
			if({ !isNumStart }, {
				i: i + 1;
			}, {
				local Int is start: i;
				if({ b == 45 || b == 43 }, { i: i + 1; });
				local Boolean is seenDot: (b == 46);
				local Boolean is stopNum: false;
				while({ i < len && !stopNum }, {
					local Int is nb: text:byteAt(index: i) & 255;
					if({ nb >= 48 && nb <= 57 }, {
						i: i + 1;
					}, {
						if({ nb == 46 && !seenDot }, {
							seenDot: true;
							i: i + 1;
						}, {
							stopNum: true;
						});
					});
				});
				local String is tok: text:substring(start: start, end: i);
				if({ tok != '' && tok != '-' && tok != '+' && tok != '.' }, {
					out:add(item: :parseFloatStr(s: tok, def: 0.0));
				});
			});
		});
		return out;
	}

	local Function of Int is hexVal(Int is b){
		if({ b >= 48 && b <= 57 }, { return b - 48; });
		if({ b >= 65 && b <= 70 }, { return b - 55; });
		if({ b >= 97 && b <= 102 }, { return b - 87; });
		return 0;
	}

	local Function of Int is parseColor(String is raw, Int is defColor){
		local String is s: raw:trim():toLower();
		if({ s == '' || s == 'none' }, { return 0; });
		if({ s == 'currentcolor' }, { return defColor; });
		if({ s == 'black' }, { return -16777216; });
		if({ s == 'white' }, { return -1; });
		if({ s:startsWith(prefix: '#') }, {
			if({ s:length() == 4 }, {
				local Int is r: :hexVal(b: s:byteAt(index: 1) & 255);
				local Int is g: :hexVal(b: s:byteAt(index: 2) & 255);
				local Int is bl: :hexVal(b: s:byteAt(index: 3) & 255);
				return (255 << 24) | ((r * 17) << 16) | ((g * 17) << 8) | (bl * 17);
			});
			if({ s:length() == 7 }, {
				local Int is r: :hexVal(b: s:byteAt(index: 1) & 255) * 16 + :hexVal(b: s:byteAt(index: 2) & 255);
				local Int is g: :hexVal(b: s:byteAt(index: 3) & 255) * 16 + :hexVal(b: s:byteAt(index: 4) & 255);
				local Int is bl: :hexVal(b: s:byteAt(index: 5) & 255) * 16 + :hexVal(b: s:byteAt(index: 6) & 255);
				return (255 << 24) | (r << 16) | (g << 8) | bl;
			});
		});
		return defColor;
	}

	local Function is appendStyleFromNode(XmlNode is node, SvgShape is shape){
		local String is fillAttr: node:attr(name: 'fill', default: '');
		local String is strokeAttr: node:attr(name: 'stroke', default: '');
		local String is swAttr: node:attr(name: 'stroke-width', default: '');
		local Int is defCol: -16777216;
		if({ fillAttr == 'none' }, {
			shape:hasFill: false;
		}, {
			if({ fillAttr != '' }, {
				shape:hasFill: true;
				shape:fillColor: :parseColor(raw: fillAttr, defColor: defCol);
			}, {
				if({ strokeAttr == '' }, {
					shape:hasFill: true;
					shape:fillColor: defCol;
				});
			});
		});
		if({ strokeAttr != '' && strokeAttr != 'none' }, {
			shape:hasStroke: true;
			shape:strokeColor: :parseColor(raw: strokeAttr, defColor: defCol);
		});
		if({ swAttr != '' }, {
			local Float is sw: :parseFloatStr(s: swAttr, def: 1.5);
			if({ sw > 0.0 }, { shape:strokeWidth: sw; });
		});
	}

	local Function is parsePathData(String is d, XmlNode is node, Array of SvgShape is shapes){
		local Int is len: d:length();
		local Int is i: 0;
		local Float is curX: 0.0;
		local Float is curY: 0.0;
		local Float is startX: 0.0;
		local Float is startY: 0.0;
		local Array of Float is xs: Array();
		local Array of Float is ys: Array();
		local Int is cmd: 0;

		while({ i < len }, {
			local Int is b: d:byteAt(index: i) & 255;
			local Boolean is isCmd: (b >= 65 && b <= 90) || (b >= 97 && b <= 122);
			if({ isCmd }, {
				cmd: b;
				i: i + 1;
				if({ cmd == 90 || cmd == 122 }, {
					if({ xs:length() > 0 }, {
						local SvgShape is sh: SvgShape(xs: xs, ys: ys, closed: true);
						:appendStyleFromNode(node: node, shape: sh);
						shapes:add(item: sh);
						xs: Array();
						ys: Array();
					});
					curX: startX;
					curY: startY;
				});
			}, {
				local Boolean is isNum: (b >= 48 && b <= 57) || b == 45 || b == 43 || b == 46;
				if({ !isNum }, {
					i: i + 1;
				}, {
					local Int is nStart: i;
					local Boolean is stopArgs: false;
					while({ i < len && !stopArgs }, {
						local Int is nb: d:byteAt(index: i) & 255;
						if({ (nb >= 65 && nb <= 90) || (nb >= 97 && nb <= 122) }, {
							stopArgs: true;
						}, {
							i: i + 1;
						});
					});
					local Array of Float is nums: :parseNumberList(text: d:substring(start: nStart, end: i));
					local Int is ni: 0;
					local Int is nCount: nums:length();
					## M / m
					if({ cmd == 77 || cmd == 109 }, {
						while({ ni + 1 < nCount }, {
							local Float is nx: nums:get(index: ni);
							local Float is ny: nums:get(index: ni + 1);
							if({ cmd == 109 }, { nx: curX + nx; ny: curY + ny; });
							if({ ni == 0 }, {
								if({ xs:length() > 0 }, {
									local SvgShape is prev: SvgShape(xs: xs, ys: ys, closed: false);
									:appendStyleFromNode(node: node, shape: prev);
									shapes:add(item: prev);
									xs: Array();
									ys: Array();
								});
								startX: nx;
								startY: ny;
							});
							curX: nx;
							curY: ny;
							xs:add(item: curX);
							ys:add(item: curY);
							ni: ni + 2;
						});
						if({ cmd == 77 }, { cmd: 76; }, { cmd: 108; });
					}, {
					## L / l
					if({ cmd == 76 || cmd == 108 }, {
						while({ ni + 1 < nCount }, {
							local Float is nx: nums:get(index: ni);
							local Float is ny: nums:get(index: ni + 1);
							if({ cmd == 108 }, { nx: curX + nx; ny: curY + ny; });
							curX: nx;
							curY: ny;
							xs:add(item: curX);
							ys:add(item: curY);
							ni: ni + 2;
						});
					}, {
					## H / h
					if({ cmd == 72 || cmd == 104 }, {
						while({ ni < nCount }, {
							local Float is nx: nums:get(index: ni);
							if({ cmd == 104 }, { nx: curX + nx; });
							curX: nx;
							xs:add(item: curX);
							ys:add(item: curY);
							ni: ni + 1;
						});
					}, {
					## V / v
					if({ cmd == 86 || cmd == 118 }, {
						while({ ni < nCount }, {
							local Float is ny: nums:get(index: ni);
							if({ cmd == 118 }, { ny: curY + ny; });
							curY: ny;
							xs:add(item: curX);
							ys:add(item: curY);
							ni: ni + 1;
						});
					}, {
					## Q / q (quadratic bezier flattened to 6 segments)
					if({ cmd == 81 || cmd == 113 }, {
						while({ ni + 3 < nCount }, {
							local Float is cx1: nums:get(index: ni);
							local Float is cy1: nums:get(index: ni + 1);
							local Float is ex: nums:get(index: ni + 2);
							local Float is ey: nums:get(index: ni + 3);
							if({ cmd == 113 }, { cx1: curX + cx1; cy1: curY + cy1; ex: curX + ex; ey: curY + ey; });
							local Int is seg: 1;
							while({ seg <= 6 }, {
								local Float is t: (seg as Float) / 6.0;
								local Float is u: 1.0 - t;
								local Float is px: u * u * curX + 2.0 * u * t * cx1 + t * t * ex;
								local Float is py: u * u * curY + 2.0 * u * t * cy1 + t * t * ey;
								xs:add(item: px);
								ys:add(item: py);
								seg: seg + 1;
							});
							curX: ex;
							curY: ey;
							ni: ni + 4;
						});
					}, {
					## C / c (cubic bezier flattened to 8 segments)
					if({ cmd == 67 || cmd == 99 }, {
						while({ ni + 5 < nCount }, {
							local Float is c1x: nums:get(index: ni);
							local Float is c1y: nums:get(index: ni + 1);
							local Float is c2x: nums:get(index: ni + 2);
							local Float is c2y: nums:get(index: ni + 3);
							local Float is ex: nums:get(index: ni + 4);
							local Float is ey: nums:get(index: ni + 5);
							if({ cmd == 99 }, {
								c1x: curX + c1x; c1y: curY + c1y;
								c2x: curX + c2x; c2y: curY + c2y;
								ex: curX + ex; ey: curY + ey;
							});
							local Int is seg: 1;
							while({ seg <= 8 }, {
								local Float is t: (seg as Float) / 8.0;
								local Float is u: 1.0 - t;
								local Float is px: u * u * u * curX + 3.0 * u * u * t * c1x + 3.0 * u * t * t * c2x + t * t * t * ex;
								local Float is py: u * u * u * curY + 3.0 * u * u * t * c1y + 3.0 * u * t * t * c2y + t * t * t * ey;
								xs:add(item: px);
								ys:add(item: py);
								seg: seg + 1;
							});
							curX: ex;
							curY: ey;
							ni: ni + 6;
						});
					}); }); }); }); }); });
				});
			});
		});

		if({ xs:length() > 0 }, {
			local SvgShape is rem: SvgShape(xs: xs, ys: ys, closed: false);
			:appendStyleFromNode(node: node, shape: rem);
			shapes:add(item: rem);
		});
	}

	local Function is collectXmlShapes(XmlNode is node, Array of SvgShape is shapes){
		local String is t: node:tag:toLower();
		if({ t == 'path' }, {
			:parsePathData(d: node:attr(name: 'd', default: ''), node: node, shapes: shapes);
		}, {
		if({ t == 'line' }, {
			local Float is x1: :parseFloatStr(s: node:attr(name: 'x1', default: '0'));
			local Float is y1: :parseFloatStr(s: node:attr(name: 'y1', default: '0'));
			local Float is x2: :parseFloatStr(s: node:attr(name: 'x2', default: '0'));
			local Float is y2: :parseFloatStr(s: node:attr(name: 'y2', default: '0'));
			local SvgShape is sh: SvgShape(xs: Array([x1, x2]), ys: Array([y1, y2]), closed: false);
			:appendStyleFromNode(node: node, shape: sh);
			shapes:add(item: sh);
		}, {
		if({ t == 'rect' }, {
			local Float is rx: :parseFloatStr(s: node:attr(name: 'x', default: '0'));
			local Float is ry: :parseFloatStr(s: node:attr(name: 'y', default: '0'));
			local Float is rw: :parseFloatStr(s: node:attr(name: 'width', default: '0'));
			local Float is rh: :parseFloatStr(s: node:attr(name: 'height', default: '0'));
			if({ rw > 0.0 && rh > 0.0 }, {
				local SvgShape is sh: SvgShape(
					xs: Array([rx, rx + rw, rx + rw, rx]),
					ys: Array([ry, ry, ry + rh, ry + rh]),
					closed: true
				);
				:appendStyleFromNode(node: node, shape: sh);
				shapes:add(item: sh);
			});
		}, {
		if({ t == 'polyline' || t == 'polygon' }, {
			local Array of Float is nums: :parseNumberList(text: node:attr(name: 'points', default: ''));
			local Array of Float is pxs: Array();
			local Array of Float is pys: Array();
			local Int is pi: 0;
			while({ pi + 1 < nums:length() }, {
				pxs:add(item: nums:get(index: pi));
				pys:add(item: nums:get(index: pi + 1));
				pi: pi + 2;
			});
			if({ pxs:length() >= 2 }, {
				local SvgShape is sh: SvgShape(xs: pxs, ys: pys, closed: (t == 'polygon'));
				:appendStyleFromNode(node: node, shape: sh);
				shapes:add(item: sh);
			});
		}, {
		if({ t == 'circle' }, {
			local Float is cx: :parseFloatStr(s: node:attr(name: 'cx', default: '0'));
			local Float is cy: :parseFloatStr(s: node:attr(name: 'cy', default: '0'));
			local Float is r: :parseFloatStr(s: node:attr(name: 'r', default: '0'));
			if({ r > 0.0 }, {
				local Array of Float is cxs: Array();
				local Array of Float is cys: Array();
				local Int is segs: 20;
				local Int is si: 0;
				while({ si < segs }, {
					local Float is ang: ((si as Float) * 6.283185307) / (segs as Float);
					cxs:add(item: cx + r * Math:cos(value: ang));
					cys:add(item: cy + r * Math:sin(value: ang));
					si: si + 1;
				});
				local SvgShape is sh: SvgShape(xs: cxs, ys: cys, closed: true);
				:appendStyleFromNode(node: node, shape: sh);
				shapes:add(item: sh);
			});
		}); }); }); }); });

		local Int is ci: 0;
		while({ ci < node:children:length() }, {
			:collectXmlShapes(node: node:children:get(index: ci), shapes: shapes);
			ci: ci + 1;
		});
	}

	Function of SvgDoc is parse(String is svgSrc){
		if({ docCache:has(key: svgSrc) }, {
			return docCache:get(key: svgSrc, default: SvgDoc());
		});
		local XmlNode is root: Xml():parseOrEmpty(input: svgSrc);
		local XmlNode is svgNode: if({ root:tag:toLower() == 'svg' }, { root }, { root:firstByTag(tagName: 'svg') });
		local Float is vx: 0.0;
		local Float is vy: 0.0;
		local Float is vw: 24.0;
		local Float is vh: 24.0;
		local String is vb: svgNode:attr(name: 'viewBox', default: '');
		if({ vb != '' }, {
			local Array of Float is vnums: :parseNumberList(text: vb);
			if({ vnums:length() >= 4 }, {
				vx: vnums:get(index: 0);
				vy: vnums:get(index: 1);
				vw: vnums:get(index: 2);
				vh: vnums:get(index: 3);
			});
		}, {
			local Float is aw: :parseFloatStr(s: svgNode:attr(name: 'width', default: '24'), def: 24.0);
			local Float is ah: :parseFloatStr(s: svgNode:attr(name: 'height', default: '24'), def: 24.0);
			if({ aw > 0.0 }, { vw: aw; });
			if({ ah > 0.0 }, { vh: ah; });
		});
		if({ vw <= 0.0 }, { vw: 24.0; });
		if({ vh <= 0.0 }, { vh: 24.0; });
		local Array of SvgShape is shapes: Array();
		:collectXmlShapes(node: svgNode, shapes: shapes);
		local SvgDoc is doc: SvgDoc(viewX: vx, viewY: vy, viewW: vw, viewH: vh, shapes: shapes);
		docCache:set(key: svgSrc, value: doc);
		return doc;
	}

	local Function of Boolean is pointInPolygon(Float is px, Float is py, Array of Float is xs, Array of Float is ys){
		local Int is n: xs:length();
		if({ n < 3 }, { return false; });
		local Boolean is inside: false;
		local Int is i: 0;
		local Int is j: n - 1;
		while({ i < n }, {
			local Float is xi: xs:get(index: i);
			local Float is yi: ys:get(index: i);
			local Float is xj: xs:get(index: j);
			local Float is yj: ys:get(index: j);
			if({ (yi > py) != (yj > py) }, {
				local Float is hitX: ((xj - xi) * (py - yi)) / (yj - yi) + xi;
				if({ px < hitX }, { inside: !inside; });
			});
			j: i;
			i: i + 1;
		});
		return inside;
	}

	local Function of Float is distSqToSegment(Float is px, Float is py, Float is ax, Float is ay, Float is bx, Float is by){
		local Float is dx: bx - ax;
		local Float is dy: by - ay;
		local Float is len2: dx * dx + dy * dy;
		if({ len2 <= 0.000001 }, {
			local Float is ex: px - ax;
			local Float is ey: py - ay;
			return ex * ex + ey * ey;
		});
		local Float is t: ((px - ax) * dx + (py - ay) * dy) / len2;
		if({ t < 0.0 }, { t: 0.0; });
		if({ t > 1.0 }, { t: 1.0; });
		local Float is cx: ax + t * dx;
		local Float is cy: ay + t * dy;
		local Float is ex: px - cx;
		local Float is ey: py - cy;
		return ex * ex + ey * ey;
	}

	local Function of Boolean is pointOnStroke(Float is px, Float is py, SvgShape is sh, Float is halfW){
		local Int is n: sh:xs:length();
		if({ n < 2 }, { return false; });
		local Float is r2: halfW * halfW;
		local Int is count: if({ sh:closed }, { n }, { n - 1 });
		local Int is i: 0;
		while({ i < count }, {
			local Int is j: if({ i + 1 < n }, { i + 1 }, { 0 });
			local Float is d2: :distSqToSegment(
				px: px, py: py,
				ax: sh:xs:get(index: i), ay: sh:ys:get(index: i),
				bx: sh:xs:get(index: j), by: sh:ys:get(index: j)
			);
			if({ d2 <= r2 }, { return true; });
			i: i + 1;
		});
		return false;
	}

	Function of SvgBitmap is rasterize(String is svgSrc, Int is widthPx, Int is heightPx){
		if({ widthPx <= 0 || heightPx <= 0 }, { return SvgBitmap(); });
		local String is cacheKey: svgSrc . ':' . (widthPx as String) . 'x' . (heightPx as String);
		if({ bitmapCache:has(key: cacheKey) }, {
			return bitmapCache:get(key: cacheKey, default: SvgBitmap());
		});

		local SvgDoc is doc: :parse(svgSrc: svgSrc);
		local Int is totalPix: widthPx * heightPx;
		local Int is maskAddr: Mem:alloc(bytes: totalPix);
		local Int is argbAddr: Mem:alloc(bytes: totalPix * 4);
		Mem:set(dst: maskAddr, byteVal: 0, bytes: totalPix);
		Mem:set(dst: argbAddr, byteVal: 0, bytes: totalPix * 4);

		local Float is sxScale: doc:viewW / (widthPx as Float);
		local Float is syScale: doc:viewH / (heightPx as Float);
		local Int is py: 0;
		while({ py < heightPx }, {
			local Int is px: 0;
			while({ px < widthPx }, {
				local Int is hits: 0;
				local Int is rSum: 0;
				local Int is gSum: 0;
				local Int is bSum: 0;
				local Int is sy: 0;
				while({ sy < 4 }, {
					local Float is vpy: doc:viewY + (((py as Float) + (((sy as Float) + 0.5) / 4.0)) * syScale);
					local Int is sx: 0;
					while({ sx < 4 }, {
						local Float is vpx: doc:viewX + (((px as Float) + (((sx as Float) + 0.5) / 4.0)) * sxScale);
						local Int is sampleColor: 0;
						local Boolean is hit: false;
						local Int is si: 0;
						while({ si < doc:shapes:length() }, {
							local SvgShape is sh: doc:shapes:get(index: si);
							if({ sh:hasFill && :pointInPolygon(px: vpx, py: vpy, xs: sh:xs, ys: sh:ys) }, {
								hit: true;
								sampleColor: sh:fillColor;
							});
							if({ sh:hasStroke && :pointOnStroke(px: vpx, py: vpy, sh: sh, halfW: sh:strokeWidth * 0.5) }, {
								hit: true;
								sampleColor: sh:strokeColor;
							});
							si: si + 1;
						});
						if({ hit }, {
							hits: hits + 1;
							rSum: rSum + ((sampleColor >> 16) & 255);
							gSum: gSum + ((sampleColor >> 8) & 255);
							bSum: bSum + (sampleColor & 255);
						});
						sx: sx + 1;
					});
					sy: sy + 1;
				});
				if({ hits > 0 }, {
					local Int is cov: (hits * 255) / 16;
					local Int is idx: py * widthPx + px;
					Mem:storeByte(ptr: maskAddr, byteOffset: idx, val: cov);
					local Int is outR: rSum / hits;
					local Int is outG: gSum / hits;
					local Int is outB: bSum / hits;
					Mem:storeI32(ptr: argbAddr, byteOffset: idx * 4, val: (cov << 24) | (outR << 16) | (outG << 8) | outB);
				});
				px: px + 1;
			});
			py: py + 1;
		});

		local SvgBitmap is bmp: SvgBitmap(width: widthPx, height: heightPx, maskAddr: maskAddr, argbAddr: argbAddr);
		bitmapCache:set(key: cacheKey, value: bmp);
		return bmp;
	}

	Function is draw(
		DrawContext is ctx,
		String is svgSrc,
		Int is x,
		Int is y,
		Int is widthPx,
		Int is heightPx,
		Int is tintColor: 0,
		Boolean is useTint: false
	){
		if({ svgSrc == '' || widthPx <= 0 || heightPx <= 0 }, { return; });
		local SvgBitmap is bmp: :rasterize(svgSrc: svgSrc, widthPx: widthPx, heightPx: heightPx);
		if({ useTint }, {
			ctx:blendAlphaMask(x: x, y: y, w: bmp:width, h: bmp:height, maskAddr: bmp:maskAddr, color: tintColor);
		}, {
			ctx:blendArgbBuffer(x: x, y: y, w: bmp:width, h: bmp:height, argbAddr: bmp:argbAddr);
		});
	}
}
