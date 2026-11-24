#! Package cleoweather:view
#! Live Cleo forecast view displaying the NWS HTTP request status and parsed forecast periods.

Class is CleoForecastView{
	replace [String] is namespace: ['cleoweather', 'view'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'cleo', [Cleo, CleoSection, CleoColor, as CleoColor(), CleoWidth, as CleoWidth(), BorderStyle, ThrobberShape, ThrobberEffect, TitlePlacement]],
		['base', 'net', HttpResponse],
		['base', 'sys', 'thread', [Task, ThreadScope]],
		['cleoweather', 'model', ForecastPeriod],
		['cleoweather', 'vm', WeatherViewModel]
	];

	local Function of CleoColor is periodColor(Int is temp, Int is index){
		if({ index % 2 == 0 }, {
			if({ temp >= 80 }, { return ansi(code: 215); });
			if({ temp <= 40 }, { return ansi(code: 117); });
			return ansi(code: 120);
		});
		return ansi(code: 250);
	}

	local Function is renderPeriods(CleoSection is fcSec, WeatherViewModel is vm){
		if({ vm:fetchError != '' }, {
			fcSec:addLine(text: "Error fetching forecast: {{vm:fetchError}}", color: ansi(code: 203));
			return;
		});
		if({ !vm:report:isOk() }, {
			fcSec:addLine(text: vm:report:errorMessage, color: ansi(code: 203));
			return;
		});
		fcSec:addLine(text: "Updated: {{vm:report:updatedAt}}", color: ansi(code: 245));
		local Int is count: vm:report:periods:length();
		local Int is i: 0;
		while({ i < count }, {
			local ForecastPeriod is p: vm:report:periods:get(index: i);
			fcSec:addLine(
				text: p:summaryText(),
				color: periodColor(temp: p:temperature, index: i),
				rightText: p:windText(),
				bold: i == 0
			);
			i: i + 1;
		});
	}

	## Fetches and displays the NWS forecast for the city currently selected in [vm].
	Function is show(WeatherViewModel is vm){
		local String is url: vm:forecastUrl();
		local Cleo is ui: Cleo(
			title: ' cleoweather ',
			titleColor: ansi(code: 255),
			titleBgColor: ansi(code: 24),
			width: percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: ansi(code: 33),
			dividerColor: ansi(code: 237)
		);
		local CleoSection is statusSec: ui:addSection(
			title: ' Request ',
			titleColor: ansi(code: 254),
			titleBgColor: ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 250)
		);
		local Int is reqSlot: statusSec:addShapeThrobber(
			shape: ThrobberShape:CIRCLE_DOT,
			effect: ThrobberEffect:BLINK,
			text: url,
			color: ansi(code: 252),
			rightText: 'fetching'
		);
		local CleoSection is fcSec: ui:addSection(
			title: vm:forecastTitle(),
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 250)
		);

		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				ui:start(scope: scope);
				local Task of HttpResponse is fetchTask: vm:fetchForecast(scope: scope, onDone: {
					if({ vm:fetchError != '' }, {
						statusSec:resolveSlot(index: reqSlot, badge: '✖', text: url, color: ansi(code: 203), rightText: 'failed');
					}, {
						if({ !vm:report:isOk() }, {
							statusSec:resolveSlot(index: reqSlot, badge: '✖', text: url, color: ansi(code: 203), rightText: 'parse error');
						}, {
							statusSec:resolveSlot(index: reqSlot, badge: '●', text: url, color: ansi(code: 82), rightText: "HTTP {{vm:httpStatusCode}}");
						});
					});
					renderPeriods(fcSec: fcSec, vm: vm);
				});
				fetchTask:await();
				ui:finish();
			},
			onError: local Function of Boolean(SpecError is _err){ false }
		);
	}
}
