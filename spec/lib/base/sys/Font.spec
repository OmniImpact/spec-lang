#! Package base:sys
#! Spec-side font layout, glyph spacing, weight boosting, measurement, and rasterization over thin `base:sysinternal:Font` primitives.

Class is Font{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sys', as File()],
		['base', 'struct', Array],
		['base', 'math', Math],
		['base', 'sysinternal', Font]
	];

	held Array of Int is cachedState: Array([-1, 0]);
	held Array of Int is cachedFallbackHandles: Array();

	Int is handle: -1;
	Boolean is ownsHandle: true;
	Float is letterSpacing: 0.045;
	Float is weightBoost: 0.35;
	Int is metricsAddr: 0;
	Int is scratchAddr: 0;
	Int is scratchCap: 0;
	Math is math: Math();
	Array of Font is fallbacks: Array();
	Boolean is fallbacksLoaded: false;
	Boolean is isFallbackFont: false;

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		return if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
	}

	local Function of Int is signI32(Int is v){
		local Int is u: v & 4294967295;
		if({ u >= 2147483648 }, { return u - 4294967296; });
		return u;
	}

	local Function is ensureMetricsBuf(){
		if({ metricsAddr == 0 }, {
			metricsAddr: Mem:alloc(bytes: 16);
		});
	}

	local Function of Int is ensureScratch(Int is needed){
		if({ needed <= 0 }, { return 0; });
		if({ scratchAddr == 0 }, {
			scratchAddr: Mem:alloc(bytes: needed);
			scratchCap: needed;
		}, {
			if({ needed > scratchCap }, {
				scratchAddr: Mem:realloc(ptr: scratchAddr, bytes: needed);
				scratchCap: needed;
			});
		});
		return scratchAddr;
	}

	## Loads a TrueType/OpenType font from raw bytes at ([dataAddr], [byteLen]).
	Function of Boolean is loadMemory(Int is dataAddr, Int is byteLen){
		if({ handle > 0 }, { close(); });
		if({ dataAddr == 0 || byteLen <= 0 }, { return false; });
		handle: base:sysinternal:Font:pal_font_init_memory(data_ptr: dataAddr, data_len: byteLen);
		ownsHandle: true;
		return handle > 0;
	}

	## Loads a TrueType/OpenType font from [path] using `base:sys:File`.
	Function of Boolean is load(String is path){
		local String is bytes: fileRead(
			path: path,
			onSuccess: local Function(String is _s){},
			onError: local Function(Any is _e){},
			default: ''
		);
		if({ bytes:length() == 0 }, { return false; });
		return :loadMemory(dataAddr: :cstrAddr(s: bytes), byteLen: bytes:length());
	}

	## Resolves and loads the OS default sans-serif TrueType font (cached process-wide).
	Function of Boolean is loadDefault(){
		local Int is cached: Font:cachedState:get(index: 0);
		if({ cached > 0 }, {
			if({ handle > 0 && ownsHandle }, {
				base:sysinternal:Font:pal_font_close(handle: handle);
			});
			handle: cached;
			ownsHandle: false;
			return true;
		});
		local Int is pathBuf: Mem:alloc(bytes: 512);
		local Int is pathLen: base:sysinternal:Font:pal_font_default_path(out_buf: pathBuf, out_cap: 512);
		local String is resolved: '';
		if({ pathLen > 0 }, {
			resolved: Mem:strFromBytes(srcAddr: pathBuf, len: pathLen);
		});
		Mem:free(ptr: pathBuf);
		if({ resolved != '' && :load(path: resolved) }, {
			Font:cachedState:set(index: 0, item: handle);
			ownsHandle: false;
			return true;
		});
		local Array of String is fallbacksList: Array([
			'/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
			'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
			'/usr/share/fonts/TTF/DejaVuSans.ttf',
			'/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
			'/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf'
		]);
		local Int is i: 0;
		while({ i < fallbacksList:length() }, {
			local String is p: fallbacksList:get(index: i);
			if({ fileExists(path: p) && :load(path: p) }, {
				Font:cachedState:set(index: 0, item: handle);
				ownsHandle: false;
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## Decodes one UTF-8 codepoint starting at byte [idx] of [text] and advances [outNext] via return.
	local Function of Int is utf8CodeAt(String is text, Int is idx, Int is len){
		local Int is c0: text:byteAt(index: idx) & 255;
		if({ c0 < 128 }, { return c0; });
		if({ (c0 & 224) == 192 && idx + 1 < len }, {
			local Int is c1: text:byteAt(index: idx + 1) & 255;
			return ((c0 & 31) << 6) | (c1 & 63);
		});
		if({ (c0 & 240) == 224 && idx + 2 < len }, {
			local Int is c1: text:byteAt(index: idx + 1) & 255;
			local Int is c2: text:byteAt(index: idx + 2) & 255;
			return ((c0 & 15) << 12) | ((c1 & 63) << 6) | (c2 & 63);
		});
		if({ (c0 & 248) == 240 && idx + 3 < len }, {
			local Int is c1: text:byteAt(index: idx + 1) & 255;
			local Int is c2: text:byteAt(index: idx + 2) & 255;
			local Int is c3: text:byteAt(index: idx + 3) & 255;
			return ((c0 & 7) << 18) | ((c1 & 63) << 12) | ((c2 & 63) << 6) | (c3 & 63);
		});
		return c0;
	}

	local Function of Int is utf8Step(String is text, Int is idx, Int is len){
		local Int is c0: text:byteAt(index: idx) & 255;
		if({ c0 < 128 }, { return 1; });
		if({ (c0 & 224) == 192 && idx + 1 < len }, { return 2; });
		if({ (c0 & 240) == 224 && idx + 2 < len }, { return 3; });
		if({ (c0 & 248) == 240 && idx + 3 < len }, { return 4; });
		return 1;
	}

	## Returns `true` if this font contains a non-`.notdef` glyph for Unicode codepoint [cp].
	Function of Boolean is hasGlyph(Int is cp){
		if({ handle <= 0 }, { return false; });
		return base:sysinternal:Font:pal_font_has_glyph(handle: handle, cp: cp) != 0;
	}

	## Registers an additional fallback [font] used when a codepoint is missing from this font.
	Function is addFallback(Font is font){
		font:isFallbackFont: true;
		fallbacks:add(item: font);
	}

	local Function is ensureFallbacks(){
		if({ isFallbackFont }, { return; });
		if({ Font:cachedState:get(index: 1) != 0 }, {
			fallbacksLoaded: true;
			return;
		});
		Font:cachedState:set(index: 1, item: 1);
		fallbacksLoaded: true;
		local Array of String is paths: Array([
			'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
			'/usr/share/fonts/TTF/DejaVuSans.ttf',
			'/usr/share/fonts/truetype/noto/NotoSansSymbols-Regular.ttf',
			'/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf',
			'/usr/share/fonts/truetype/noto/NotoSansMath-Regular.ttf',
			'/usr/share/fonts/truetype/freefont/FreeSans.ttf'
		]);
		local Int is i: 0;
		while({ i < paths:length() }, {
			local String is p: paths:get(index: i);
			if({ fileExists(path: p) }, {
				local String is bytes: fileRead(
					path: p,
					onSuccess: local Function(String is _s){},
					onError: local Function(Any is _e){},
					default: ''
				);
				if({ bytes:length() > 0 }, {
					local Int is fh: base:sysinternal:Font:pal_font_init_memory(data_ptr: :cstrAddr(s: bytes), data_len: bytes:length());
					if({ fh > 0 }, {
						Font:cachedFallbackHandles:add(item: fh);
					});
				});
			});
			i: i + 1;
		});
	}

	local Function of Int is resolveHandleFor(Int is cp){
		if({ cp < 128 || :hasGlyph(cp: cp) }, { return handle; });
		local Int is i: 0;
		while({ i < fallbacks:length() }, {
			local Font is fb: fallbacks:get(index: i);
			if({ fb:hasGlyph(cp: cp) }, {
				return fb:handle;
			});
			i: i + 1;
		});
		:ensureFallbacks();
		i: 0;
		while({ i < Font:cachedFallbackHandles:length() }, {
			local Int is fh: Font:cachedFallbackHandles:get(index: i);
			if({ base:sysinternal:Font:pal_font_has_glyph(handle: fh, cp: cp) != 0 }, {
				return fh;
			});
			i: i + 1;
		});
		return handle;
	}

	## Measures the horizontal pixel advance of UTF-8 [text] at [pixelHeight].
	Function of Int is measureWidth(String is text, Int is pixelHeight: 16, Float is spacing: -1.0){
		if({ handle <= 0 || pixelHeight <= 0 || text == '' }, { return 0; });
		:ensureMetricsBuf();
		local Float is baseScale: base:sysinternal:Font:pal_font_scale(handle: handle, pixel_height: pixelHeight);
		local Float is sp: if({ spacing >= 0.0 }, { spacing }, { letterSpacing });
		local Float is tracking: math:toFloat(value: pixelHeight) * sp;
		local Float is xpos: 0.0;
		local Int is len: text:length();
		local Int is idx: 0;
		local Int is prevCp: 0;
		local Int is prevH: 0;
		while({ idx < len }, {
			local Int is cp: :utf8CodeAt(text: text, idx: idx, len: len);
			idx: idx + :utf8Step(text: text, idx: idx, len: len);
			local Int is gh: :resolveHandleFor(cp: cp);
			local Float is gScale: if({ gh == handle }, { baseScale }, { base:sysinternal:Font:pal_font_scale(handle: gh, pixel_height: pixelHeight) });
			if({ prevCp != 0 && prevH == gh }, {
				local Int is kern: base:sysinternal:Font:pal_font_kern_advance(handle: gh, cp1: prevCp, cp2: cp);
				xpos: xpos + math:toFloat(value: kern) * gScale;
			});
			base:sysinternal:Font:pal_font_hmetrics(handle: gh, cp: cp, out_2_i32_ptr: metricsAddr);
			local Int is adv: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 0));
			xpos: xpos + math:toFloat(value: adv) * gScale + tracking;
			prevCp: cp;
			prevH: gh;
		});
		return math:toInt(value: math:round(value: xpos));
	}

	## Releases the underlying font handle (if owned), custom fallback fonts, and cached scratch buffers.
	Function is close(){
		local Int is i: 0;
		while({ i < fallbacks:length() }, {
			fallbacks:get(index: i):close();
			i: i + 1;
		});
		fallbacks: Array();
		fallbacksLoaded: false;
		if({ handle > 0 }, {
			if({ ownsHandle }, {
				base:sysinternal:Font:pal_font_close(handle: handle);
			});
			handle: -1;
			ownsHandle: true;
		});
		if({ metricsAddr != 0 }, {
			Mem:free(ptr: metricsAddr);
			metricsAddr: 0;
		});
		if({ scratchAddr != 0 }, {
			Mem:free(ptr: scratchAddr);
			scratchAddr: 0;
			scratchCap: 0;
		});
	}

	Function is destroy(){
		:close();
	}

	## Alpha-blends UTF-8 [text] at ([x], [y]) into an ARGB8888 buffer at [pixelsAddr].
	Function of Boolean is drawText(
		Int is pixelsAddr,
		Int is bufW,
		Int is bufH,
		Int is x,
		Int is y,
		String is text,
		Int is pixelHeight: 16,
		Int is argbColor: -1,
		Float is spacing: -1.0,
		Float is weight: -1.0
	){
		if({ handle <= 0 || pixelsAddr == 0 || bufW <= 0 || bufH <= 0 || pixelHeight <= 0 || text == '' }, {
			return false;
		});
		:ensureMetricsBuf();
		local Float is scale: base:sysinternal:Font:pal_font_scale(handle: handle, pixel_height: pixelHeight);
		base:sysinternal:Font:pal_font_vmetrics(handle: handle, out_3_i32_ptr: metricsAddr);
		local Int is ascent: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 0));
		local Int is descent: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 4));
		local Int is lineGap: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 8));

		local Int is baseline: y + math:toInt(value: math:round(value: math:toFloat(value: ascent) * scale));
		local Int is lineStep: math:toInt(value: math:round(value: math:toFloat(value: ascent - descent + lineGap) * scale));
		local Float is sp: if({ spacing >= 0.0 }, { spacing }, { letterSpacing });
		local Float is wb: if({ weight >= 0.0 }, { weight }, { weightBoost });
		local Float is tracking: math:toFloat(value: pixelHeight) * sp;
		local Float is xpos: math:toFloat(value: x);

		local Int is fgA: (argbColor >> 24) & 255;
		if({ fgA == 0 }, { fgA: 255; });
		local Int is fgR: (argbColor >> 16) & 255;
		local Int is fgG: (argbColor >> 8) & 255;
		local Int is fgB: argbColor & 255;
		local Int is boostNum: math:toInt(value: math:round(value: wb * 256.0));
		if({ boostNum < 0 }, { boostNum: 0; });

		local Int is len: text:length();
		local Int is idx: 0;
		local Int is prevCp: 0;
		local Int is prevH: 0;
		while({ idx < len }, {
			local Int is cp: :utf8CodeAt(text: text, idx: idx, len: len);
			idx: idx + :utf8Step(text: text, idx: idx, len: len);
			if({ cp == 10 }, {
				xpos: math:toFloat(value: x);
				baseline: baseline + lineStep;
				prevCp: 0;
				prevH: 0;
			}, {
				local Int is gHandle: :resolveHandleFor(cp: cp);
				local Float is gScale: if({ gHandle == handle }, { scale }, { base:sysinternal:Font:pal_font_scale(handle: gHandle, pixel_height: pixelHeight) });
				if({ prevCp != 0 && prevH == gHandle }, {
					local Int is kern: base:sysinternal:Font:pal_font_kern_advance(handle: gHandle, cp1: prevCp, cp2: cp);
					xpos: xpos + math:toFloat(value: kern) * gScale;
				});
				base:sysinternal:Font:pal_font_hmetrics(handle: gHandle, cp: cp, out_2_i32_ptr: metricsAddr);
				local Int is adv: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 0));

				base:sysinternal:Font:pal_font_glyph_box(handle: gHandle, cp: cp, pixel_height: pixelHeight, out_4_i32_ptr: metricsAddr);
				local Int is x0: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 0));
				local Int is y0: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 4));
				local Int is x1: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 8));
				local Int is y1: :signI32(v: Mem:loadI32(ptr: metricsAddr, byteOffset: 12));
				local Int is gw: x1 - x0;
				local Int is gh: y1 - y0;

				if({ gw > 0 && gh > 0 }, {
					local Int is buf: :ensureScratch(needed: gw * gh);
					if({ buf != 0 }, {
						base:sysinternal:Font:pal_font_rasterize_glyph(
							handle: gHandle,
							cp: cp,
							pixel_height: pixelHeight,
							dst_ptr: buf,
							gw: gw,
							gh: gh
						);
						local Int is dstX0: math:toInt(value: math:floor(value: xpos)) + x0;
						local Int is dstY0: baseline + y0;
						local Int is gy: 0;
						while({ gy < gh }, {
							local Int is py: dstY0 + gy;
							if({ py >= 0 && py < bufH }, {
								local Int is rowBase: py * bufW;
								local Int is gRowBase: gy * gw;
								local Int is gx: 0;
								while({ gx < gw }, {
									local Int is px: dstX0 + gx;
									if({ px >= 0 && px < bufW }, {
										local Int is cov: Mem:loadByte(ptr: buf, byteOffset: gRowBase + gx) & 255;
										if({ cov > 0 }, {
											if({ boostNum > 0 }, {
												cov: cov + ((cov * (255 - cov) * boostNum) >> 16);
												if({ cov > 255 }, { cov: 255; });
											});
											local Int is a: (cov * fgA) / 255;
											local Int is invA: 255 - a;
											local Int is pOff: (rowBase + px) * 4;
											local Int is bg: Mem:loadI32(ptr: pixelsAddr, byteOffset: pOff);
											local Int is bgA: (bg >> 24) & 255;
											local Int is bgR: (bg >> 16) & 255;
											local Int is bgG: (bg >> 8) & 255;
											local Int is bgB: bg & 255;
											local Int is outA: a + (bgA * invA) / 255;
											local Int is r: (fgR * a + bgR * invA) / 255;
											local Int is g: (fgG * a + bgG * invA) / 255;
											local Int is b: (fgB * a + bgB * invA) / 255;
											Mem:storeI32(ptr: pixelsAddr, byteOffset: pOff, val: (outA << 24) | (r << 16) | (g << 8) | b);
										});
									});
									gx: gx + 1;
								});
							});
							gy: gy + 1;
						});
					});
				});

				xpos: xpos + math:toFloat(value: adv) * gScale + tracking;
				prevCp: cp;
				prevH: gHandle;
			});
		});
		return true;
	}

	## True when a font is loaded and ready for measurement and rendering.
	Function of Boolean is isLoaded(){
		return handle > 0;
	}

	## Returns the last font loading/rasterization error message.
	Function of String is lastError(){
		local Int is cstr: base:sysinternal:Font:pal_font_last_error();
		if({ cstr == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}
}
