#! Package base:regex
#! Compiled, immutable, reusable Thompson NFA regular expression pattern (`ArexPattern`).

Class is ArexPattern{
	namespace: ['base', 'regex'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'struct', Array],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	# NFA opcodes:
	# 0 = SPLIT (epsilon to out1, out2)
	# 1 = LITERAL (arg1 = byte, to out1)
	# 2 = ANY (any byte except '\n', to out1)
	# 3 = CLASS (arg1 = classId, to out1)
	# 4 = ANCHOR_START (pos == 0, to out1)
	# 5 = ANCHOR_END (pos == inputLen, to out1)
	# 6 = MATCH (accepting)
	local Array of Int is ops: [];
	local Array of Int is arg1s: [];
	local Array of Int is out1s: [];
	local Array of Int is out2s: [];

	local Array of Int is classNegated: [];
	local Array of Int is classRangeCid: [];
	local Array of Int is classRangeLo: [];
	local Array of Int is classRangeHi: [];

	local Str is pat: '';
	local Int is pLen: 0;
	local Int is pos: 0;
	local Int is startState: 0;

	replace Function is init(){
		:ops: [];
		:arg1s: [];
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
	}

	## Compiles [pattern] into a reusable [ArexPattern].
	held Function of ArexPattern is compile(Str is pattern){
		local ArexPattern is compiled: ArexPattern:init();
		compiled:compilePattern(pattern: pattern);
		return compiled;
	}

	## Returns the original pattern source string.
	Function of Str is pattern(){
		return :pat;
	}

	local Function of Int is addNode(Int is op, Int is arg1, Int is out1, Int is out2){
		local Int is id: :ops:length();
		:ops:add(item: op);
		:arg1s:add(item: arg1);
		:out1s:add(item: out1);
		:out2s:add(item: out2);
		return id;
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
	}

	local Function is addSpaceRanges(Int is cid){
		:addClassRange(cid: cid, lo: 9, hi: 13);
		:addClassRange(cid: cid, lo: 32, hi: 32);
	}

	local Function of Boolean is classMatches(Int is cid, Int is b){
		local Int is n: :classRangeCid:length();
		local Boolean is hit: false;
		local Int is i: 0;
		while({ i < n }, {
			if({ :classRangeCid:get(index: i) == cid && b >= :classRangeLo:get(index: i) && b <= :classRangeHi:get(index: i) }, {
				hit: true;
				i: n;
			}, {
				i: i + 1;
			});
		});
		if({ :classNegated:get(index: cid) == 1 }, {
			return !hit;
		});
		return hit;
	}

	local Function of Array of Int is makeFrag(Int is start, Int is exit){
		local Array of Int is f: [];
		f:add(item: start);
		f:add(item: exit);
		return f;
	}

	local Function of Array of Int is emptyFrag(){
		local Int is s: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		return :makeFrag(start: s, exit: s);
	}

	local Function of Array of Int is singleNodeFrag(Int is op, Int is arg1){
		local Int is exit: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		local Int is start: :addNode(op: op, arg1: arg1, out1: exit, out2: -1);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is concatFrag(Array of Int is a, Array of Int is b){
		:out1s:set(index: a:get(index: 1), value: b:get(index: 0));
		return :makeFrag(start: a:get(index: 0), exit: b:get(index: 1));
	}

	local Function of Array of Int is altFrag(Array of Int is a, Array of Int is b){
		local Int is start: :addNode(op: 0, arg1: 0, out1: a:get(index: 0), out2: b:get(index: 0));
		local Int is exit: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		:out1s:set(index: a:get(index: 1), value: exit);
		:out1s:set(index: b:get(index: 1), value: exit);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is starFrag(Array of Int is a){
		local Int is exit: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		local Int is start: :addNode(op: 0, arg1: 0, out1: a:get(index: 0), out2: exit);
		:out1s:set(index: a:get(index: 1), value: start);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Array of Int is plusFrag(Array of Int is a){
		local Int is exit: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		local Int is loop: :addNode(op: 0, arg1: 0, out1: a:get(index: 0), out2: exit);
		:out1s:set(index: a:get(index: 1), value: loop);
		return :makeFrag(start: a:get(index: 0), exit: exit);
	}

	local Function of Array of Int is optFrag(Array of Int is a){
		local Int is exit: :addNode(op: 0, arg1: 0, out1: -1, out2: -1);
		local Int is start: :addNode(op: 0, arg1: 0, out1: a:get(index: 0), out2: exit);
		:out1s:set(index: a:get(index: 1), value: exit);
		return :makeFrag(start: start, exit: exit);
	}

	local Function of Int is unescapeChar(Int is b){
		if({ b == 110 }, { return 10; }); # \n
		if({ b == 114 }, { return 13; }); # \r
		if({ b == 116 }, { return 9; });  # \t
		return b;
	}

	local Function of Array of Int is parseEscapeAtom(){
		if({ :pos >= :pLen }, {
			return :singleNodeFrag(op: 1, arg1: 92);
		});
		local Int is b: :pat:byteAt(index: :pos);
		:pos: :pos + 1;
		if({ b == 100 || b == 68 }, { # \d, \D
			local Int is neg: 0;
			if({ b == 68 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addDigitRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid);
		});
		if({ b == 119 || b == 87 }, { # \w, \W
			local Int is neg: 0;
			if({ b == 87 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addWordRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid);
		});
		if({ b == 115 || b == 83 }, { # \s, \S
			local Int is neg: 0;
			if({ b == 83 }, { neg: 1; });
			local Int is cid: :newClass(negated: neg);
			:addSpaceRanges(cid: cid);
			return :singleNodeFrag(op: 3, arg1: cid);
		});
		return :singleNodeFrag(op: 1, arg1: :unescapeChar(b: b));
	}

	local Function of Int is readClassChar(){
		local Int is b: :pat:byteAt(index: :pos);
		:pos: :pos + 1;
		if({ b == 92 && :pos < :pLen }, {
			local Int is esc: :pat:byteAt(index: :pos);
			:pos: :pos + 1;
			return :unescapeChar(b: esc);
		});
		return b;
	}

	local Function of Array of Int is parseClassAtom(){
		local Int is negated: 0;
		if({ :pos < :pLen && :pat:byteAt(index: :pos) == 94 }, { # '^'
			negated: 1;
			:pos: :pos + 1;
		});
		local Int is cid: :newClass(negated: negated);
		local Boolean is first: true;
		while({ :pos < :pLen }, {
			local Int is b: :pat:byteAt(index: :pos);
			if({ b == 93 && !first }, { # ']'
				:pos: :pos + 1;
				return :singleNodeFrag(op: 3, arg1: cid);
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
							if({ :pos + 1 < :pLen && :pat:byteAt(index: :pos) == 45 && :pat:byteAt(index: :pos + 1) != 93 }, {
								:pos: :pos + 1;
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
				if({ :pos + 1 < :pLen && :pat:byteAt(index: :pos) == 45 && :pat:byteAt(index: :pos + 1) != 93 }, {
					:pos: :pos + 1;
					local Int is hi: :readClassChar();
					:addClassRange(cid: cid, lo: ch, hi: hi);
				}, {
					:addClassRange(cid: cid, lo: ch, hi: ch);
				});
			});
		});
		return :singleNodeFrag(op: 3, arg1: cid);
	}

	local Function of Array of Int is parseAtom(){
		local Int is b: :pat:byteAt(index: :pos);
		:pos: :pos + 1;
		if({ b == 40 }, { # '('
			local Array of Int is inner: :parseAlt();
			if({ :pos < :pLen && :pat:byteAt(index: :pos) == 41 }, {
				:pos: :pos + 1;
			});
			return inner;
		});
		if({ b == 91 }, { # '['
			return :parseClassAtom();
		});
		if({ b == 92 }, { # '\'
			return :parseEscapeAtom();
		});
		if({ b == 46 }, { # '.'
			return :singleNodeFrag(op: 2, arg1: 0);
		});
		if({ b == 94 }, { # '^'
			return :singleNodeFrag(op: 4, arg1: 0);
		});
		if({ b == 36 }, { # '$'
			return :singleNodeFrag(op: 5, arg1: 0);
		});
		return :singleNodeFrag(op: 1, arg1: b);
	}

	local Function of Array of Int is parseRepetitionSpan(Array of Int is baseFrag, Int is atomStart, Int is atomEnd){
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
		local Int is afterBracePos: :pos;

		local Array of Int is res: baseFrag;
		if({ minVal == 0 }, {
			res: :emptyFrag();
		});
		local Int is count: 1;
		while({ count < minVal }, {
			:pos: atomStart;
			local Array of Int is copy: :parseAtom();
			res: :concatFrag(a: res, b: copy);
			count: count + 1;
		});
		if({ unbounded }, {
			:pos: atomStart;
			local Array of Int is tail: :starFrag(a: :parseAtom());
			res: :concatFrag(a: res, b: tail);
		}, {
			local Int is optCount: minVal;
			if({ minVal == 0 }, { optCount: 0; });
			while({ optCount < maxVal }, {
				:pos: atomStart;
				local Array of Int is optCopy: :optFrag(a: :parseAtom());
				res: :concatFrag(a: res, b: optCopy);
				optCount: optCount + 1;
			});
		});
		:pos: afterBracePos;
		return res;
	}

	local Function of Array of Int is parseQuantified(){
		local Int is atomStart: :pos;
		local Array of Int is frag: :parseAtom();
		local Int is atomEnd: :pos;
		local Boolean is more: true;
		while({ more && :pos < :pLen }, {
			local Int is q: :pat:byteAt(index: :pos);
			if({ q == 42 }, { # '*'
				:pos: :pos + 1;
				frag: :starFrag(a: frag);
			}, {
				if({ q == 43 }, { # '+'
					:pos: :pos + 1;
					frag: :plusFrag(a: frag);
				}, {
					if({ q == 63 }, { # '?'
						:pos: :pos + 1;
						frag: :optFrag(a: frag);
					}, {
						if({ q == 123 }, { # '{'
							local Int is before: :pos;
							frag: :parseRepetitionSpan(baseFrag: frag, atomStart: atomStart, atomEnd: atomEnd);
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
				local Array of Int is nextFrag: :parseQuantified();
				if({ !hasOne }, {
					frag: nextFrag;
					hasOne: true;
				}, {
					frag: :concatFrag(a: frag, b: nextFrag);
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
		:pLen: pattern:length();
		:pos: 0;
		local Array of Int is root: :parseAlt();
		local Int is matchNode: :addNode(op: 6, arg1: 0, out1: -1, out2: -1);
		:out1s:set(index: root:get(index: 1), value: matchNode);
		:startState: root:get(index: 0);
	}

	local Function is addStateWithStart(
		Int is state,
		Int is threadStart,
		Int is pos,
		Int is inputLen,
		Array of Int is listStates,
		Array of Int is stateStarts,
		Array of Int is stamps,
		Int is stamp,
		Array of Int is stackStates,
		Array of Int is stackStarts
	){
		if({ state < 0 }, { return; });
		stackStates:clear();
		stackStarts:clear();
		stackStates:add(item: state);
		stackStarts:add(item: threadStart);
		while({ stackStates:length() > 0 }, {
			local Int is top: stackStates:length() - 1;
			local Int is s: stackStates:get(index: top);
			local Int is ts: stackStarts:get(index: top);
			stackStates:removeAt(index: top);
			stackStarts:removeAt(index: top);
			if({ s >= 0 }, {
				local Boolean is isNew: stamps:get(index: s) != stamp;
				local Boolean is improved: isNew || ts < stateStarts:get(index: s);
				if({ improved }, {
					stamps:set(index: s, value: stamp);
					stateStarts:set(index: s, value: ts);
					local Int is op: :ops:get(index: s);
					if({ op == 0 }, {
						local Int is o2: :out2s:get(index: s);
						local Int is o1: :out1s:get(index: s);
						if({ o2 >= 0 }, {
							stackStates:add(item: o2);
							stackStarts:add(item: ts);
						});
						if({ o1 >= 0 }, {
							stackStates:add(item: o1);
							stackStarts:add(item: ts);
						});
					}, {
						if({ op == 4 }, {
							if({ pos == 0 }, {
								local Int is o1: :out1s:get(index: s);
								if({ o1 >= 0 }, {
									stackStates:add(item: o1);
									stackStarts:add(item: ts);
								});
							});
						}, {
							if({ op == 5 }, {
								if({ pos == inputLen }, {
									local Int is o1: :out1s:get(index: s);
									if({ o1 >= 0 }, {
										stackStates:add(item: o1);
										stackStarts:add(item: ts);
									});
								});
							}, {
								if({ isNew }, {
									listStates:add(item: s);
								});
							});
						});
					});
				});
			});
		});
	}

	## Returns `[found(0|1), start, end]` for the leftmost-longest match in [input].
	Function of Array of Int is findFirstSync(Str is input){
		local Int is numStates: :ops:length();
		local Int is inLen: input:length();

		local Array of Int is currStates: [];
		local Array of Int is nextStates: [];
		local Array of Int is currStarts: [];
		local Array of Int is nextStarts: [];
		local Array of Int is currStamps: [];
		local Array of Int is nextStamps: [];
		local Array of Int is stackStates: [];
		local Array of Int is stackStarts: [];

		local Int is i: 0;
		while({ i < numStates }, {
			currStarts:add(item: 0);
			nextStarts:add(item: 0);
			currStamps:add(item: 0);
			nextStamps:add(item: 0);
			i: i + 1;
		});

		local Int is currStamp: 1;
		local Int is nextStamp: 1;
		local Boolean is found: false;
		local Int is bestStart: -1;
		local Int is bestEnd: -1;

		local Int is idx: 0;
		while({ idx <= inLen }, {
			if({ !found }, {
				:addStateWithStart(
					state: :startState,
					threadStart: idx,
					pos: idx,
					inputLen: inLen,
					listStates: currStates,
					stateStarts: currStarts,
					stamps: currStamps,
					stamp: currStamp,
					stackStates: stackStates,
					stackStarts: stackStarts
				);
			});

			local Int is minActiveStart: inLen + 1;
			local Int is k: 0;
			while({ k < currStates:length() }, {
				local Int is s: currStates:get(index: k);
				local Int is ts: currStarts:get(index: s);
				if({ ts < minActiveStart }, {
					minActiveStart: ts;
				});
				if({ :ops:get(index: s) == 6 }, {
					if({ !found || ts < bestStart || (ts == bestStart && idx > bestEnd) }, {
						found: true;
						bestStart: ts;
						bestEnd: idx;
					});
				});
				k: k + 1;
			});

			if({ found && minActiveStart > bestStart }, {
				idx: inLen + 1;
			}, {
				if({ idx < inLen }, {
					local Int is b: input:byteAt(index: idx);
					nextStamp: nextStamp + 1;
					nextStates:clear();
					k: 0;
					while({ k < currStates:length() }, {
						local Int is s: currStates:get(index: k);
						local Int is op: :ops:get(index: s);
						local Boolean is matched: false;
						if({ op == 1 }, {
							matched: b == :arg1s:get(index: s);
						}, {
							if({ op == 2 }, {
								matched: b != 10;
							}, {
								if({ op == 3 }, {
									matched: :classMatches(cid: :arg1s:get(index: s), b: b);
								});
							});
						});
						if({ matched }, {
							:addStateWithStart(
								state: :out1s:get(index: s),
								threadStart: currStarts:get(index: s),
								pos: idx + 1,
								inputLen: inLen,
								listStates: nextStates,
								stateStarts: nextStarts,
								stamps: nextStamps,
								stamp: nextStamp,
								stackStates: stackStates,
								stackStarts: stackStarts
							);
						});
						k: k + 1;
					});
					currStamp: currStamp + 1;
					currStates:clear();
					k: 0;
					while({ k < nextStates:length() }, {
						local Int is ns: nextStates:get(index: k);
						currStates:add(item: ns);
						currStarts:set(index: ns, value: nextStarts:get(index: ns));
						currStamps:set(index: ns, value: currStamp);
						k: k + 1;
					});
				});
				idx: idx + 1;
			});
		});

		local Int is foundInt: 0;
		if({ found }, { foundInt: 1; });
		local Array of Int is res: [];
		res:add(item: foundInt);
		res:add(item: bestStart);
		res:add(item: bestEnd);
		return res;
	}

	## Runs `test` synchronously on the calling thread and invokes [result].
	Function is testSync(Str is input, Function is result){
		local Array of Int is matchRes: :findFirstSync(input: input);
		local Boolean is matched: matchRes:get(index: 0) == 1;
		result(matched);
	}

	## Runs `find` synchronously on the calling thread and invokes [result].
	Function is findSync(Str is input, Function is result){
		local Array of Int is matchRes: :findFirstSync(input: input);
		local Boolean is found: matchRes:get(index: 0) == 1;
		local Int is start: matchRes:get(index: 1);
		local Int is end: matchRes:get(index: 2);
		local Str is matchedText: '';
		if({ found }, {
			matchedText: input:substring(start: start, end: end);
		});
		result(found, matchedText, start, end);
	}

	## Tests whether [input] matches this compiled pattern and invokes [result] with a `Boolean`.
	## Runs asynchronously inside an active `ThreadScope:open`, or waits if called outside one.
	Function is test(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:testSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of this compiled pattern in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is find(Str is input, Function is result){
		ThreadScope:dispatch(task: local Function(){
			:findSync(input: input, result: result);
		});
	}
}
