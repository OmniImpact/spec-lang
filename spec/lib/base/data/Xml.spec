#! Package base:data
#! XML and HTML DOM parser producing [XmlNode] trees.

Class is Xml{
	replace [String] is namespace: ['base', 'data'];

	replace [[String]] is using: [
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', XmlError],
		['base', 'data', XmlNode],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is pos: 0;
	local Int is len: 0;
	local Boolean is htmlMode: false;

	local Function is fail(String is msg){
		:raiseError(error: SpecError:init(kind: XmlError:SYNTAX_ERROR, description: msg));
	}

	local Function of Boolean is isSpace(String is ch){
		return ch == ' ' || ch == "\t" || ch == "\n" || ch == "\r";
	}

	local Function of Boolean is isNameChar(String is ch){
		if({ ch == '' }, { return false; });
		return !isSpace(ch: ch) && ch != '>' && ch != '<' && ch != '/' && ch != '=' && ch != '"' && ch != '\'';
	}

	local Function of Boolean is isVoidHtmlTag(String is tag){
		local String is lt: tag:toLower();
		return lt == 'meta' || lt == 'link' || lt == 'br' || lt == 'hr'
			|| lt == 'img' || lt == 'input' || lt == 'source' || lt == 'area'
			|| lt == 'base' || lt == 'col' || lt == 'embed' || lt == 'param'
			|| lt == 'track' || lt == 'wbr';
	}

	local Function is skipSpaces(String is src){
		while({ pos < len && isSpace(ch: src:charAt(index: pos, default: '')) }, {
			pos++;
		});
	}

	local Function of String is decodeEntities(String is raw){
		if({ !raw:contains(needle: '&') }, { return raw; });
		local String is out: '';
		local Int is n: raw:length();
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: raw:charAt(index: i, default: '');
			if({ ch == '&' }, {
				local Int is semi: raw:indexOfFrom(search: ';', from: i + 1, default: -1);
				if({ semi > i + 1 && semi - i <= 12 }, {
					local String is ent: raw:substring(start: i + 1, end: semi);
					local String is decoded: match(on: ent, when: [
						'amp': { '&' },
						'lt': { '<' },
						'gt': { '>' },
						'quot': { '"' },
						'apos': { '\'' },
						'nbsp': { ' ' },
						else: { '' }
					]);
					if({ decoded != '' }, {
						out: out . decoded;
						i: semi + 1;
					}, {
						if({ ent:startsWith(prefix: '#x') || ent:startsWith(prefix: '#X') }, {
							local Int is cp: ent:substring(start: 2, end: ent:length()):parseInt(base: 16, default: -1);
							if({ cp >= 32 && cp < 127 }, {
								out: out . String:fromCharCode(code: cp);
								i: semi + 1;
							}, {
								out: out . ch;
								i++;
							});
						}, {
							if({ ent:startsWith(prefix: '#') }, {
								local Int is cp: ent:substring(start: 1, end: ent:length()):parseInt(default: -1);
								if({ cp >= 32 && cp < 127 }, {
									out: out . String:fromCharCode(code: cp);
									i: semi + 1;
								}, {
									out: out . ch;
									i++;
								});
							}, {
								out: out . ch;
								i++;
							});
						});
					});
				}, {
					out: out . ch;
					i++;
				});
			}, {
				out: out . ch;
				i++;
			});
		});
		return out;
	}

	local Function of String is readName(String is src){
		local Int is start: pos;
		while({ pos < len && isNameChar(ch: src:charAt(index: pos, default: '')) }, {
			pos++;
		});
		return src:substring(start: start, end: pos);
	}

	local Function is skipMisc(String is src){
		local Boolean is progressed: true;
		while({ progressed && pos < len }, {
			progressed: false;
			skipSpaces(src: src);
			if({ pos + 4 <= len && src:substring(start: pos, end: pos + 4) == '<!--' }, {
				local Int is endC: src:indexOfFrom(search: '-->', from: pos + 4, default: -1);
				if({ endC < 0 }, {
					if({ !htmlMode }, { fail(msg: 'Unterminated XML comment'); });
					pos: len;
				}, {
					pos: endC + 3;
				});
				progressed: true;
			}, {
				if({ pos + 2 <= len && src:substring(start: pos, end: pos + 2) == '<?' }, {
					local Int is endP: src:indexOfFrom(search: '?>', from: pos + 2, default: -1);
					if({ endP < 0 }, {
						if({ !htmlMode }, { fail(msg: 'Unterminated processing instruction'); });
						pos: len;
					}, {
						pos: endP + 2;
					});
					progressed: true;
				}, {
					if({ pos + 2 <= len && src:substring(start: pos, end: pos + 2) == '<!' && !(pos + 9 <= len && src:substring(start: pos, end: pos + 9) == '<![CDATA[') }, {
						local Int is endD: src:indexOfFrom(search: '>', from: pos + 2, default: -1);
						if({ endD < 0 }, {
							if({ !htmlMode }, { fail(msg: 'Unterminated declaration'); });
							pos: len;
						}, {
							pos: endD + 1;
						});
						progressed: true;
					});
				});
			});
		});
	}

	local Function is parseAttributes(String is src, XmlNode is node){
		while({ pos < len }, {
			skipSpaces(src: src);
			if({ pos >= len }, { return; });
			local String is ch: src:charAt(index: pos, default: '');
			if({ ch == '>' || ch == '/' }, { return; });
			local String is attrName: readName(src: src);
			if({ attrName == '' }, {
				if({ !htmlMode }, { fail(msg: 'Invalid attribute name at offset ' . (pos as String)); });
				pos++;
			}, {
				skipSpaces(src: src);
				if({ pos < len && src:charAt(index: pos, default: '') == '=' }, {
					pos++;
					skipSpaces(src: src);
					local String is val: '';
					if({ pos < len }, {
						local String is q: src:charAt(index: pos, default: '');
						if({ q == '"' || q == '\'' }, {
							pos++;
							local Int is endQ: src:indexOfFrom(search: q, from: pos, default: -1);
							if({ endQ < 0 }, {
								if({ !htmlMode }, { fail(msg: 'Unterminated attribute value'); });
								val: decodeEntities(raw: src:substring(start: pos, end: len));
								pos: len;
							}, {
								val: decodeEntities(raw: src:substring(start: pos, end: endQ));
								pos: endQ + 1;
							});
						}, {
							local Int is vStart: pos;
							while({ pos < len && !isSpace(ch: src:charAt(index: pos, default: '')) && src:charAt(index: pos, default: '') != '>' }, {
								pos++;
							});
							val: decodeEntities(raw: src:substring(start: vStart, end: pos));
						});
					});
					node:attrs:set(key: attrName, value: val);
				}, {
					node:attrs:set(key: attrName, value: '');
				});
			});
		});
	}

	local Function of XmlNode is parseElement(String is src, [String] is openStack){
		pos++; # skip '<'
		local String is tag: readName(src: src);
		if({ tag == '' }, {
			if({ !htmlMode }, { fail(msg: 'Expected tag name at offset ' . (pos as String)); });
			return XmlNode();
		});
		local XmlNode is node: XmlNode:element(tag: tag);
		parseAttributes(src: src, node: node);
		skipSpaces(src: src);
		local Boolean is selfClosing: false;
		if({ pos < len && src:charAt(index: pos, default: '') == '/' }, {
			selfClosing: true;
			pos++;
		});
		if({ pos < len && src:charAt(index: pos, default: '') == '>' }, {
			pos++;
		}, {
			if({ !htmlMode }, { fail(msg: 'Expected \'>\' for tag <' . tag . '>'); });
		});

		if({ selfClosing || (htmlMode && isVoidHtmlTag(tag: tag)) }, {
			return node;
		});

		local String is tagLower: tag:toLower();
		if({ htmlMode && (tagLower == 'script' || tagLower == 'style') }, {
			local String is closeTag: '</' . tagLower . '>';
			local String is lowerSlice: src:substring(start: pos, end: len):toLower();
			local Int is endIdx: lowerSlice:indexOf(search: closeTag, default: -1);
			if({ endIdx >= 0 }, {
				local String is rawBody: src:substring(start: pos, end: pos + endIdx);
				if({ rawBody != '' }, {
					node:addChild(node: XmlNode:textNode(text: rawBody));
				});
				pos: pos + endIdx + closeTag:length();
			}, {
				pos: len;
			});
			return node;
		});

		openStack:push(item: tag);
		local Boolean is done: false;
		while({ !done && pos < len }, {
			local String is ch: src:charAt(index: pos, default: '');
			if({ ch == '<' }, {
				if({ pos + 9 <= len && src:substring(start: pos, end: pos + 9) == '<![CDATA[' }, {
					local Int is endCd: src:indexOfFrom(search: ']]>', from: pos + 9, default: -1);
					if({ endCd < 0 }, {
						if({ !htmlMode }, { fail(msg: 'Unterminated CDATA section'); });
						node:addChild(node: XmlNode:textNode(text: src:substring(start: pos + 9, end: len)));
						pos: len;
					}, {
						node:addChild(node: XmlNode:textNode(text: src:substring(start: pos + 9, end: endCd)));
						pos: endCd + 3;
					});
				}, {
					if({ pos + 4 <= len && src:substring(start: pos, end: pos + 4) == '<!--' }, {
						skipMisc(src: src);
					}, {
						if({ pos + 2 <= len && src:substring(start: pos, end: pos + 2) == '</' }, {
							local Int is savePos: pos;
							pos: pos + 2;
							local String is closeName: readName(src: src);
							skipSpaces(src: src);
							if({ pos < len && src:charAt(index: pos, default: '') == '>' }, {
								pos++;
							});
							if({ closeName == tag || (htmlMode && closeName:toLower() == tagLower) }, {
								openStack:pop();
								done: true;
							}, {
								if({ !htmlMode }, {
									fail(msg: 'Mismatched closing tag </' . closeName . '>, expected </' . tag . '>');
								});
								# HTML mode: if closeName matches an ancestor, rewind and let ancestor close
								local Boolean is matchesAncestor: false;
								local String is closeLower: closeName:toLower();
								times(count: openStack:length(), worker: local Function(Int is si){
									if({ openStack:get(index: si):toLower() == closeLower }, {
										matchesAncestor: true;
									});
								});
								if({ matchesAncestor }, {
									pos: savePos;
									openStack:pop();
									done: true;
								});
							});
						}, {
							if({ pos + 2 <= len && (src:substring(start: pos, end: pos + 2) == '<?' || src:substring(start: pos, end: pos + 2) == '<!') }, {
								skipMisc(src: src);
							}, {
								local XmlNode is child: parseElement(src: src, openStack: openStack);
								if({ child:tag != '' }, {
									node:addChild(node: child);
								});
							});
						});
					});
				});
			}, {
				local Int is nextLt: src:indexOfFrom(search: '<', from: pos, default: -1);
				local Int is tEnd: if({ nextLt < 0 }, { len }, { nextLt });
				local String is txt: decodeEntities(raw: src:substring(start: pos, end: tEnd));
				if({ txt != '' }, {
					node:addChild(node: XmlNode:textNode(text: txt));
				});
				pos: tEnd;
			});
		});

		if({ !done }, {
			if({ !htmlMode }, {
				fail(msg: 'Unclosed tag <' . tag . '>');
			});
			if({ openStack:length() > 0 }, { openStack:pop(); });
		});
		return node;
	}

	local Function of XmlNode is parseInternal(String is input, Boolean is isHtml){
		:pos: 0;
		:len: input:length();
		:htmlMode: isHtml;
		skipMisc(src: input);
		if({ pos >= len }, {
			if({ !isHtml }, { fail(msg: 'Empty XML input'); });
			return XmlNode:element(tag: 'document');
		});
		if({ isHtml }, {
			local XmlNode is doc: XmlNode:element(tag: 'document');
			local [String] is stack: [];
			while({ pos < len }, {
				skipMisc(src: input);
				if({ pos < len }, {
					if({ input:charAt(index: pos, default: '') == '<' }, {
						if({ pos + 2 <= len && input:substring(start: pos, end: pos + 2) == '</' }, {
							local Int is endC: input:indexOfFrom(search: '>', from: pos + 2, default: -1);
							pos: if({ endC < 0 }, { len }, { endC + 1 });
						}, {
							local XmlNode is el: parseElement(src: input, openStack: stack);
							if({ el:tag != '' }, { doc:addChild(node: el); });
						});
					}, {
						local Int is nextLt: input:indexOfFrom(search: '<', from: pos, default: -1);
						local Int is tEnd: if({ nextLt < 0 }, { len }, { nextLt });
						local String is txt: decodeEntities(raw: input:substring(start: pos, end: tEnd));
						if({ txt:trim() != '' }, { doc:addChild(node: XmlNode:textNode(text: txt)); });
						pos: tEnd;
					});
				});
			});
			if({ doc:children:length() == 1 }, {
				return doc:children:get(index: 0);
			});
			return doc;
		});

		local [String] is stack: [];
		if({ input:charAt(index: pos, default: '') != '<' }, {
			fail(msg: 'Expected root XML element');
		});
		local XmlNode is root: parseElement(src: input, openStack: stack);
		skipMisc(src: input);
		if({ pos < len }, {
			fail(msg: 'Unexpected trailing content at offset ' . (pos as String));
		});
		return root;
	}

	## Parses strict XML [input], returning `Result:Ok(XmlNode)` or `Result:Err(SpecError of XmlError)`.
	Function of Result of XmlNode to XmlError is parse(String is input){
		local SpecError of XmlError is failErr: SpecError:init(kind: XmlError:SYNTAX_ERROR, description: '');
		local XmlNode is root: try(
			body: local Function of XmlNode(){
				return :parseInternal(input: input, isHtml: false);
			},
			guard: local Function of XmlNode(SpecError of XmlError is err){
				failErr: err;
				return XmlNode();
			}
		);
		if({ failErr:description == '' }, {
			local Result of XmlNode to XmlError is okR: Result:Ok(value: root);
			return okR;
		});
		local Result of XmlNode to XmlError is errR: Result:Err(error: failErr);
		return errR;
	}

	## Parses strict XML [input], returning an empty [XmlNode] on syntax error.
	Function of XmlNode is parseOrEmpty(String is input){
		return try({
			:parseInternal(input: input, isHtml: false)
		}, guard: local Function of XmlNode(SpecError is _err){
			XmlNode()
		});
	}

	## Parses HTML5-style [input] leniently (void tags, raw script/style, unclosed tags) into an [XmlNode] tree.
	Function of XmlNode is parseHtml(String is input){
		return parseInternal(input: input, isHtml: true);
	}
}
