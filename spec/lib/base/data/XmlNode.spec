#! Package base:data
#! DOM node representation for parsed XML and HTML documents.

Class is XmlNode{
	replace [String] is namespace: ['base', 'data'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is tag: '';
	String is text: '';
	Boolean is isText: false;
	Map of String to String is attrs: Map:init();
	[XmlNode] is children: [];

	replace Function is init(String is tag: '', String is text: '', Boolean is isText: false){
		:tag: tag;
		:text: text;
		:isText: isText;
	}

	## Creates a text node holding [text].
	held Function of XmlNode is textNode(String is text){
		return XmlNode(tag: '', text: text, isText: true);
	}

	## Creates an element node with [tag].
	held Function of XmlNode is element(String is tag){
		return XmlNode(tag: tag, text: '', isText: false);
	}

	## Returns the attribute value for [name], or [default] if absent.
	Function of String is attr(String is name, String is default: ''){
		return attrs:getString(key: name, default: default);
	}

	## True when attribute [name] is present on this node.
	Function of Boolean is hasAttr(String is name){
		return attrs:has(key: name);
	}

	## Appends a child [node] to this element.
	Function is addChild(XmlNode is node){
		children:push(item: node);
	}

	local Function is collectText(Boolean is skipInvisible, Array of String is parts){
		if({ isText }, {
			if({ text != '' }, { parts:add(item: text); });
			return;
		});
		if({ skipInvisible }, {
			local String is lt: tag:toLower();
			if({ lt == 'script' || lt == 'style' || lt == 'noscript' }, {
				return;
			});
		});
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):collectText(skipInvisible: skipInvisible, parts: parts);
		});
	}

	## Returns all concatenated text content under this node.
	Function of String is textContent(){
		local Array of String is parts: Array();
		collectText(skipInvisible: false, parts: parts);
		return parts:join(separator: '');
	}

	## Returns normalized visible text under this node, skipping `<script>` and `<style>` blocks
	## and collapsing runs of whitespace into single spaces.
	Function of String is visibleText(){
		local Array of String is parts: Array();
		collectText(skipInvisible: true, parts: parts);
		local String is raw: parts:join(separator: ' ');
		local [String] is words: [];
		local String is cur: '';
		local Int is n: raw:length();
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: raw:charAt(index: i, default: '');
			if({ ch == ' ' || ch == "\t" || ch == "\n" || ch == "\r" }, {
				if({ cur != '' }, {
					words:push(item: cur);
					cur: '';
				});
			}, {
				cur: cur . ch;
			});
			i++;
		});
		if({ cur != '' }, { words:push(item: cur); });
		local Array of String is out: Array();
		times(count: words:length(), worker: local Function(Int is wi){
			out:add(item: words:get(index: wi));
		});
		return out:join(separator: ' ');
	}

	local Function is collectByTag(String is wantLower, [XmlNode] is out){
		if({ isText }, { return; });
		if({ tag:toLower() == wantLower }, {
			out:push(item: :);
		});
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):collectByTag(wantLower: wantLower, out: out);
		});
	}

	## Finds all descendant elements (including self) matching [tagName] (case-insensitive).
	Function of [XmlNode] is findByTag(String is tagName){
		local [XmlNode] is out: [];
		collectByTag(wantLower: tagName:toLower(), out: out);
		return out;
	}

	## Returns the first descendant element (including self) matching [tagName], or an empty node.
	Function of XmlNode is firstByTag(String is tagName){
		local [XmlNode] is hits: findByTag(tagName: tagName);
		if({ hits:length() > 0 }, { return hits:get(index: 0); });
		return XmlNode();
	}

	## Serializes this node and its subtree back to XML text.
	Function of String is toXmlString(){
		if({ isText }, { return text; });
		if({ tag == '' }, {
			local String is out: '';
			times(count: children:length(), worker: local Function(Int is i){
				out: out . children:get(index: i):toXmlString();
			});
			return out;
		});
		local String is out: '<' . tag;
		local Array of String is aKeys: attrs:keys();
		times(count: aKeys:length(), worker: local Function(Int is ai){
			local String is k: aKeys:get(index: ai, default: '');
			out: out . ' ' . k . '="' . attrs:getString(key: k, default: '') . '"';
		});
		if({ children:length() == 0 }, {
			return out . ' />';
		});
		out: out . '>';
		times(count: children:length(), worker: local Function(Int is i){
			out: out . children:get(index: i):toXmlString();
		});
		return out . '</' . tag . '>';
	}
}
