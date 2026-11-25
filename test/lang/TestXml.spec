#! specunit: suite

Class of SpecUnitTest is TestXml{
	replace [String] is namespace: ['test', 'lang'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', [Xml, XmlError, XmlNode]]
	];

	Function is testParseSimpleXml(){
		local Xml is x: Xml();
		local Result of XmlNode to XmlError is res: x:parse(input: '<?xml version="1.0"?><root id="42"><item flag=\'ok\'>Hello &amp; World</item><empty /></root>');
		local Boolean is ok: false;
		local XmlNode is root: XmlNode();
		match(on: res, when: [
			Result:Ok: local Function of Void(XmlNode is value){
				ok: true;
				root: value;
			},
			Result:Err: local Function of Void(SpecError of XmlError is _e){}
		]);
		Assert:isTrue(ok);
		Assert:isTrue(root:tag == 'root');
		Assert:isTrue(root:attr(name: 'id') == '42');
		Assert:isTrue(root:children:length() == 2);
		local XmlNode is item: root:firstByTag(tagName: 'item');
		Assert:isTrue(item:attr(name: 'flag') == 'ok');
		Assert:isTrue(item:textContent() == 'Hello & World');
	}

	Function is testMalformedXmlReturnsErr(){
		local Xml is x: Xml();
		local Result of XmlNode to XmlError is res: x:parse(input: '<root><open></wrong></root>');
		local Boolean is isErr: match(on: res, when: [
			Result:Ok: local Function of Boolean(XmlNode is _v){ return false; },
			Result:Err: local Function of Boolean(SpecError of XmlError is _e){ return true; }
		]);
		Assert:isTrue(isErr);
		local XmlNode is empty: x:parseOrEmpty(input: '<unclosed>');
		Assert:isTrue(empty:tag == '');
	}

	Function is testParseHtmlAndVisibleText(){
		local Xml is x: Xml();
		local String is html: '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spec Docs</title><style>body { color: red; }</style></head><body><h1>Welcome</h1><p>Use <code>match</code> &amp; <b>closures</b>.</p><script>var secret = 1;</script></body></html>';
		local XmlNode is doc: x:parseHtml(input: html);
		local XmlNode is titleNode: doc:firstByTag(tagName: 'title');
		Assert:isTrue(titleNode:visibleText() == 'Spec Docs');
		local String is bodyText: doc:firstByTag(tagName: 'body'):visibleText();
		Assert:isTrue(bodyText:contains(needle: 'Welcome'));
		Assert:isTrue(bodyText:contains(needle: 'Use match & closures .'));
		Assert:isFalse(bodyText:contains(needle: 'secret'));
		Assert:isFalse(bodyText:contains(needle: 'color: red'));
	}
}
