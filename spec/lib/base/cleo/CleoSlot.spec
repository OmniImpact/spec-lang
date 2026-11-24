#! Package base:cleo
#! An indexed row/block slot inside a CleoSection.

Class is CleoSlot{
	replace [String] is namespace: ['base', 'cleo'];

	replace [[String]] is using: [
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', as CleoText()],
		['base', 'cleo', CleoImage],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'struct', Array],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()]
	];

	Int is id: 0;
	Int is kind: 0;
	String is text: '';
	String is rightText: '';
	CleoColor is fgColor: CleoColor:default();
	CleoColor is bgColor: CleoColor:default();
	Boolean is bold: false;
	# Wrap (never truncate) overlong text at render time — for error
	# and diagnostic lines where content must not be lost.
	Boolean is wrap: false;

	# Throbber state
	Array of String is frames: Array(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']);
	ThrobberShape is shape: ThrobberShape:DOT;
	ThrobberEffect is effect: ThrobberEffect:BLINK;
	Array of CleoColor is palette: Array();
	Boolean is queued: false;
	Boolean is resolved: false;
	String is badge: '';

	# Two-stage overlaid progress state
	Float is stage1: 0.0;
	Float is stage2: 0.0;
	CleoColor is stage1Color: CleoColor:ansi(code: 252);
	CleoColor is stage2Color: CleoColor:ansi(code: 243);
	CleoColor is trackColor: CleoColor:ansi(code: 236);
	Boolean is showTwoStagePercent: true;

	# Image / multi-line block state
	Boolean is hasImage: false;
	CleoImage is image: CleoImage:init(pixelWidth: 0, pixelHeight: 0);
	Array of String is asciiLines: Array();

	replace Function is init(Int is id, Int is kind){
		:id: id;
		:kind: kind;
	}

	Function of String is shapeOnGlyph(ThrobberShape is sh){
		if({ sh == ThrobberShape:DOT }, { return '●'; });
		if({ sh == ThrobberShape:CIRCLE }, { return '●'; });
		if({ sh == ThrobberShape:CIRCLE_DOT }, { return '◉'; });
		if({ sh == ThrobberShape:DIAMOND }, { return '◆'; });
		if({ sh == ThrobberShape:SQUARE }, { return '■'; });
		if({ sh == ThrobberShape:STAR }, { return '★'; });
		if({ sh == ThrobberShape:TRIANGLE }, { return '▲'; });
		if({ sh == ThrobberShape:ASCII_DOT }, { return '*'; });
		return '●';
	}

	Function of String is shapeOffGlyph(ThrobberShape is sh){
		if({ sh == ThrobberShape:DOT }, { return ' '; });
		if({ sh == ThrobberShape:CIRCLE }, { return '○'; });
		if({ sh == ThrobberShape:CIRCLE_DOT }, { return '○'; });
		if({ sh == ThrobberShape:DIAMOND }, { return '◇'; });
		if({ sh == ThrobberShape:SQUARE }, { return '□'; });
		if({ sh == ThrobberShape:STAR }, { return '☆'; });
		if({ sh == ThrobberShape:TRIANGLE }, { return '△'; });
		if({ sh == ThrobberShape:ASCII_DOT }, { return ' '; });
		return ' ';
	}

	Function of String is effectivePrefix(Int is tick, CleoColor is fallbackFg){
		if({ :kind != 1 && :kind != 2 }, {
			return '';
		});
		if({ :resolved }, {
			local CleoColor is c: if({ :fgColor:isSet() }, { :fgColor }, { fallbackFg });
			return c:fgSeq() . :badge . Ansi:reset() . ' ';
		});
		if({ :queued }, {
			local CleoColor is c: if({ :fgColor:isSet() }, { :fgColor }, { fallbackFg });
			return c:fgSeq() . :shapeOffGlyph(sh: :shape) . Ansi:reset() . ' ';
		});
		if({ :kind == 1 }, {
			local Int is n: :frames:length();
			local String is f: if({ n > 0 }, { :frames:get(index: tick % n, default: '*') }, { '*' });
			local CleoColor is c: if({ :fgColor:isSet() }, { :fgColor }, { fallbackFg });
			return c:fgSeq() . f . Ansi:reset() . ' ';
		});
		# Shape throbber
		local String is glyph: :shapeOnGlyph(sh: :shape);
		if({ :effect == ThrobberEffect:BLINK || :effect == ThrobberEffect:BLINK_AND_COLOR }, {
			if({ (tick % 2) == 1 }, {
				glyph: :shapeOffGlyph(sh: :shape);
			});
		});
		local CleoColor is activeColor: if({ :fgColor:isSet() }, { :fgColor }, { fallbackFg });
		if({ (:effect == ThrobberEffect:COLOR_CYCLE || :effect == ThrobberEffect:BLINK_AND_COLOR) && :palette:length() > 0 }, {
			activeColor: :palette:get(index: tick % :palette:length(), default: activeColor);
		});
		return activeColor:fgSeq() . glyph . Ansi:reset() . ' ';
	}

	Function of String is styleLine(String is raw, Int is innerW, CleoColor is secFg, CleoColor is secBg){
		local CleoColor is effFg: if({ :fgColor:isSet() }, { :fgColor }, { secFg });
		local CleoColor is effBg: if({ :bgColor:isSet() }, { :bgColor }, { secBg });
		local String is padded: CleoText:padRight(text: raw, width: innerW);
		local String is prefix: '';
		if({ effBg:isSet() }, { prefix: prefix . effBg:bgSeq(); });
		if({ effFg:isSet() }, { prefix: prefix . effFg:fgSeq(); });
		if({ :bold }, { prefix: prefix . Ansi:bold(); });
		if({ prefix == '' }, {
			return padded;
		});
		# Re-apply section/slot bg after any inner ANSI reset so full row background stays intact
		local String is patched: padded:replaceAll(search: Ansi:reset(), replacement: Ansi:reset() . prefix);
		return prefix . patched . Ansi:reset();
	}

	Function of String is formatRowWithRight(String is leftPart, String is rightPart, Int is innerW){
		if({ rightPart == '' }, {
			return leftPart;
		});
		local Int is rw: CleoText:displayWidth(text: rightPart);
		local Int is lw: CleoText:displayWidth(text: leftPart);
		if({ lw + 1 + rw <= innerW }, {
			return leftPart . CleoText:repeatStr(s: ' ', count: innerW - lw - rw) . rightPart;
		});
		local Int is avail: innerW - rw - 1;
		if({ avail > 0 }, {
			return CleoText:padRight(text: leftPart, width: avail) . ' ' . rightPart;
		});
		return leftPart;
	}

	Function of Array of String is renderInnerLines(Int is innerW, CleoColor is secFg, CleoColor is secBg, Int is tick){
		local Array of String is out: Array();
		if({ :kind == 0 || :kind == 1 || :kind == 2 }, {
			local String is pfx: :effectivePrefix(tick: tick, fallbackFg: secFg);
			if(check: { :wrap && :rightText == '' && pfx == '' }, then: {
				local Array of String is wrapped: CleoText:wrap(text: :text, maxCols: innerW);
				local Int is wi: 0;
				while({ wi < wrapped:length() }, {
					out:add(item: :styleLine(raw: wrapped:get(index: wi, default: ''), innerW: innerW, secFg: secFg, secBg: secBg));
					wi++;
				});
				return out;
			});
			local String is combined: :formatRowWithRight(leftPart: pfx . :text, rightPart: :rightText, innerW: innerW);
			out:add(item: :styleLine(raw: combined, innerW: innerW, secFg: secFg, secBg: secBg));
			return out;
		});
		if({ :kind == 3 }, {
			# Progress Area: text block + two-stage overlaid bar
			if({ :text != '' }, {
				local String is header: :formatRowWithRight(leftPart: :text, rightPart: :rightText, innerW: innerW);
				out:add(item: :styleLine(raw: header, innerW: innerW, secFg: secFg, secBg: secBg));
			});
			local Float is s1: :stage1;
			if({ s1 < 0.0 }, { s1: 0.0; });
			if({ s1 > 1.0 }, { s1: 1.0; });
			local Float is s2: :stage2;
			if({ s2 < s1 }, { s2: s1; });
			if({ s2 > 1.0 }, { s2: 1.0; });

			local Int is p1: ((s1 * 100.0) + 0.5) as Int;
			local Int is p2: ((s2 * 100.0) + 0.5) as Int;
			local String is pctLabel: '';
			if({ :showTwoStagePercent }, {
				pctLabel: '  ' . (p1 as String) . '% (' . (p2 as String) . '%)';
			});
			if({ !:showTwoStagePercent }, {
				pctLabel: '  ' . (p1 as String) . '%';
			});
			local Int is labelW: CleoText:displayWidth(text: pctLabel);
			local Int is barW: innerW - labelW;
			if({ barW < 4 }, { barW: 4; });

			local Int is c1: ((s1 * (barW as Float)) + 0.5) as Int;
			local Int is c2: ((s2 * (barW as Float)) + 0.5) as Int;
			if({ c1 > barW }, { c1: barW; });
			if({ c2 < c1 }, { c2: c1; });
			if({ c2 > barW }, { c2: barW; });
			local Int is c3: barW - c2;

			local String is bar: '';
			if({ c1 > 0 }, {
				bar: bar . :stage1Color:fgSeq() . CleoText:repeatStr(s: '█', count: c1) . Ansi:reset();
			});
			if({ (c2 - c1) > 0 }, {
				bar: bar . :stage2Color:fgSeq() . CleoText:repeatStr(s: '▓', count: c2 - c1) . Ansi:reset();
			});
			if({ c3 > 0 }, {
				bar: bar . :trackColor:fgSeq() . CleoText:repeatStr(s: '░', count: c3) . Ansi:reset();
			});
			bar: bar . pctLabel;
			out:add(item: :styleLine(raw: bar, innerW: innerW, secFg: secFg, secBg: secBg));
			return out;
		});
		if({ :kind == 4 }, {
			if({ :hasImage }, {
				:image:renderLines():each(action: local Function(String is row){
					out:add(item: :styleLine(raw: row, innerW: innerW, secFg: secFg, secBg: secBg));
				});
			});
			if({ !:hasImage }, {
				:asciiLines:each(action: local Function(String is row){
					out:add(item: :styleLine(raw: row, innerW: innerW, secFg: secFg, secBg: secBg));
				});
			});
			return out;
		});
		return out;
	}
}
