#! Package specserv:model
#! Configuration model for a single served directory site.

Class is SiteConfig{
	replace [String] is namespace: ['specserv', 'model'];

	String is name: 'Site';
	String is directory: '.';
	Int is port: 47321;
	Boolean is enabled: true;

	replace Function is init(String is name: 'Site', String is directory: '.', Int is port: 47321, Boolean is enabled: true){
		:name: name;
		:directory: directory;
		:port: port;
		:enabled: enabled;
	}

	Function of String is summary(){
		local String is flag: if({ enabled }, { '[ON]' }, { '[OFF]' });
		return flag . ' ' . name . ' (:' . (port as String) . ') -> ' . directory;
	}
}
