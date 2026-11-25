#! Package specserv:model
#! JSON-backed server configuration managing multiple sites and port allocation.

Class is ServerConfig{
	replace [String] is namespace: ['specserv', 'model'];

	merge [[String]] is using: [
		['specserv', 'model', SiteConfig],
		['base', 'data', as Json()],
		['base', 'struct', [Array, Map]],
		['base', 'sys', as File()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	held Int is DEFAULT_BASE_PORT: 47321;

	[SiteConfig] is sites: [];

	replace Function is init([SiteConfig] is sites: []){
		:sites: sites;
	}

	## True when [port] is already used by any active/enabled site (or any site if [enabledOnly] is false).
	Function of Boolean is isPortUsed(Int is port, Boolean is enabledOnly: false){
		local Int is i: 0;
		while({ i < sites:length() }, {
			local SiteConfig is s: sites:get(index: i);
			if({ s:port == port && (!enabledOnly || s:enabled) }, {
				return true;
			});
			i++;
		});
		return false;
	}

	## Returns the default port (47321) or the next higher port not used by any active site.
	Function of Int is nextAvailablePort(){
		local Int is cand: ServerConfig:DEFAULT_BASE_PORT;
		while({ isPortUsed(port: cand, enabledOnly: false) }, {
			cand++;
		});
		return cand;
	}

	## Adds a site for [directory], defaulting to [nextAvailablePort] when [port] <= 0 or already taken.
	Function of SiteConfig is addDirectory(String is name, String is directory, Int is port: 0, Boolean is enabled: true){
		local Int is chosenPort: if({ port > 0 && !isPortUsed(port: port, enabledOnly: false) }, { port }, { nextAvailablePort() });
		local String is cleanName: if({ name:trim() != '' }, { name:trim() }, { 'Site ' . ((sites:length() + 1) as String) });
		local SiteConfig is site: SiteConfig(name: cleanName, directory: directory, port: chosenPort, enabled: enabled);
		sites:push(item: site);
		return site;
	}

	Function of Boolean is removeAt(Int is index){
		if({ index < 0 || index >= sites:length() }, { return false; });
		local [SiteConfig] is next: [];
		times(count: sites:length(), worker: local Function(Int is i){
			if({ i != index }, { next:push(item: sites:get(index: i)); });
		});
		sites: next;
		return true;
	}

	Function of String is toJsonString(){
		local String is out: "{\n  \"sites\": [";
		times(count: sites:length(), worker: local Function(Int is i){
			local SiteConfig is s: sites:get(index: i);
			if({ i > 0 }, { out: out . ','; });
			local String is enStr: if({ s:enabled }, { 'true' }, { 'false' });
			out: out . "\n    {\n"
				. "      \"name\": \"" . escapeString(str: s:name) . "\",\n"
				. "      \"directory\": \"" . escapeString(str: s:directory) . "\",\n"
				. "      \"port\": " . (s:port as String) . ",\n"
				. "      \"enabled\": " . enStr . "\n"
				. "    }";
		});
		if({ sites:length() > 0 }, { out: out . "\n  "; });
		return out . "]\n}";
	}

	Function of Boolean is saveToFile(String is path){
		return fileWrite(path: path, content: toJsonString() . "\n", onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});
	}

	Function of ServerConfig is loadFromJson(String is jsonText){
		local ServerConfig is cfg: ServerConfig();
		local Map of String to Any is root: parseObjectText(text: jsonText);
		if({ !root:has(key: 'sites') }, { return cfg; });
		local Array of Any is rawSites: getArray(obj: root, key: 'sites', default: Array());
		times(count: rawSites:length(), worker: local Function(Int is i){
			local Map of String to Any is item: getObjectAt(arr: rawSites, index: i);
			local String is nm: getString(obj: item, key: 'name', default: 'Site');
			local String is dir: getString(obj: item, key: 'directory', default: '.');
			local Int is pt: getInt(obj: item, key: 'port', default: 0);
			local Boolean is en: getBool(obj: item, key: 'enabled', default: true);
			cfg:addDirectory(name: nm, directory: dir, port: pt, enabled: en);
		});
		return cfg;
	}

	Function of ServerConfig is loadFromFile(String is path){
		if({ !fileExists(path: path) }, {
			return ServerConfig();
		});
		local String is text: fileRead(path: path, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		if({ text:trim() == '' }, { return ServerConfig(); });
		return loadFromJson(jsonText: text);
	}
}
