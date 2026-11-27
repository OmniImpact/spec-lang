#! Package base:wardrobe
#! File-browser tree widget built on [TreeView] with a top pinned-locations dropdown backed by [FilePinnedLocations].

Class of SewNode is FileTree{
	replace [String] is namespace: ['base', 'wardrobe', 'file'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Dir],
		['base', 'sys', Process],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'scrap', 'tree', TreeNode],
		['base', 'scrap', 'tree', TreeView],
		['base', 'scrap', ScrollView],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'scrap', 'menu', MenuItemConfig],
		['base', 'scrap', 'menu', MenuContext],
		['base', 'wardrobe', 'file', FilePinnedLocations]
	];

	String is rootDir: '';
	String is rootLabel: '';
	Boolean is showHidden: false;
	Boolean is headerHover: false;
	String is dropdownIconSvg: '';
	String is plusIconSvg: '';
	String is minusIconSvg: '';
	FilePinnedLocations is pinned: FilePinnedLocations();
	TreeView is treeView: TreeView();
	ScrollView is treeScroll: ScrollView(child: TreeView());
	MenuContext is contextMenu: MenuContext();
	Function is onOpenFile: local Function(String is _path){};

	replace Function is init(
		String is rootDir: '',
		MenuContext is contextMenu: MenuContext(),
		Function is onOpenFile: local Function(String is _path){},
		Boolean is showHidden: false,
		String is dropdownIconSvg: '',
		String is plusIconSvg: '',
		String is minusIconSvg: ''
	){
		:contextMenu: contextMenu;
		:onOpenFile: onOpenFile;
		:showHidden: showHidden;
		:dropdownIconSvg: dropdownIconSvg;
		:plusIconSvg: plusIconSvg;
		:minusIconSvg: minusIconSvg;
		:pinned: FilePinnedLocations();
		:pinned:load();
		:treeView: TreeView(
			plusIconSvg: plusIconSvg,
			minusIconSvg: minusIconSvg,
			onToggle: local Function(TreeNode is node){ :handleToggle(node: node); },
			onActivate: local Function(TreeNode is node){
				local Function is cb: onOpenFile;
				cb(node:id);
			}
		);
		:treeScroll: ScrollView(child: treeView);
		local String is startDir: rootDir;
		if({ startDir == '' || !Dir():isDir(path: startDir) }, {
			local String is pwd: Process():getEnv(key: 'PWD', default: '');
			if({ pwd != '' && Dir():isDir(path: pwd) }, {
				startDir: pwd;
			}, {
				local String is home: Process():getEnv(key: 'HOME', default: '');
				startDir: if({ home != '' && Dir():isDir(path: home) }, { home }, { '/' });
			});
		});
		:setRootDir(dirPath: startDir);
	}

	local Function of String is baseName(String is path){
		if({ path == '/' }, { return '/'; });
		local Int is len: path:length();
		if({ len == 0 }, { return '/'; });
		local Int is i: len - 1;
		while({ i >= 0 && path:byteAt(index: i) != 47 }, { i: i - 1; });
		local String is b: path:substring(start: i + 1, end: len);
		return if({ b == '' }, { path }, { b });
	}

	local Function of String is joinPath(String is dir, String is name){
		if({ dir == '' || dir == '.' }, { return name; });
		if({ dir:endsWith(suffix: '/') }, { return dir . name; });
		return dir . '/' . name;
	}

	local Function is sortStrings(Array of String is items){
		local Int is n: items:length();
		local Int is i: 1;
		while({ i < n }, {
			local String is key: items:get(index: i);
			local String is keyLow: key:toLower();
			local Int is j: i - 1;
			while({ j >= 0 && items:get(index: j):toLower() > keyLow }, {
				items:set(index: j + 1, item: items:get(index: j));
				j: j - 1;
			});
			items:set(index: j + 1, item: key);
			i: i + 1;
		});
	}

	local Function of Array of TreeNode is loadDirectoryNodes(String is dirPath){
		local Array of TreeNode is nodes: Array();
		if({ dirPath == '' || !Dir():isDir(path: dirPath) }, { return nodes; });
		local Array of String is raw: Dir():dirList(path: dirPath);
		local Array of String is dirs: Array();
		local Array of String is files: Array();
		local Int is i: 0;
		while({ i < raw:length() }, {
			local String is name: raw:get(index: i);
			if({ name != '.' && name != '..' && (showHidden || !name:startsWith(prefix: '.')) }, {
				local String is full: :joinPath(dir: dirPath, name: name);
				if({ Dir():isDir(path: full) }, {
					dirs:add(item: name);
				}, {
					files:add(item: name);
				});
			});
			i: i + 1;
		});
		:sortStrings(items: dirs);
		:sortStrings(items: files);
		i: 0;
		while({ i < dirs:length() }, {
			local String is dname: dirs:get(index: i);
			nodes:add(item: TreeNode(
				id: :joinPath(dir: dirPath, name: dname),
				label: dname,
				expandable: true,
				expanded: false,
				loaded: false
			));
			i: i + 1;
		});
		i: 0;
		while({ i < files:length() }, {
			local String is fname: files:get(index: i);
			nodes:add(item: TreeNode(
				id: :joinPath(dir: dirPath, name: fname),
				label: fname,
				expandable: false
			));
			i: i + 1;
		});
		return nodes;
	}

	local Function is handleToggle(TreeNode is node){
		if({ node:expandable && node:expanded && !node:loaded }, {
			node:children: :loadDirectoryNodes(dirPath: node:id);
			node:loaded: true;
		});
	}

	Function is setRootDir(String is dirPath){
		if({ dirPath == '' || !Dir():isDir(path: dirPath) }, { return; });
		:rootDir: dirPath;
		:rootLabel: :baseName(path: dirPath);
		treeView:setRoots(roots: :loadDirectoryNodes(dirPath: dirPath));
		invalidate();
	}

	local Function of Int is headerHeightPx(){
		local Int is h: activeScale:px(pt: 28.0);
		return if({ h < 22 }, { 22 }, { h });
	}

	local Function of Int is headerFontPx(){
		local Int is px: activeScale:px(pt: 15.0);
		return if({ px < 11 }, { 11 }, { px });
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		treeScroll:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		treeScroll:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		treeScroll:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: c:clampW(w: c:maxW);
		local Int is h: c:clampH(h: c:maxH);
		local Int is hh: :headerHeightPx();
		local Int is th: if({ h > hh }, { h - hh }, { 0 });
		treeScroll:measure(c: Constraints(minW: w, maxW: w, minH: th, maxH: th));
		desiredSize: Size(width: w, height: h);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is hh: :headerHeightPx();
		local Int is th: if({ bounds:height > hh }, { bounds:height - hh }, { 0 });
		treeScroll:arrange(bounds: Rect(x: bounds:x, y: bounds:y + hh, width: bounds:width, height: th));
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is hh: :headerHeightPx();
		local Int is bg: if({ headerHover }, { activeTheme:hoverBg }, { activeTheme:toolbarBg });
		local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: hh, color: bg);
		ctx:fillRect(x: b:x, y: b:y + hh - linePx, w: b:width, h: linePx, color: activeTheme:toolbarBorder);

		local Int is fpx: :headerFontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is chevSz: activeScale:px(pt: 11.0);
		if({ chevSz < 9 }, { chevSz: 9; });
		ctx:setClip(x: b:x, y: b:y, w: b:width, h: hh);
		ctx:drawText(
			x: b:x + padX,
			y: b:y + (hh - th) / 2,
			text: rootLabel,
			color: activeTheme:textPrimary,
			pixelHeight: fpx,
			bold: true
		);
		local Int is lw: ctx:measureTextWidth(text: rootLabel, pixelHeight: fpx, bold: true);
		local Int is chevX: b:x + padX + lw + activeScale:px(pt: 4.0);
		if({ dropdownIconSvg != '' && chevX + chevSz <= b:x + b:width - 4 }, {
			SvgRenderer:shared:draw(
				ctx: ctx,
				svgSrc: dropdownIconSvg,
				x: chevX,
				y: b:y + (hh - chevSz) / 2,
				widthPx: chevSz,
				heightPx: chevSz,
				tintColor: activeTheme:textMuted,
				useTint: true
			);
		});
		ctx:clearClip();

		treeScroll:paint(ctx: ctx);
	}

	local Function is openPinnedDropdown(Int is x, Int is y){
		pinned:load();
		local Array of MenuItemConfig is items: Array();
		local Int is i: 0;
		while({ i < pinned:paths:length() }, {
			local String is pname: pinned:names:get(index: i);
			local String is ppath: pinned:paths:get(index: i);
			items:add(item: MenuItemConfig(
				id: 'pin_' . (i as String),
				label: pname,
				checked: (ppath == rootDir),
				kind: 'radio',
				onClick: local Function(){ :setRootDir(dirPath: ppath); }
			));
			i: i + 1;
		});
		if({ items:length() > 0 }, {
			local Rect is b: bounds();
			contextMenu:open(x: b:x + 2, y: b:y + :headerHeightPx(), items: items);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is hh: :headerHeightPx();
		local Boolean is nextHover: x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + hh;
		local Boolean is changed: false;
		if({ nextHover != headerHover }, {
			headerHover: nextHover;
			invalidate();
			changed: true;
		});
		if({ treeScroll:onPointerMove(x: x, y: y) }, { changed: true; });
		return changed;
	}

	replace Function is clearHover(){
		if({ headerHover }, {
			headerHover: false;
			invalidate();
		});
		treeScroll:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		local Int is hh: :headerHeightPx();
		if({ x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + hh }, {
			:openPinnedDropdown(x: x, y: y);
			return true;
		});
		return treeScroll:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return treeScroll:onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return treeScroll:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return treeScroll:onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return treeScroll:onScrollX(deltaX: deltaX);
	}
}
