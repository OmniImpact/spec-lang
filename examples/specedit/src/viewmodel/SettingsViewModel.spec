#! Package specedit:viewmodel
#! ViewModel for the SpecEdit Settings dialog (Appearance, Locations, Interface).

Class is SettingsViewModel{
	replace [String] is namespace: ['specedit', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['base', 'wardrobe', 'file', FilePinnedLocations],
		['specedit', 'model', SettingsModel]
	];

	SettingsModel is model: SettingsModel();
	FilePinnedLocations is pinned: FilePinnedLocations();
	BoolEmitter is open: BoolEmitter(initial: false);
	TextEmitter is selectedRoute: TextEmitter(initial: 'appearance');

	Function is themeChangeHandler: local Function(Theme is _t){};
	Function is zoomChangeHandler: local Function(Float is _z){};
	Function is docDeltaHandler: local Function(Float is _d){};
	Function is pinnedChangeHandler: local Function(){};
	Function is defaultsChangeHandler: local Function(Boolean is _mono, Boolean is _wrap, Boolean is _tree){};
	Function is viewRefreshHandler: local Function(){};
	Function of String is activeDirProvider: local Function of String(){ '' };
	Function of String is activeFileProvider: local Function of String(){ '' };

	replace Function is init(){
		:model: SettingsModel();
		:model:load();
		:pinned: FilePinnedLocations();
		:pinned:load();
	}

	Function is bindHandlers(
		Function is onThemeChange,
		Function is onZoomChange,
		Function is onDocTextDeltaChange,
		Function is onPinnedChange,
		Function is onDefaultsChange,
		Function of String is getActiveDir,
		Function of String is getActiveFile
	){
		:themeChangeHandler: onThemeChange;
		:zoomChangeHandler: onZoomChange;
		:docDeltaHandler: onDocTextDeltaChange;
		:pinnedChangeHandler: onPinnedChange;
		:defaultsChangeHandler: onDefaultsChange;
		:activeDirProvider: getActiveDir;
		:activeFileProvider: getActiveFile;
	}

	Function is bindViewRefresh(Function is onRefresh){
		:viewRefreshHandler: onRefresh;
	}

	local Function is notifyRefresh(){
		local Function is cb: viewRefreshHandler;
		cb();
	}

	Function of Theme is currentTheme(){
		return Theme:forPreset(preset: model:themePreset, baseTextPt: model:baseTextPt);
	}

	Function is openSettings(){
		pinned:load();
		open:emit(value: true);
		:notifyRefresh();
	}

	Function is closeSettings(){
		open:emit(value: false);
	}

	Function is selectRoute(String is routeName){
		if({ routeName != 'appearance' && routeName != 'locations' && routeName != 'interface' }, { return; });
		selectedRoute:emit(value: routeName);
		:notifyRefresh();
	}

	Function is selectTheme(ThemePreset is preset){
		model:themePreset: preset;
		model:save();
		local Function is cb: themeChangeHandler;
		cb(:currentTheme());
		:notifyRefresh();
	}

	Function is adjustDocTextDelta(Float is delta){
		local Float is next: model:docTextDeltaPt + delta;
		if({ next < -6.0 }, { next: -6.0; });
		if({ next > 16.0 }, { next: 16.0; });
		model:docTextDeltaPt: next;
		model:save();
		local Function is cb: docDeltaHandler;
		cb(next);
		:notifyRefresh();
	}

	Function is adjustBaseTextPt(Float is delta){
		local Float is next: model:baseTextPt + delta;
		if({ next < 10.0 }, { next: 10.0; });
		if({ next > 22.0 }, { next: 22.0; });
		model:baseTextPt: next;
		model:save();
		local Function is cb: themeChangeHandler;
		cb(:currentTheme());
		:notifyRefresh();
	}

	Function is selectZoomPct(Int is pct){
		if({ pct != 70 && pct != 100 && pct != 115 && pct != 130 }, { return; });
		model:uiZoomPct: pct;
		model:save();
		local Function is cb: zoomChangeHandler;
		cb(model:zoomFactor());
		:notifyRefresh();
	}

	Function is removePinned(Int is index){
		if({ pinned:removeAt(index: index) }, {
			pinned:save();
			local Function is cb: pinnedChangeHandler;
			cb();
			:notifyRefresh();
		});
	}

	local Function of String is baseNameOf(String is path){
		local Int is len: path:length();
		local Int is i: len - 1;
		while({ i >= 0 }, {
			local String is ch: path:substring(start: i, end: i + 1);
			if({ ch == '/' || ch == '\\' }, {
				return path:substring(start: i + 1, end: len);
			});
			i: i - 1;
		});
		return path;
	}

	Function is pinPath(String is path){
		if({ path == '' }, { return; });
		local String is name: :baseNameOf(path: path);
		if({ name == '' }, { name: path; });
		if({ pinned:add(name: name, path: path) }, {
			pinned:save();
			local Function is cb: pinnedChangeHandler;
			cb();
			:notifyRefresh();
		});
	}

	Function is pinCurrentDirectory(){
		local Function of String is dirFn: activeDirProvider;
		:pinPath(path: dirFn());
	}

	Function is pinCurrentFile(){
		local Function of String is fileFn: activeFileProvider;
		:pinPath(path: fileFn());
	}

	Function is toggleDefaultMonospace(){
		model:defaultMonospace: !model:defaultMonospace;
		model:save();
		local Function is cb: defaultsChangeHandler;
		cb(model:defaultMonospace, model:defaultWrap, model:defaultShowFileTree);
		:notifyRefresh();
	}

	Function is toggleDefaultWrap(){
		model:defaultWrap: !model:defaultWrap;
		model:save();
		local Function is cb: defaultsChangeHandler;
		cb(model:defaultMonospace, model:defaultWrap, model:defaultShowFileTree);
		:notifyRefresh();
	}

	Function is toggleDefaultShowFileTree(){
		model:defaultShowFileTree: !model:defaultShowFileTree;
		model:save();
		local Function is cb: defaultsChangeHandler;
		cb(model:defaultMonospace, model:defaultWrap, model:defaultShowFileTree);
		:notifyRefresh();
	}

	Function of String is docDeltaLabel(){
		local Int is v: (model:docTextDeltaPt + if({ model:docTextDeltaPt >= 0.0 }, { 0.5 }, { -0.5 })) as Int;
		if({ v > 0 }, { return '+' . (v as String) . ' pt'; });
		return (v as String) . ' pt';
	}

	Function of String is baseTextLabel(){
		local Int is v: (model:baseTextPt + 0.5) as Int;
		return (v as String) . ' pt';
	}
}