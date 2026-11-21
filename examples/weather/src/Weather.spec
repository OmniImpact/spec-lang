#! Weather forecast example using base:net:Http, base:data:Json, and base:cleo:Cleo.
#! Fetches https://api.weather.gov/gridpoints/RAH/74,58/forecast on a worker
#! thread with callbacks and renders the forecast in a SpecUnit-style Cleo UI.

Class is Weather{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'net', HttpResponse],
		['base', 'net', HttpError],
		['base', 'net', as Http()],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
		['base', 'data', as Json()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		Output:line("Unhandled error: {{error:toString()}}");
		return true;
	}

	replace Function is init(){
		local Str is url: 'https://api.weather.gov/gridpoints/RAH/74,58/forecast';
		local String is urlStr: url as String;

		local Cleo is ui: Cleo(
			title: ' weather ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is statusSec: ui:addSection(
			title: ' Request ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local Int is reqSlot: statusSec:addShapeThrobber(
			shape: ThrobberShape:CIRCLE_DOT,
			effect: ThrobberEffect:BLINK,
			text: urlStr,
			color: CleoColor:ansi(code: 252),
			rightText: 'fetching'
		);
		local CleoSection is fcSec: ui:addSection(
			title: ' Raleigh / RAH (74,58) Forecast ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);

		ThreadScope:open(body: local Function(ThreadScope is scope){
			ui:start(scope: scope);
			Http:get(
				scope: scope,
				url: urlStr,
				onSuccess: local Function(HttpResponse is resp){
					statusSec:resolveSlot(index: reqSlot, badge: '●', text: urlStr, color: CleoColor:ansi(code: 252), rightText: "HTTP {{resp:statusCode}}");
					populateForecast(rawJson: resp:body, fcSec: fcSec);
				},
				onError: local Function(SpecError of HttpError is err){
					statusSec:resolveSlot(index: reqSlot, badge: '✖', text: urlStr, color: CleoColor:ansi(code: 203), rightText: 'failed');
					fcSec:addLine(text: "Error fetching forecast: {{err:description}}", color: CleoColor:ansi(code: 203));
				}
			);
			ui:finish();
		});
	}

	## Formats a single NWS forecast period object as a summary line.
	Function of String is formatPeriod(Map is p){
		local String is name: Json:getString(obj: p, key: 'name', default: '?');
		local Int is temp: Json:getInt(obj: p, key: 'temperature', default: 0);
		local String is unit: Json:getString(obj: p, key: 'temperatureUnit', default: 'F');
		local String is shortFc: Json:getString(obj: p, key: 'shortForecast', default: '');
		return "{{name}}: {{temp}}°{{unit}} · {{shortFc}}";
	}

	Function is populateForecast(String is rawJson, CleoSection is fcSec){
		local Result of Map to JsonError is rootR: Json:parseMapResult(text: rawJson);
		local Map is root: Map:init();
		local String is parseMsg: '';
		match(on: rootR, when: [
			Result:Ok: local Function of Void(Map is v){
				root: v;
			},
			Result:Err: local Function of Void(SpecError of JsonError is e){
				parseMsg: e:description;
			}
		]);
		if({ parseMsg != '' }, {
			fcSec:addLine(text: "JSON parse error: {{parseMsg}}", color: CleoColor:ansi(code: 203));
			return;
		});
		local Map is props: Json:getObject(obj: root, key: 'properties');
		local String is updated: Json:getString(obj: props, key: 'updateTime', default: Json:getString(obj: props, key: 'updated', default: 'unknown'));
		local Array is periods: Json:getArray(obj: props, key: 'periods');

		fcSec:addLine(text: "Updated: {{updated}}", color: CleoColor:ansi(code: 245));

		local Int is limit: if({ periods:length() < 6 }, { periods:length() }, { 6 });
		local Int is i: 0;
		while({ i < limit }, {
			local Map is p: Json:getObjectAt(arr: periods, index: i);
			local String is wind: Json:getString(obj: p, key: 'windSpeed', default: '');
			local String is dir: Json:getString(obj: p, key: 'windDirection', default: '');
			fcSec:addLine(
				text: formatPeriod(p: p),
				color: CleoColor:ansi(code: 252),
				rightText: "Wind {{wind}} {{dir}}"
			);
			i: i + 1;
		});
	}
}
