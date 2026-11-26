#! Package specedit:model
#! Persistent SpecEdit user settings stored in the default config directory.

Class is SettingsModel{
	replace [String] is namespace: ['specedit', 'model'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', Dir],
		['base', 'sys', Uri],
		['base', 'struct', Map],
		['base', 'core', Result],
		['base', 'data', Json],
		['base', 'data', JsonNumber],
		['base', 'data', JsonBool],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset]
	];

	ThemePreset is themePreset: ThemePreset:LIGHT;
	Float is docTextDeltaPt: 0.0;
	Float is baseTextPt: 12.0;
	Int is uiZoomPct: 100;
	Boolean is defaultMonospace: false;
	Boolean is defaultWrap: false;
	Boolean is defaultShowFileTree: true;

	Function of String is configPath(){
		local Uri is u: Uri();
		local String is appDir: u:appConfigDir(appName: 'spec');
		if({ Dir():isDir(path: appDir) }, {
			return appDir . '/specedit.json';
		});
		return u:configDir() . '/specedit_settings.json';
	}

	Function of Float is zoomFactor(){
		return (uiZoomPct as Float) / 100.0;
	}

	Function is load(){
		local String is raw: fileRead(
			path: :configPath(),
			onSuccess: local Function(String is _s){},
			onError: local Function(Any is _err){},
			default: ''
		);
		if({ raw == '' }, { return; });
		local Json is j: Json();
		local Map of String to Any is obj: Map:init();
		match(on: j:parseMapResult(text: raw), when: [
			Result:Ok: local Function(Map of String to Any is m){ obj: m; }
		], default: {});
		local String is presetStr: j:getString(obj: obj, key: 'theme', default: 'light');
		:themePreset: Theme:presetFromString(name: presetStr);
		:docTextDeltaPt: j:getFloat(obj: obj, key: 'docTextDeltaPt', default: 0.0);
		local Float is bpt: j:getFloat(obj: obj, key: 'baseTextPt', default: 12.0);
		:baseTextPt: if({ bpt < 8.0 }, { 8.0 }, { if({ bpt > 20.0 }, { 20.0 }, { bpt }) });
		local Int is zp: j:getInt(obj: obj, key: 'uiZoomPct', default: 100);
		if({ zp == 70 || zp == 100 || zp == 115 || zp == 130 }, {
			:uiZoomPct: zp;
		}, {
			:uiZoomPct: 100;
		});
		:defaultMonospace: j:getBool(obj: obj, key: 'defaultMonospace', default: false);
		:defaultWrap: j:getBool(obj: obj, key: 'defaultWrap', default: false);
		:defaultShowFileTree: j:getBool(obj: obj, key: 'defaultShowFileTree', default: true);
	}

	Function is save(){
		local Map of String to Any is obj: Map:init();
		obj:set(key: 'theme', value: Theme:presetId(preset: themePreset));
		obj:set(key: 'docTextDeltaPt', value: JsonNumber(rawText: docTextDeltaPt as String, isFloating: true));
		obj:set(key: 'baseTextPt', value: JsonNumber(rawText: baseTextPt as String, isFloating: true));
		obj:set(key: 'uiZoomPct', value: JsonNumber(rawText: uiZoomPct as String, isFloating: false));
		obj:set(key: 'defaultMonospace', value: JsonBool(value: defaultMonospace));
		obj:set(key: 'defaultWrap', value: JsonBool(value: defaultWrap));
		obj:set(key: 'defaultShowFileTree', value: JsonBool(value: defaultShowFileTree));
		local String is jsonStr: Json():format(value: obj, indent: 2) . "\n";
		fileWrite(
			path: :configPath(),
			content: jsonStr,
			onSuccess: local Function(Int is _n){},
			onError: local Function(Any is _err){}
		);
	}
}