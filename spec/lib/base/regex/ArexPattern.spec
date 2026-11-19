#! Package base:regex
#! Compiled, reusable regular expression pattern (`ArexPattern`).
##
## Uses a linear-time Pike VM (Thompson NFA with capture groups, lazy/greedy
## priority, word boundaries, flags, and optional Unicode codepoint mode) for all
## standard patterns, and dispatches to a backtracking VM only when opt-in
## lookaround or backreferences are used.

Class is ArexPattern{
	namespace: ['base', 'regex'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'core', String],
		['base', 'struct', Array],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	# NFA opcodes:
	#  0 = SPLIT (epsilon to out1, out2; out1 has higher priority)
	#  1 = LITERAL (arg1 = unit/codepoint, arg2 = caseFold, to out1)
	#  2 = ANY (arg2 = dotAll, to out1)
	#  3 = CLASS (arg1 = classId, arg2 = caseFold, to out1)
	#  4 = ANCHOR_START (arg2 = multiline, to out1)
	#  5 = ANCHOR_END (arg2 = multiline, to out1)
	#  6 = MATCH (accepting)
	#  7 = SAVE (arg1 = capture slot, to out1)
	#  8 = WORD_BOUNDARY (\b, to out1)
	#  9 = NON_WORD_BOUNDARY (\B, to out1)
	# 10 = LOOKAHEAD_POS (arg1 = subStart, to out1)
	# 11 = LOOKAHEAD_NEG (arg1 = subStart, to out1)
	# 12 = LOOKBEHIND_POS (arg1 = subStart, to out1)
	# 13 = LOOKBEHIND_NEG (arg1 = subStart, to out1)
	# 14 = BACKREF (arg1 = groupIndex, arg2 = caseFold, to out1)
	local Array of Int is ops: [];
	local Array of Int is arg1s: [];
	local Array of Int is arg2s: [];
	local Array of Int is out1s: [];
	local Array of Int is out2s: [];

	local Array of Int is classNegated: [];
	local Array of Int is classRangeCid: [];
	local Array of Int is classRangeLo: [];
	local Array of Int is classRangeHi: [];

	local Str is pat: '';
	local String is patStr: '';
	local Int is pLen: 0;
	local Int is pos: 0;
	local Int is startState: 0;
	local Int is numGroups: 0;
	local Array of String is groupNames: [];

	local Boolean is flagI: false;
	local Boolean is flagM: false;
	local Boolean is flagS: false;
	local Boolean is flagU: false;

	local Boolean is allowLookaround: false;
	local Boolean is allowBackref: false;
	local Boolean is hasLookaround: false;
	local Boolean is hasBackref: false;
	local Str is compileError: '';

	replace Function is init(){
		:ops: [];
		:arg1s: [];
		:arg2s: [];
		:out1s: [];
		:out2s: [];
		:classNegated: [];
		:classRangeCid: [];
		:classRangeLo: [];
		:classRangeHi: [];
		:pat: '';
		:pLen: 0;
		:pos: 0;
		:startState: 0;
		:numGroups: 0;
		:groupNames: [''];
		:flagI: false;
		:flagM: false;
		:flagS: false;
		:flagU: false;
		:allowLookaround: false;
		:allowBackref: false;
		:hasLookaround: false;
		:hasBackref: false;
		:compileError: '';
	}

	## Compiles [pattern] into a reusable [ArexPattern].
	held Function of ArexPattern is compile(
		Str is pattern,
		Str is flags: '',
		Boolean is enableLookaround: false,
		Boolean is enableBackreference: false
	){
		local ArexPattern is compiled: ArexPattern:init();
		compiled:configureAndCompile(
			pattern: pattern,
			flags: flags,
			enableLookaround: enableLookaround,
			enableBackreference: enableBackreference
		);
		return compiled;
	}

	Function is configureAndCompile(
		Str is pattern,
		Str is flags,
		Boolean is enableLookaround,
		Boolean is enableBackreference
	){
		:allowLookaround: enableLookaround;
		:allowBackref: enableBackreference;
		:applyFlagString(flags: flags, enable: true);
		:compilePattern(pattern: pattern);
	}

	## Returns the original pattern source string.
	Function of Str is pattern(){
		return :pat;
	}

	## True when compilation failed with a syntax or feature-gate error.
	Function of Boolean is hasError(){
		return :compileError != '';
	}

	## Returns the compilation error message ('' when valid).
	Function of Str is errorMessage(){
		return :compileError;
	}

	## Number of capturing groups in this pattern.
	Function of Int is groupCount(){
		return :numGroups;
	}

	local Function is setError(Str is msg){
		if({ :compileError == '' }, {
			:compileError: msg;
		});
	}

	local Function is applyFlagString(Str is flags, Boolean is enable){
		local Int is i: 0;
		local Int is flen: flags:length();
		while({ i < flen }, {
			local Int is b: flags:byteAt(index: i);
			if({ b == 105 }, { :flagI: enable; }); # 'i'
			if({ b == 109 }, { :flagM: enable; }); # 'm'
			if({ b == 115 }, { :flagS: enable; }); # 's'
			if({ b == 117 }, { :flagU: enable; }); # 'u'
			i: i + 1;
		});
	}

	local Function of Int is addNode(Int is op, Int is arg1, Int is arg2, Int is out1, Int is out2){
		local Int is id: :ops:length();
		:ops:add(item: op);
		:arg1s:add(item: arg1);
		:arg2s:add(item: arg2);
		:out1s:add(item: out1);
		:out2s:add(item: out2);
		return id;
	}

	local Function of Int is foldCodepoint(Int is cp){
		if({ cp >= 65 && cp <= 90 }, { return cp + 32; });
		if({ !:flagU }, { return cp; });
		if({ (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) || (cp >= 913 && cp <= 937 && cp != 930) || (cp >= 1040 && cp <= 1071) || (cp >= 65313 && cp <= 65338) }, {
			return cp + 32;
		});
		if({ cp == 930 }, { return 962; });
		if({ cp >= 256 && cp <= 310 && (cp & 1) == 0 }, { return cp + 1; });
		if({ cp >= 1024 && cp <= 1039 }, { return cp + 80; });
		return cp;
	}

	local Function of Int is newClass(Int is negated){
		local Int is cid: :classNegated:length();
		:classNegated:add(item: negated);
		return cid;
	}

	local Function is addClassRange(Int is cid, Int is lo, Int is hi){
		:classRangeCid:add(item: cid);
		:classRangeLo:add(item: lo);
		:classRangeHi:add(item: hi);
	}

	local Function is addDigitRanges(Int is cid){
		:addClassRange(cid: cid, lo: 48, hi: 57);
	}

	local Function is addWordRanges(Int is cid){
		:addClassRange(cid: cid, lo: 48, hi: 57);
		:addClassRange(cid: cid, lo: 65, hi: 90);
		:addClassRange(cid: cid, lo: 95, hi: 95);
		:addClassRange(cid: cid, lo: 97, hi: 122);
		if({ :flagU }, {
			:addClassRange(cid: cid, lo: 192, hi: 687);
			:addClassRange(cid: cid, lo: 880, hi: 1153);
		});
	}

	local Function is addSpaceRanges(Int is cid){
		:addClassRange(cid: cid, lo: 9, hi: 13);
		:addClassRange(cid: cid, lo: 32, hi: 32);
		if({ :flagU }, {
			:addClassRange(cid: cid, lo: 160, hi: 160);
			:addClassRange(cid: cid, lo: 8192, hi: 8202);
			:addClassRange(cid: cid, lo: 12288, hi: 12288);
		});
	}

	local Function of Boolean is classMatches(Int is cid, Int is cp, Int is caseFold){
		local Int is target: cp;
		if({ caseFold == 1 }, {
			target: :foldCodepoint(cp: cp);
		});
		local Int is n: :classRangeCid:length();
		local Boolean is hit: false;
		local Int is i: 0;
		while({ i < n }, {
			if({ :classRangeCid:get(index: i) == cid }, {
				local Int is lo: :classRangeLo:get(index: i);
				local Int is hi: :classRangeHi:get(index: i);
				if({ caseFold == 1 }, {
					lo: :foldCodepoint(cp: lo);
					hi: :foldCodepoint(cp: hi);
					if({ lo > hi }, {
						local Int is tmp: lo;
						lo: hi;
						hi: tmp;
					});
				});
				if({ target >= lo && target <= hi }, {
					hit: true;
					i: n;
				}, {
					i: i + 1;
				});
			}, {
				i: i + 1;
			});
		});
		if({ :classNegated:get(index: cid) == 1 }, {
			return !hit;
		});
		return hit;
	}

	local Function of Int is flagIVal(){
		if({ :flagI }, { return 1; });
		return 0;
	}

	local Function of Int is flagMVal(){
		if({ :flagM }, { return 1; });
		return 0;
	}

	local Function of Int is flagSVal(){
		if({ :flagS }, { return 1; });
		return 0;
	}

	local Function of Int is peekUnit(){
		if({ :pos >= :pLen }, { return -1; });
		if({ :flagU }, {
			return :patStr:codePointAt(byteIndex: :pos, default: -1);
		});
		return :pat:byteAt(index: :pos);
	}

	local Function of Int is readUnit(){
		if({ :pos >= :pLen }, { return -1; });
		if({ :flagU }, {
			local Int is cp: :patStr:codePointAt(byteIndex: :pos, default: -1);
			local Int is blen: :patStr:codePointByteLen(byteIndex: :pos);
			if({ blen <= 0 }, { blen: 1; });
			:pos: :pos + blen;
			return cp;
		});
		local Int is b: :pat:byteAt(index: :pos);
		:pos: :pos + 1;
		return b;
	}

	local Function of Array of Int is makeFrag(Int is start, Int is exit){
		local Array of Int is f: [];
		f:add(item: start);
		f:add(item: exit);
		return f;
	}

	local Function of Array of Int is emptyFrag(){
		local Int is s: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		return :makeFrag(start: s, exit: s);
	}

	local Function of Array of Int is singleNodeFrag(Int is op, Int is arg1, Int is arg2){
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		local Int is start: :addNode(op: op, arg1: arg1, arg2: arg2, out1: exit, out2: -1);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is concatFrag(Array of Int is a, Array of Int is b){
		:out1s:set(index: a:get(index: 1), value: b:get(index: 0));
		return :makeFrag(start: a:get(index: 0), exit: b:get(index: 1));
	}

	local Function of Array of Int is altFrag(Array of Int is a, Array of Int is b){
		local Int is start: :addNode(op: 0, arg1: 0, arg2: 0, out1: a:get(index: 0), out2: b:get(index: 0));
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		:out1s:set(index: a:get(index: 1), value: exit);
		:out1s:set(index: b:get(index: 1), value: exit);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is starFrag(Array of Int is a, Boolean is lazy){
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		local Int is start: 0;
		if({ lazy }, {
			start: :addNode(op: 0, arg1: 0, arg2: 0, out1: exit, out2: a:get(index: 0));
		}, {
			start: :addNode(op: 0, arg1: 0, arg2: 0, out1: a:get(index: 0), out2: exit);
		});
		:out1s:set(index: a:get(index: 1), value: start);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is plusFrag(Array of Int is a, Boolean is lazy){
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		local Int is loop: 0;
		if({ lazy }, {
			loop: :addNode(op: 0, arg1: 0, arg2: 0, out1: exit, out2: a:get(index: 0));
		}, {
			loop: :addNode(op: 0, arg1: 0, arg2: 0, out1: a:get(index: 0), out2: exit);
		});
		:out1s:set(index: a:get(index: 1), value: loop);
		return :makeFrag(start: a:get(index: 0), exit: exit);
	}

	local Function of Array of Int is optFrag(Array of Int is a, Boolean is lazy){
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		local Int is start: 0;
		if({ lazy }, {
			start: :addNode(op: 0, arg1: 0, arg2: 0, out1: exit, out2: a:get(index: 0));
		}, {
			start: :addNode(op: 0, arg1: 0, arg2: 0, out1: a:get(index: 0), out2: exit);
		});
		:out1s:set(index: a:get(index: 1), value: exit);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is wrapCaptureFrag(Array of Int is inner, Int is groupIdx){
		local Int is saveStart: :addNode(op: 7, arg1: groupIdx * 2, arg2: 0, out1: inner:get(index: 0), out2: -1);
		local Int is exit: :addNode(op: 0, arg1: 0, arg2: 0, out1: -1, out2: -1);
		local Int is saveEnd: :addNode(op: 7, arg1: groupIdx * 2 + 1, arg2: 0, out1: exit, out2: -1);
		:out1s:set(index: inner:get(index: 1), value: saveEnd);
		return :makeFrag(start: saveStart, exit: exit);
	}

	local Function of Int is unescapeChar(Int is b){
		if({ b == 110 }, { return 10; }); # \n
		if({ b == 114 }, { return 13; }); # \r
		if({ b == 116 }, { return 9; });  # \t
		return b;
	}

	local Function of Array of Int is parseEscapeAtom(){
		if({ :pos >= :pLen }, {
			:setError(msg: 'Trailing backslash in regex pattern.');
			return :singleNodeFrag(op: 1, arg1: 92, arg2: 0);
		});
		local Int is b: :readUnit();
		if({ b == 98 }, { # \b
			return :singleNodeFrag(op: 8, arg1: 0, arg2: 0);
		});
		if({ b == 66 }, { # \B
			return :singleNodeFrag(op: 9, arg1: 0, arg2: 0);
		});
		if({ b >= 49 && b <= 57 }, { # \1 .. \9
			if({ !:allowBackref }, {
				:setError(msg: 'Backreferences are disabled; call enableBackreference(true) to enable them.');
				return :emptyFrag();
			});
			:hasBackref: true;
			return :singleNodeFrag(op: 14, arg1: b - 48, arg2: :flagIVal());
		});
		if({ b == 100 || b == 68 }, { # \d, \D
			local Int is neg: 0;
			if({ b == 68 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addDigitRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid, arg2: 0);
		});
		if({ b == 119 || b == 87 }, { # \w, \W
			local Int is neg: 0;
			if({ b == 87 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addWordRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid, arg2: 0);
		});
		if({ b == 115 || b == 83 }, { # \s, \S
			local Int is neg: 0;
			if({ b == 83 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addSpaceRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid, arg2: 0);
		});
		local Int is ch: :unescapeChar(b: b);
		local Int is cf: :flagIVal();
		if({ cf == 1 }, { ch: :foldCodepoint(cp: ch); });
		return :singleNodeFrag(op: 1, arg1: ch, arg2: cf);
	}

	local Function of Int is readClassChar(){
		local Int is b: :readUnit();
		if({ b == 92 }, {
			if({ :pos >= :pLen }, {
				:setError(msg: 'Trailing backslash inside character class.');
				return 92;
			});
			local Int is esc: :readUnit();
			return :unescapeChar(b: esc);
		});
		return b;
	}

	local Function of Array of Int is parseClassAtom(){
		local Int is negated: 0;
		if({ :peekUnit() == 94 }, { # '^'
			negated: 1;
			:readUnit();
		});
		local Int is cid: :newClass(negated: negated);
		local Boolean is first: true;
		while({ :pos < :pLen }, {
			local Int is b: :peekUnit();
			if({ b == 93 && !first }, { # ']'
				:readUnit();
				return :singleNodeFrag(op: 3, arg1: cid, arg2: :flagIVal());
			});
			first: false;
			if({ b == 92 && :pos + 1 < :pLen }, {
				local Int is nextB: :pat:byteAt(index: :pos + 1);
				if({ nextB == 100 }, { # \d
					:pos: :pos + 2;
					:addDigitRanges(cid: cid);
				}, {
					if({ nextB == 119 }, { # \w
						:pos: :pos + 2;
						:addWordRanges(cid: cid);
					}, {
						if({ nextB == 115 }, { # \s
							:pos: :pos + 2;
							:addSpaceRanges(cid: cid);
						}, {
							local Int is ch: :readClassChar();
							if({ :peekUnit() == 45 && :pos + 1 < :pLen && :pat:byteAt(index: :pos + 1) != 93 }, {
								:readUnit();
								local Int is hi: :readClassChar();
								:addClassRange(cid: cid, lo: ch, hi: hi);
							}, {
								:addClassRange(cid: cid, lo: ch, hi: ch);
							});
						});
					});
				});
			}, {
				local Int is ch: :readClassChar();
				if({ :peekUnit() == 45 && :pos + 1 < :pLen && :pat:byteAt(index: :pos + 1) != 93 }, {
					:readUnit();
					local Int is hi: :readClassChar();
					:addClassRange(cid: cid, lo: ch, hi: hi);
				}, {
					:addClassRange(cid: cid, lo: ch, hi: ch);
				});
			});
		});
		:setError(msg: 'Unclosed character class \'[\' in regex pattern.');
		return :singleNodeFrag(op: 3, arg1: cid, arg2: :flagIVal());
	}

	local Function of Array of Int is parseGroupAtom(){
		if({ :peekUnit() == 63 }, { # '(?'
			:readUnit();
			local Int is next: :peekUnit();
			if({ next == 58 }, { # '(?:' non-capturing
				:readUnit();
				local Array of Int is inner: :parseAlt();
				if({ :peekUnit() == 41 }, { :readUnit(); }, { :setError(msg: 'Unclosed group \'(\' in regex pattern.'); });
				return inner;
			});
			if({ next == 61 || next == 33 }, { # '(?=' or '(?!'
				:readUnit();
				if({ !:allowLookaround }, {
					:setError(msg: 'Lookaround is disabled; call enableLookaround(true) to enable it.');
					:parseAlt();
					if({ :peekUnit() == 41 }, { :readUnit(); });
					return :emptyFrag();
				});
				:hasLookaround: true;
				local Int is laOp: 10;
				if({ next == 33 }, { laOp: 11; });
				local Array of Int is sub: :parseAlt();
				if({ :peekUnit() == 41 }, { :readUnit(); }, { :setError(msg: 'Unclosed lookahead group in regex pattern.'); });
				local Int is subMatch: :addNode(op: 6, arg1: 0, arg2: 0, out1: -1, out2: -1);
				:out1s:set(index: sub:get(index: 1), value: subMatch);
				return :singleNodeFrag(op: laOp, arg1: sub:get(index: 0), arg2: 0);
			});
			if({ next == 60 }, { # '(?<' -> lookbehind '(?<=' / '(?<!' OR named capture '(?<name>...)'
				:readUnit();
				local Int is lbCh: :peekUnit();
				if({ lbCh == 61 || lbCh == 33 }, {
					:readUnit();
					if({ !:allowLookaround }, {
						:setError(msg: 'Lookaround is disabled; call enableLookaround(true) to enable it.');
						:parseAlt();
						if({ :peekUnit() == 41 }, { :readUnit(); });
						return :emptyFrag();
					});
					:hasLookaround: true;
					local Int is lbOp: 12;
					if({ lbCh == 33 }, { lbOp: 13; });
					local Array of Int is sub: :parseAlt();
					if({ :peekUnit() == 41 }, { :readUnit(); }, { :setError(msg: 'Unclosed lookbehind group in regex pattern.'); });
					local Int is subMatch: :addNode(op: 6, arg1: 0, arg2: 0, out1: -1, out2: -1);
					:out1s:set(index: sub:get(index: 1), value: subMatch);
					return :singleNodeFrag(op: lbOp, arg1: sub:get(index: 0), arg2: 0);
				});
				# Named capturing group (?<name>...)
				local String is gName: '';
				while({ :pos < :pLen && :peekUnit() != 62 }, {
					local Int is ch: :readUnit();
					gName: gName . String:fromCodePoint(code: ch);
				});
				if({ :peekUnit() == 62 }, { :readUnit(); }, { :setError(msg: 'Unclosed named group \'(?<...>\' in regex pattern.'); });
				:numGroups: :numGroups + 1;
				local Int is gIdx: :numGroups;
				:groupNames:add(item: gName);
				local Array of Int is inner: :parseAlt();
				if({ :peekUnit() == 41 }, { :readUnit(); }, { :setError(msg: 'Unclosed group \'(\' in regex pattern.'); });
				return :wrapCaptureFrag(inner: inner, groupIdx: gIdx);
			});
			# Inline flags (?i), (?ims), (?i:...)
			local Boolean is savedI: :flagI;
			local Boolean is savedM: :flagM;
			local Boolean is savedS: :flagS;
			local Boolean is savedU: :flagU;
			local Boolean is negMode: false;
			local Boolean is flagLoop: true;
			while({ flagLoop && :pos < :pLen }, {
				local Int is fc: :peekUnit();
				if({ fc == 45 }, { # '-'
					negMode: true;
					:readUnit();
				}, {
					if({ fc == 105 }, { :flagI: !negMode; :readUnit(); }, {
						if({ fc == 109 }, { :flagM: !negMode; :readUnit(); }, {
							if({ fc == 115 }, { :flagS: !negMode; :readUnit(); }, {
								if({ fc == 117 }, { :flagU: !negMode; :readUnit(); }, {
									flagLoop: false;
								});
							});
						});
					});
				});
			});
			if({ :peekUnit() == 58 }, { # '(?ims:...)' scoped flags
				:readUnit();
				local Array of Int is inner: :parseAlt();
				if({ :peekUnit() == 41 }, { :readUnit(); }, { :setError(msg: 'Unclosed group \'(\' in regex pattern.'); });
				:flagI: savedI;
				:flagM: savedM;
				:flagS: savedS;
				:flagU: savedU;
				return inner;
			});
			if({ :peekUnit() == 41 }, {
				:readUnit();
				return :emptyFrag();
			});
			:setError(msg: 'Invalid inline group syntax \'(?...)\' in regex pattern.');
			return :emptyFrag();
		});
		:numGroups: :numGroups + 1;
		local Int is gIdx: :numGroups;
		:groupNames:add(item: '');
		local Array of Int is inner: :parseAlt();
		if({ :peekUnit() == 41 }, {
			:readUnit();
		}, {
			:setError(msg: 'Unclosed group \'(\' in regex pattern.');
		});
		return :wrapCaptureFrag(inner: inner, groupIdx: gIdx);
	}

	local Function of Array of Int is parseAtom(){
		local Int is b: :readUnit();
		if({ b == 40 }, { # '('
			return :parseGroupAtom();
		});
		if({ b == 91 }, { # '['
			return :parseClassAtom();
		});
		if({ b == 92 }, { # '\'
			return :parseEscapeAtom();
		});
		if({ b == 46 }, { # '.'
			return :singleNodeFrag(op: 2, arg1: 0, arg2: :flagSVal());
		});
		if({ b == 94 }, { # '^'
			return :singleNodeFrag(op: 4, arg1: 0, arg2: :flagMVal());
		});
		if({ b == 36 }, { # '$'
			return :singleNodeFrag(op: 5, arg1: 0, arg2: :flagMVal());
		});
		local Int is cf: :flagIVal();
		if({ cf == 1 }, { b: :foldCodepoint(cp: b); });
		return :singleNodeFrag(op: 1, arg1: b, arg2: cf);
	}

	local Function of Array of Int is parseRepetitionSpan(Array of Int is baseFrag, Int is atomStart, Int is savedGroups){
		local Int is savePos: :pos;
		:pos: :pos + 1; # skip '{'
		local Int is minVal: 0;
		local Boolean is hasMin: false;
		while({ :pos < :pLen && :pat:byteAt(index: :pos) >= 48 && :pat:byteAt(index: :pos) <= 57 }, {
			hasMin: true;
			minVal: minVal * 10 + (:pat:byteAt(index: :pos) - 48);
			:pos: :pos + 1;
		});
		if({ !hasMin || :pos >= :pLen }, {
			:pos: savePos;
			return baseFrag;
		});
		local Int is maxVal: minVal;
		local Boolean is unbounded: false;
		local Int is sep: :pat:byteAt(index: :pos);
		if({ sep == 44 }, { # ','
			:pos: :pos + 1;
			if({ :pos < :pLen && :pat:byteAt(index: :pos) == 125 }, { # '}'
				unbounded: true;
			}, {
				maxVal: 0;
				local Boolean is hasMax: false;
				while({ :pos < :pLen && :pat:byteAt(index: :pos) >= 48 && :pat:byteAt(index: :pos) <= 57 }, {
					hasMax: true;
					maxVal: maxVal * 10 + (:pat:byteAt(index: :pos) - 48);
					:pos: :pos + 1;
				});
				if({ !hasMax }, {
					:pos: savePos;
					return baseFrag;
				});
			});
		});
		if({ :pos >= :pLen || :pat:byteAt(index: :pos) != 125 }, { # '}'
			:pos: savePos;
			return baseFrag;
		});
		:pos: :pos + 1; # skip '}'
		if({ !unbounded && maxVal < minVal }, {
			:setError(msg: 'Invalid repetition range {min,max}: max < min.');
			return baseFrag;
		});
		local Boolean is lazy: false;
		if({ :pos < :pLen && :pat:byteAt(index: :pos) == 63 }, {
			lazy: true;
			:pos: :pos + 1;
		});
		local Int is afterBracePos: :pos;

		local Array of Int is res: baseFrag;
		if({ minVal == 0 }, {
			res: :emptyFrag();
		});
		local Int is count: 1;
		while({ count < minVal }, {
			:pos: atomStart;
			:numGroups: savedGroups;
			local Array of Int is copy: :parseAtom();
			res: :concatFrag(a: res, b: copy);
			count: count + 1;
		});
		if({ unbounded }, {
			:pos: atomStart;
			:numGroups: savedGroups;
			local Array of Int is tail: :starFrag(a: :parseAtom(), lazy: lazy);
			res: :concatFrag(a: res, b: tail);
		}, {
			local Int is optCount: minVal;
			if({ minVal == 0 }, { optCount: 0; });
			while({ optCount < maxVal }, {
				:pos: atomStart;
				:numGroups: savedGroups;
				local Array of Int is optCopy: :optFrag(a: :parseAtom(), lazy: lazy);
				res: :concatFrag(a: res, b: optCopy);
				optCount: optCount + 1;
			});
		});
		:pos: afterBracePos;
		return res;
	}

	local Function of Array of Int is parseQuantified(){
		local Int is atomStart: :pos;
		local Int is savedGroups: :numGroups;
		local Array of Int is frag: :parseAtom();
		local Boolean is more: true;
		while({ more && :pos < :pLen }, {
			local Int is q: :pat:byteAt(index: :pos);
			if({ q == 42 }, { # '*'
				:pos: :pos + 1;
				local Boolean is lazy: false;
				if({ :pos < :pLen && :pat:byteAt(index: :pos) == 63 }, { lazy: true; :pos: :pos + 1; });
				frag: :starFrag(a: frag, lazy: lazy);
			}, {
				if({ q == 43 }, { # '+'
					:pos: :pos + 1;
					local Boolean is lazy: false;
					if({ :pos < :pLen && :pat:byteAt(index: :pos) == 63 }, { lazy: true; :pos: :pos + 1; });
					frag: :plusFrag(a: frag, lazy: lazy);
				}, {
					if({ q == 63 }, { # '?'
						:pos: :pos + 1;
						local Boolean is lazy: false;
						if({ :pos < :pLen && :pat:byteAt(index: :pos) == 63 }, { lazy: true; :pos: :pos + 1; });
						frag: :optFrag(a: frag, lazy: lazy);
					}, {
						if({ q == 123 }, { # '{'
							local Int is before: :pos;
							frag: :parseRepetitionSpan(baseFrag: frag, atomStart: atomStart, savedGroups: savedGroups);
							if({ :pos == before }, {
								more: false;
							});
						}, {
							more: false;
						});
					});
				});
			});
		});
		return frag;
	}

	local Function of Array of Int is parseSeq(){
		local Array of Int is frag: :emptyFrag();
		local Boolean is hasOne: false;
		local Boolean is more: true;
		while({ more && :pos < :pLen }, {
			local Int is b: :pat:byteAt(index: :pos);
			if({ b == 41 || b == 124 }, { # ')' or '|'
				more: false;
			}, {
				if({ b == 42 || b == 43 || b == 63 }, {
					:setError(msg: 'Nothing to repeat before quantifier in regex pattern.');
					:pos: :pos + 1;
				}, {
					local Array of Int is nextFrag: :parseQuantified();
					if({ !hasOne }, {
						frag: nextFrag;
						hasOne: true;
					}, {
						frag: :concatFrag(a: frag, b: nextFrag);
					});
				});
			});
		});
		return frag;
	}

	local Function of Array of Int is parseAlt(){
		local Array of Int is left: :parseSeq();
		while({ :pos < :pLen && :pat:byteAt(index: :pos) == 124 }, { # '|'
			:pos: :pos + 1;
			local Array of Int is right: :parseSeq();
			left: :altFrag(a: left, b: right);
		});
		return left;
	}

	local Function is compilePattern(Str is pattern){
		:pat: pattern;
		:patStr: pattern:copy();
		:pLen: pattern:length();
		:pos: 0;
		local Array of Int is root: :parseAlt();
		if({ :pos < :pLen }, {
			:setError(msg: 'Unmatched \')\' in regex pattern.');
		});
		local Array of Int is wrapped: :wrapCaptureFrag(inner: root, groupIdx: 0);
		local Int is matchNode: :addNode(op: 6, arg1: 0, arg2: 0, out1: -1, out2: -1);
		:out1s:set(index: wrapped:get(index: 1), value: matchNode);
		:startState: wrapped:get(index: 0);
	}

	# --- Input unit helpers (bytes vs Unicode codepoints when flagU is true) ---

	local Function is prepareUnits(Str is input, Array of Int is units, Array of Int is byteOffsets){
		local Int is blen: input:length();
		if({ !:flagU }, {
			local Int is i: 0;
			while({ i < blen }, {
				units:add(item: input:byteAt(index: i));
				byteOffsets:add(item: i);
				i: i + 1;
			});
			byteOffsets:add(item: blen);
			return;
		});
		local String is inStr: input:copy();
		local Int is i: 0;
		while({ i < blen }, {
			local Int is cp: inStr:codePointAt(byteIndex: i, default: 65533);
			local Int is clen: inStr:codePointByteLen(byteIndex: i);
			if({ clen <= 0 }, { clen: 1; });
			units:add(item: cp);
			byteOffsets:add(item: i);
			i: i + clen;
		});
		byteOffsets:add(item: blen);
	}

	local Function of Boolean is isWordUnit(Int is cp){
		if({ (cp >= 48 && cp <= 57) || (cp >= 65 && cp <= 90) || cp == 95 || (cp >= 97 && cp <= 122) }, {
			return true;
		});
		if({ :flagU && ((cp >= 192 && cp <= 687) || (cp >= 880 && cp <= 1153)) }, {
			return true;
		});
		return false;
	}

	local Function of Boolean is checkWordBoundary(Array of Int is units, Int is pos, Int is uLen, Boolean is wantBoundary){
		local Boolean is prevW: pos > 0 && :isWordUnit(cp: units:get(index: pos - 1));
		local Boolean is currW: pos < uLen && :isWordUnit(cp: units:get(index: pos));
		local Boolean is isBound: prevW != currW;
		if({ wantBoundary }, { return isBound; });
		return !isBound;
	}

	local Function of Boolean is checkAnchorStart(Array of Int is units, Int is pos, Int is multiline){
		if({ pos == 0 }, { return true; });
		if({ multiline == 1 && units:get(index: pos - 1) == 10 }, { return true; });
		return false;
	}

	local Function of Boolean is checkAnchorEnd(Array of Int is units, Int is pos, Int is uLen, Int is multiline){
		if({ pos == uLen }, { return true; });
		if({ multiline == 1 && units:get(index: pos) == 10 }, { return true; });
		return false;
	}

	local Function of Boolean is unitMatchesNode(Int is s, Int is u){
		local Int is op: :ops:get(index: s);
		if({ op == 1 }, {
			local Int is target: u;
			if({ :arg2s:get(index: s) == 1 }, {
				target: :foldCodepoint(cp: u);
			});
			return target == :arg1s:get(index: s);
		});
		if({ op == 2 }, {
			if({ :arg2s:get(index: s) == 1 }, { return true; });
			return u != 10;
		});
		if({ op == 3 }, {
			return :classMatches(cid: :arg1s:get(index: s), cp: u, caseFold: :arg2s:get(index: s));
		});
		return false;
	}

	# --- Pike VM (linear-time, ordered threads with capture slots & lazy priority) ---

	local Function is pikeAddThread(
		Int is state,
		Int is pos,
		Array of Int is units,
		Int is uLen,
		Array of Int is baseCaps,
		Int is capStride,
		Array of Int is listStates,
		Array of Int is listCaps,
		Array of Int is stamps,
		Int is stamp,
		Array of Int is stackStates,
		Array of Int is stackCaps
	){
		if({ state < 0 }, { return; });
		stackStates:clear();
		stackCaps:clear();
		stackStates:add(item: state);
		local Int is ci: 0;
		while({ ci < capStride }, {
			stackCaps:add(item: baseCaps:get(index: ci));
			ci: ci + 1;
		});

		while({ stackStates:length() > 0 }, {
			local Int is top: stackStates:length() - 1;
			local Int is s: stackStates:get(index: top);
			stackStates:removeAt(index: top);

			local Array of Int is curC: [];
			local Int is cBase: stackCaps:length() - capStride;
			ci: 0;
			while({ ci < capStride }, {
				curC:add(item: stackCaps:get(index: cBase + ci));
				ci: ci + 1;
			});
			ci: 0;
			while({ ci < capStride }, {
				stackCaps:removeAt(index: stackCaps:length() - 1);
				ci: ci + 1;
			});

			if({ s >= 0 && stamps:get(index: s) != stamp }, {
				stamps:set(index: s, value: stamp);
				local Int is op: :ops:get(index: s);
				if({ op == 0 }, {
					local Int is o2: :out2s:get(index: s);
					local Int is o1: :out1s:get(index: s);
					if({ o2 >= 0 }, {
						stackStates:add(item: o2);
						ci: 0;
						while({ ci < capStride }, {
							stackCaps:add(item: curC:get(index: ci));
							ci: ci + 1;
						});
					});
					if({ o1 >= 0 }, {
						stackStates:add(item: o1);
						ci: 0;
						while({ ci < capStride }, {
							stackCaps:add(item: curC:get(index: ci));
							ci: ci + 1;
						});
					});
				}, {
					if({ op == 7 }, { # SAVE
						local Int is slot: :arg1s:get(index: s);
						local Int is o1: :out1s:get(index: s);
						if({ o1 >= 0 }, {
							curC:set(index: slot, value: pos);
							stackStates:add(item: o1);
							ci: 0;
							while({ ci < capStride }, {
								stackCaps:add(item: curC:get(index: ci));
								ci: ci + 1;
							});
						});
					}, {
						if({ op == 4 || op == 5 || op == 8 || op == 9 }, {
							local Boolean is ok: false;
							if({ op == 4 }, { ok: :checkAnchorStart(units: units, pos: pos, multiline: :arg2s:get(index: s)); });
							if({ op == 5 }, { ok: :checkAnchorEnd(units: units, pos: pos, uLen: uLen, multiline: :arg2s:get(index: s)); });
							if({ op == 8 }, { ok: :checkWordBoundary(units: units, pos: pos, uLen: uLen, wantBoundary: true); });
							if({ op == 9 }, { ok: :checkWordBoundary(units: units, pos: pos, uLen: uLen, wantBoundary: false); });
							local Int is o1: :out1s:get(index: s);
							if({ ok && o1 >= 0 }, {
								stackStates:add(item: o1);
								ci: 0;
								while({ ci < capStride }, {
									stackCaps:add(item: curC:get(index: ci));
									ci: ci + 1;
								});
							});
						}, {
							listStates:add(item: s);
							ci: 0;
							while({ ci < capStride }, {
								listCaps:add(item: curC:get(index: ci));
								ci: ci + 1;
							});
						});
					});
				});
			});
		});
	}

	local Function of Array of Int is pikeMatchUnits(
		Array of Int is units,
		Int is startOffset,
		Boolean is anchorStart,
		Boolean is anchorEnd
	){
		local Int is uLen: units:length();
		local Int is numStates: :ops:length();
		local Int is capStride: (:numGroups + 1) * 2;

		local Array of Int is emptyCaps: [];
		local Int is ci: 0;
		while({ ci < capStride }, {
			emptyCaps:add(item: -1);
			ci: ci + 1;
		});

		local Array of Int is currStates: [];
		local Array of Int is currCaps: [];
		local Array of Int is nextStates: [];
		local Array of Int is nextCaps: [];
		local Array of Int is stamps: [];
		local Array of Int is stackStates: [];
		local Array of Int is stackCaps: [];

		local Int is i: 0;
		while({ i < numStates }, {
			stamps:add(item: 0);
			i: i + 1;
		});

		local Int is stamp: 1;
		local Boolean is found: false;
		local Array of Int is bestCaps: [];
		ci: 0;
		while({ ci < capStride }, {
			bestCaps:add(item: -1);
			ci: ci + 1;
		});

		local Int is idx: startOffset;
		while({ idx <= uLen }, {
			if({ (!anchorStart && !found) || (anchorStart && idx == 0) }, {
				stamp: stamp + 1;
				# Preserve existing thread deduplication by seeding after existing threads
				# (leftmost threads stay ahead of new threads!).
				local Int is ti: 0;
				while({ ti < currStates:length() }, {
					stamps:set(index: currStates:get(index: ti), value: stamp);
					ti: ti + 1;
				});
				:pikeAddThread(
					state: :startState,
					pos: idx,
					units: units,
					uLen: uLen,
					baseCaps: emptyCaps,
					capStride: capStride,
					listStates: currStates,
					listCaps: currCaps,
					stamps: stamps,
					stamp: stamp,
					stackStates: stackStates,
					stackCaps: stackCaps
				);
			});

			# Scan ordered threads: first MATCH wins for its priority, and cuts off lower-priority threads.
			local Int is limitThreads: currStates:length();
			local Int is k: 0;
			while({ k < limitThreads }, {
				local Int is s: currStates:get(index: k);
				if({ :ops:get(index: s) == 6 && (!anchorEnd || idx == uLen) }, {
					found: true;
					local Int is cBase: k * capStride;
					ci: 0;
					while({ ci < capStride }, {
						bestCaps:set(index: ci, value: currCaps:get(index: cBase + ci));
						ci: ci + 1;
					});
					limitThreads: k;
				});
				k: k + 1;
			});

			# Truncate lower-priority threads after a MATCH.
			if({ limitThreads < currStates:length() }, {
				while({ currStates:length() > limitThreads }, {
					currStates:removeAt(index: currStates:length() - 1);
					ci: 0;
					while({ ci < capStride }, {
						currCaps:removeAt(index: currCaps:length() - 1);
						ci: ci + 1;
					});
				});
			});

			if({ currStates:length() == 0 && (found || anchorStart) }, {
				idx: uLen + 1;
			}, {
				if({ idx < uLen }, {
					local Int is u: units:get(index: idx);
					stamp: stamp + 1;
					nextStates:clear();
					nextCaps:clear();
					k: 0;
					while({ k < currStates:length() }, {
						local Int is s: currStates:get(index: k);
						if({ :unitMatchesNode(s: s, u: u) }, {
							local Array of Int is tCaps: [];
							local Int is cBase: k * capStride;
							ci: 0;
							while({ ci < capStride }, {
								tCaps:add(item: currCaps:get(index: cBase + ci));
								ci: ci + 1;
							});
							:pikeAddThread(
								state: :out1s:get(index: s),
								pos: idx + 1,
								units: units,
								uLen: uLen,
								baseCaps: tCaps,
								capStride: capStride,
								listStates: nextStates,
								listCaps: nextCaps,
								stamps: stamps,
								stamp: stamp,
								stackStates: stackStates,
								stackCaps: stackCaps
							);
						});
						k: k + 1;
					});
					currStates:clear();
					currCaps:clear();
					k: 0;
					while({ k < nextStates:length() }, {
						currStates:add(item: nextStates:get(index: k));
						k: k + 1;
					});
					ci: 0;
					while({ ci < nextCaps:length() }, {
						currCaps:add(item: nextCaps:get(index: ci));
						ci: ci + 1;
					});
				});
				idx: idx + 1;
			});
		});

		local Array of Int is out: [];
		if({ found }, { out:add(item: 1); }, { out:add(item: 0); });
		ci: 0;
		while({ ci < capStride }, {
			out:add(item: bestCaps:get(index: ci));
			ci: ci + 1;
		});
		return out;
	}

	# --- Backtracking VM (used only when lookaround or backreferences are present) ---

	local Function of Boolean is btExec(
		Int is s,
		Int is pos,
		Array of Int is units,
		Int is uLen,
		Array of Int is caps,
		Int is exactEndPos
	){
		if({ s < 0 }, { return false; });
		local Int is op: :ops:get(index: s);
		if({ op == 6 }, { # MATCH
			if({ exactEndPos >= 0 && pos != exactEndPos }, { return false; });
			return true;
		});
		if({ op == 0 }, { # SPLIT
			if({ :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos) }, {
				return true;
			});
			return :btExec(s: :out2s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 7 }, { # SAVE
			local Int is slot: :arg1s:get(index: s);
			local Int is oldVal: caps:get(index: slot);
			caps:set(index: slot, value: pos);
			if({ :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos) }, {
				return true;
			});
			caps:set(index: slot, value: oldVal);
			return false;
		});
		if({ op == 4 }, {
			if({ !:checkAnchorStart(units: units, pos: pos, multiline: :arg2s:get(index: s)) }, { return false; });
			return :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 5 }, {
			if({ !:checkAnchorEnd(units: units, pos: pos, uLen: uLen, multiline: :arg2s:get(index: s)) }, { return false; });
			return :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 8 || op == 9 }, {
			if({ !:checkWordBoundary(units: units, pos: pos, uLen: uLen, wantBoundary: op == 8) }, { return false; });
			return :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 10 || op == 11 }, { # LOOKAHEAD_POS / LOOKAHEAD_NEG
			local Int is subStart: :arg1s:get(index: s);
			local Boolean is ok: :btExec(s: subStart, pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: -1);
			if({ op == 11 }, { ok: !ok; });
			if({ !ok }, { return false; });
			return :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 12 || op == 13 }, { # LOOKBEHIND_POS / LOOKBEHIND_NEG
			local Int is subStart: :arg1s:get(index: s);
			local Boolean is matchedLb: false;
			local Int is lbStart: pos;
			while({ lbStart >= 0 && !matchedLb }, {
				if({ :btExec(s: subStart, pos: lbStart, units: units, uLen: uLen, caps: caps, exactEndPos: pos) }, {
					matchedLb: true;
				}, {
					lbStart: lbStart - 1;
				});
			});
			local Boolean is ok: matchedLb;
			if({ op == 13 }, { ok: !matchedLb; });
			if({ !ok }, { return false; });
			return :btExec(s: :out1s:get(index: s), pos: pos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ op == 14 }, { # BACKREF
			local Int is g: :arg1s:get(index: s);
			if({ g * 2 + 1 >= caps:length() }, { return false; });
			local Int is gs: caps:get(index: g * 2);
			local Int is ge: caps:get(index: g * 2 + 1);
			if({ gs < 0 || ge < gs }, { return false; });
			local Int is glen: ge - gs;
			if({ pos + glen > uLen }, { return false; });
			local Int is cf: :arg2s:get(index: s);
			local Int is j: 0;
			while({ j < glen }, {
				local Int is u1: units:get(index: gs + j);
				local Int is u2: units:get(index: pos + j);
				if({ cf == 1 }, {
					u1: :foldCodepoint(cp: u1);
					u2: :foldCodepoint(cp: u2);
				});
				if({ u1 != u2 }, { return false; });
				j: j + 1;
			});
			return :btExec(s: :out1s:get(index: s), pos: pos + glen, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
		});
		if({ pos >= uLen }, { return false; });
		if({ !:unitMatchesNode(s: s, u: units:get(index: pos)) }, { return false; });
		return :btExec(s: :out1s:get(index: s), pos: pos + 1, units: units, uLen: uLen, caps: caps, exactEndPos: exactEndPos);
	}

	local Function of Array of Int is btMatchUnits(
		Array of Int is units,
		Int is startOffset,
		Boolean is anchorStart,
		Boolean is anchorEnd
	){
		local Int is uLen: units:length();
		local Int is capStride: (:numGroups + 1) * 2;
		local Array of Int is caps: [];
		local Int is ci: 0;
		while({ ci < capStride }, {
			caps:add(item: -1);
			ci: ci + 1;
		});
		local Int is exactEnd: -1;
		if({ anchorEnd }, { exactEnd: uLen; });
		local Int is maxStart: uLen;
		if({ anchorStart }, { maxStart: 0; });
		local Int is sPos: startOffset;
		while({ sPos <= maxStart }, {
			ci: 0;
			while({ ci < capStride }, {
				caps:set(index: ci, value: -1);
				ci: ci + 1;
			});
			if({ :btExec(s: :startState, pos: sPos, units: units, uLen: uLen, caps: caps, exactEndPos: exactEnd) }, {
				local Array of Int is out: [1];
				ci: 0;
				while({ ci < capStride }, {
					out:add(item: caps:get(index: ci));
					ci: ci + 1;
				});
				return out;
			});
			sPos: sPos + 1;
		});
		local Array of Int is miss: [0];
		ci: 0;
		while({ ci < capStride }, {
			miss:add(item: -1);
			ci: ci + 1;
		});
		return miss;
	}

	local Function of Array of Int is runUnitMatch(
		Array of Int is units,
		Int is startOffset,
		Boolean is anchorStart,
		Boolean is anchorEnd
	){
		if({ :hasLookaround || :hasBackref }, {
			return :btMatchUnits(units: units, startOffset: startOffset, anchorStart: anchorStart, anchorEnd: anchorEnd);
		});
		return :pikeMatchUnits(units: units, startOffset: startOffset, anchorStart: anchorStart, anchorEnd: anchorEnd);
	}

	local Function of String is expandReplacement(Str is template, Str is input, Array of Int is matchRes, Array of Int is byteOffsets){
		local Int is tlen: template:length();
		local String is out: '';
		local Int is i: 0;
		while({ i < tlen }, {
			local Int is b: template:byteAt(index: i);
			if({ b == 36 && i + 1 < tlen }, { # '$'
				local Int is nb: template:byteAt(index: i + 1);
				if({ nb == 36 }, { # '$$'
					out: out . '$';
					i: i + 2;
				}, {
					if({ nb >= 48 && nb <= 57 }, { # '$0'..'$9'
						local Int is g: nb - 48;
						if({ g <= :numGroups }, {
							local Int is us: matchRes:get(index: 1 + g * 2);
							local Int is ue: matchRes:get(index: 1 + g * 2 + 1);
							if({ us >= 0 && ue >= us }, {
								local Int is bs: byteOffsets:get(index: us);
								local Int is be: byteOffsets:get(index: ue);
								out: out . input:substring(start: bs, end: be);
							});
						});
						i: i + 2;
					}, {
						out: out . template:substring(start: i, end: i + 1);
						i: i + 1;
					});
				});
			}, {
				out: out . template:substring(start: i, end: i + 1);
				i: i + 1;
			});
		});
		return out;
	}

	# --- Synchronous execution entry points ---

	Function is rContainsSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: false, anchorEnd: false);
		local Boolean is matched: matchRes:get(index: 0) == 1;
		result(matched);
	}

	Function is rEqualsSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: true, anchorEnd: true);
		local Boolean is matched: matchRes:get(index: 0) == 1;
		result(matched);
	}

	Function is rStartsWithSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: true, anchorEnd: false);
		local Boolean is matched: matchRes:get(index: 0) == 1;
		result(matched);
	}

	Function is rEndsWithSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: false, anchorEnd: true);
		local Boolean is matched: matchRes:get(index: 0) == 1;
		result(matched);
	}

	Function is rFindSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: false, anchorEnd: false);
		local Boolean is found: matchRes:get(index: 0) == 1;
		local Int is start: -1;
		local Int is end: -1;
		local Str is matchedText: '';
		if({ found }, {
			start: byteOffsets:get(index: matchRes:get(index: 1));
			end: byteOffsets:get(index: matchRes:get(index: 2));
			matchedText: input:substring(start: start, end: end);
		});
		result(found, matchedText, start, end);
	}

	Function is rCapturesSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Array of Int is matchRes: :runUnitMatch(units: units, startOffset: 0, anchorStart: false, anchorEnd: false);
		local Boolean is found: matchRes:get(index: 0) == 1;
		local Array of Str is groups: [];
		if({ found }, {
			local Int is g: 0;
			while({ g <= :numGroups }, {
				local Int is us: matchRes:get(index: 1 + g * 2);
				local Int is ue: matchRes:get(index: 1 + g * 2 + 1);
				if({ us >= 0 && ue >= us }, {
					groups:add(item: input:substring(start: byteOffsets:get(index: us), end: byteOffsets:get(index: ue)));
				}, {
					groups:add(item: '');
				});
				g: g + 1;
			});
		});
		result(found, groups);
	}

	Function is rCountSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Int is uLen: units:length();
		local Int is cursor: 0;
		local Int is total: 0;
		local Boolean is running: true;
		while({ running && cursor <= uLen }, {
			local Array of Int is m: :runUnitMatch(units: units, startOffset: cursor, anchorStart: false, anchorEnd: false);
			if({ m:get(index: 0) == 1 }, {
				total: total + 1;
				local Int is s: m:get(index: 1);
				local Int is e: m:get(index: 2);
				if({ e > s }, {
					cursor: e;
				}, {
					cursor: e + 1;
					if({ e >= uLen }, { running: false; });
				});
			}, {
				running: false;
			});
		});
		result(total);
	}

	Function is rFindAllSync(Str is input, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Int is uLen: units:length();
		local Array of Str is matches: [];
		local Int is cursor: 0;
		local Boolean is running: true;
		while({ running && cursor <= uLen }, {
			local Array of Int is m: :runUnitMatch(units: units, startOffset: cursor, anchorStart: false, anchorEnd: false);
			if({ m:get(index: 0) == 1 }, {
				local Int is s: m:get(index: 1);
				local Int is e: m:get(index: 2);
				matches:add(item: input:substring(start: byteOffsets:get(index: s), end: byteOffsets:get(index: e)));
				if({ e > s }, {
					cursor: e;
				}, {
					cursor: e + 1;
					if({ e >= uLen }, { running: false; });
				});
			}, {
				running: false;
			});
		});
		result(matches);
	}

	Function is rSplitSync(Str is input, Function is result, Int is limit: -1){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Int is uLen: units:length();
		local Int is inLen: input:length();
		local Array of Str is parts: [];
		if({ limit == 1 }, {
			parts:add(item: input);
			result(parts);
			return;
		});
		local Int is cursor: 0;
		local Boolean is running: true;
		while({ running && cursor <= uLen }, {
			if({ limit > 0 && parts:length() + 1 >= limit }, {
				parts:add(item: input:substring(start: byteOffsets:get(index: cursor), end: inLen));
				cursor: uLen + 1;
				running: false;
			}, {
				local Array of Int is m: :runUnitMatch(units: units, startOffset: cursor, anchorStart: false, anchorEnd: false);
				if({ m:get(index: 0) == 1 }, {
					local Int is s: m:get(index: 1);
					local Int is e: m:get(index: 2);
					parts:add(item: input:substring(start: byteOffsets:get(index: cursor), end: byteOffsets:get(index: s)));
					if({ e > s }, {
						cursor: e;
					}, {
						cursor: e + 1;
						if({ e >= uLen }, { running: false; });
					});
				}, {
					parts:add(item: input:substring(start: byteOffsets:get(index: cursor), end: inLen));
					cursor: uLen + 1;
					running: false;
				});
			});
		});
		if({ cursor == uLen }, {
			parts:add(item: '');
		});
		result(parts);
	}

	Function is rReplaceStrSync(Str is input, Str is replacement, Boolean is all, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Int is uLen: units:length();
		local Int is inLen: input:length();
		local Array of String is chunks: [];
		local Int is cursor: 0;
		local Boolean is running: true;
		while({ running && cursor <= uLen }, {
			local Array of Int is m: :runUnitMatch(units: units, startOffset: cursor, anchorStart: false, anchorEnd: false);
			if({ m:get(index: 0) == 1 }, {
				local Int is s: m:get(index: 1);
				local Int is e: m:get(index: 2);
				chunks:add(item: input:substring(start: byteOffsets:get(index: cursor), end: byteOffsets:get(index: s)));
				chunks:add(item: :expandReplacement(template: replacement, input: input, matchRes: m, byteOffsets: byteOffsets));
				if({ e > s }, {
					cursor: e;
				}, {
					if({ e < uLen }, {
						chunks:add(item: input:substring(start: byteOffsets:get(index: e), end: byteOffsets:get(index: e + 1)));
					});
					cursor: e + 1;
					if({ e >= uLen }, { running: false; });
				});
				if({ !all }, {
					running: false;
				});
			}, {
				running: false;
			});
		});
		if({ cursor <= uLen }, {
			chunks:add(item: input:substring(start: byteOffsets:get(index: cursor), end: inLen));
		});
		local Str is out: chunks:join(separator: '');
		result(out);
	}

	Function is rReplaceFnSync(Str is input, Function is replacer, Boolean is all, Function is result){
		local Array of Int is units: [];
		local Array of Int is byteOffsets: [];
		:prepareUnits(input: input, units: units, byteOffsets: byteOffsets);
		local Int is uLen: units:length();
		local Int is inLen: input:length();
		local Array of String is chunks: [];
		local Int is cursor: 0;
		local Boolean is running: true;
		while({ running && cursor <= uLen }, {
			local Array of Int is m: :runUnitMatch(units: units, startOffset: cursor, anchorStart: false, anchorEnd: false);
			if({ m:get(index: 0) == 1 }, {
				local Int is s: m:get(index: 1);
				local Int is e: m:get(index: 2);
				local Int is bs: byteOffsets:get(index: s);
				local Int is be: byteOffsets:get(index: e);
				chunks:add(item: input:substring(start: byteOffsets:get(index: cursor), end: bs));
				local Str is matchedStr: input:substring(start: bs, end: be);
				local Str is rep: replacer(matchedStr, bs, be);
				chunks:add(item: rep as String);
				if({ e > s }, {
					cursor: e;
				}, {
					if({ e < uLen }, {
						chunks:add(item: input:substring(start: byteOffsets:get(index: e), end: byteOffsets:get(index: e + 1)));
					});
					cursor: e + 1;
					if({ e >= uLen }, { running: false; });
				});
				if({ !all }, {
					running: false;
				});
			}, {
				running: false;
			});
		});
		if({ cursor <= uLen }, {
			chunks:add(item: input:substring(start: byteOffsets:get(index: cursor), end: inLen));
		});
		local Str is out: chunks:join(separator: '');
		result(out);
	}

	# --- Async instance methods on ArexPattern ---

	Function is rContains(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rContainsSync(input: input, result: result);
		});
	}

	Function is rEquals(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rEqualsSync(input: input, result: result);
		});
	}

	Function is rStartsWith(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rStartsWithSync(input: input, result: result);
		});
	}

	Function is rEndsWith(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rEndsWithSync(input: input, result: result);
		});
	}

	Function is rFind(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rFindSync(input: input, result: result);
		});
	}

	Function is rCaptures(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rCapturesSync(input: input, result: result);
		});
	}

	Function is rCount(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rCountSync(input: input, result: result);
		});
	}

	Function is rFindAll(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rFindAllSync(input: input, result: result);
		});
	}

	Function is rSplit(Str is input, Function is result, Int is limit: -1){
		ThreadScope:dispatch(task: local Function(){
			:rSplitSync(input: input, result: result, limit: limit);
		});
	}

	Function is rReplace(Str is input, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rReplaceStrSync(input: input, replacement: replacement, all: false, result: result);
		});
	}

	Function is rReplaceWith(Str is input, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rReplaceFnSync(input: input, replacer: replacer, all: false, result: result);
		});
	}

	Function is rReplaceAll(Str is input, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rReplaceStrSync(input: input, replacement: replacement, all: true, result: result);
		});
	}

	Function is rReplaceAllWith(Str is input, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:rReplaceFnSync(input: input, replacer: replacer, all: true, result: result);
		});
	}
}
