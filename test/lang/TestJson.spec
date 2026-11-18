#! specunit: suite
#! Comprehensive unit test suite for native JSON library (base:data:Json).

Class of SpecUnitTest is TestJson{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'data', as Json()],
		['base', 'data', JsonNull],
		['base', 'data', JsonBool],
		['base', 'data', JsonNumber]
	];

	Function is testParsePrimitives(){
		local Any is numVal: Json:parse(text: '42');
		Assert:areEqualInt(42, (numVal as JsonNumber):toInt());

		local Any is negVal: Json:parse(text: '-100');
		Assert:areEqualInt(-100, (negVal as JsonNumber):toInt());

		local Any is trueVal: Json:parse(text: 'true');
		Assert:isTrue((trueVal as JsonBool):value());

		local Any is falseVal: Json:parse(text: 'false');
		Assert:isFalse((falseVal as JsonBool):value());

		local Any is nullVal: Json:parse(text: 'null');
		Assert:isTrue(Json:isNull(value: nullVal));
	}

	Function is testParseStrings(){
		local Any is s1: Json:parse(text: '"hello world"');
		Assert:areEqualString('hello world', Json:asString(val: s1));

		local Any is s2: Json:parse(text: '"line1\\nline2\\t\\"quoted\\"\\\\slash"');
		Assert:areEqualString("line1\nline2\t\"quoted\"\\slash", Json:asString(val: s2));

		local Any is s3: Json:parse(text: '"caf\\u00e9"');
		Assert:areEqualString('café', Json:asString(val: s3));
	}

	Function is testParseArray(){
		local Any is emptyArr: Json:parse(text: '[]');
		Assert:areEqualInt(0, (emptyArr as Array):length());

		local Any is arrVal: Json:parse(text: '[1, "two", true, null]');
		local Array is arr: arrVal as Array;
		Assert:areEqualInt(4, arr:length());
		Assert:areEqualInt(1, Json:getIntAt(arr: arr, index: 0));
		Assert:areEqualString('two', Json:getStringAt(arr: arr, index: 1));
		Assert:isTrue(Json:getBoolAt(arr: arr, index: 2));
		Assert:isTrue(Json:isNull(value: arr:get(index: 3, default: '')));
	}

	Function is testParseObject(){
		local String is src: '{"name": "Spec", "version": "0.1.0", "cores": 16, "debug": true, "extra": null}';
		local Any is objVal: Json:parse(text: src);
		local Map is obj: objVal as Map;

		Assert:areEqualString('Spec', Json:getString(obj: obj, key: 'name'));
		Assert:areEqualString('0.1.0', Json:getString(obj: obj, key: 'version'));
		Assert:areEqualInt(16, Json:getInt(obj: obj, key: 'cores'));
		Assert:isTrue(Json:getBool(obj: obj, key: 'debug'));
		Assert:isTrue(Json:isNull(value: obj:get(key: 'extra', default: '')));
	}

	Function is testParseNested(){
		local String is src: '{"compiler": {"name": "spec", "optLevel": 2}, "targets": ["c11", "x86_64"]}';
		local Map is root: Json:parseObjectText(text: src);

		local Map is comp: Json:getObject(obj: root, key: 'compiler');
		Assert:areEqualString('spec', Json:getString(obj: comp, key: 'name'));
		Assert:areEqualInt(2, Json:getInt(obj: comp, key: 'optLevel'));

		local Array is targets: Json:getArray(obj: root, key: 'targets');
		Assert:areEqualInt(2, targets:length());
		Assert:areEqualString('c11', Json:getStringAt(arr: targets, index: 0));
		Assert:areEqualString('x86_64', Json:getStringAt(arr: targets, index: 1));
	}

	Function is testStringify(){
		local Map is m: Map:init();
		m:set(key: 'name', value: 'Spec');
		m:set(key: 'cores', value: Json:number(n: 8));
		m:set(key: 'active', value: Json:bool(b: true));
		m:set(key: 'parent', value: Json:nullValue());

		local String is s: Json:stringify(value: m);
		Assert:isTrue(s:contains(needle: '"name":"Spec"'));
		Assert:isTrue(s:contains(needle: '"cores":8'));
		Assert:isTrue(s:contains(needle: '"active":true'));
		Assert:isTrue(s:contains(needle: '"parent":null'));
	}

	Function is testFormat(){
		local Map is m: Map:init();
		m:set(key: 'name', value: 'my_app');
		m:set(key: 'ver', value: '1.0');

		local String is formatted: Json:format(value: m, indent: 2);
		Assert:isTrue(formatted:startsWith(prefix: "{\n"));
		Assert:isTrue(formatted:endsWith(suffix: "\n}"));
		Assert:isTrue(formatted:contains(needle: '  "name": "my_app"'));
		Assert:isTrue(formatted:contains(needle: '  "ver": "1.0"'));
	}

	Function is testMalformedJson(){
		local Any is bad1: Json:parse(text: '{ invalid json }', default: 'fallback');
		Assert:areEqualString('fallback', Json:asString(val: bad1));
		Assert:isTrue(Json:hasError());
		Assert:isTrue(Json:errorMessage():length() > 0);

		local Any is bad2: Json:parse(text: '[1, 2,', default: 'bad_array');
		Assert:areEqualString('bad_array', Json:asString(val: bad2));
		Assert:isTrue(Json:hasError());
	}

	Function is testRoundTrip(){
		local String is original: '{"app": "speclsp", "count": 100, "flag": false, "items": ["a", "b"]}';
		local Any is parsed: Json:parse(text: original);
		local String is serialized: Json:stringify(value: parsed);
		local Any is reParsed: Json:parse(text: serialized);
		local Map is m: reParsed as Map;

		Assert:areEqualString('speclsp', Json:getString(obj: m, key: 'app'));
		Assert:areEqualInt(100, Json:getInt(obj: m, key: 'count'));
		Assert:isFalse(Json:getBool(obj: m, key: 'flag'));
		local Array is items: Json:getArray(obj: m, key: 'items');
		Assert:areEqualInt(2, items:length());
		Assert:areEqualString('a', Json:getStringAt(arr: items, index: 0));
		Assert:areEqualString('b', Json:getStringAt(arr: items, index: 1));
	}
}
