#! Package cleoweather:view
#! Interactive two-step Cleo menu for choosing a US state and then a major city.

Class is CleoSelectorView{
	replace [String] is namespace: ['cleoweather', 'view'];

	merge [[String]] is using: [
		['base', 'cleo', [Cleo, CleoSection, CleoColor, as CleoColor(), CleoWidth, as CleoWidth(), BorderStyle, TitlePlacement]],
		['base', 'sys', [as Input(), as Output()]],
		['cleoweather', 'model', [CityLocation, StateGroup]],
		['cleoweather', 'vm', WeatherViewModel]
	];

	local Function of Cleo is buildMenuUi(String is subtitle){
		return Cleo(
			title: " cleoweather · {{subtitle}} ",
			titleColor: ansi(code: 255),
			titleBgColor: ansi(code: 24),
			width: percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: ansi(code: 33),
			dividerColor: ansi(code: 237)
		);
	}

	## Prompts the user to select a US state from [vm] using Cleo + stdin.
	Function is chooseState(WeatherViewModel is vm){
		local Cleo is ui: buildMenuUi(subtitle: 'Step 1 of 2');
		local CleoSection is sec: ui:addSection(
			title: ' Choose a US State ',
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 252)
		);
		local Int is i: 0;
		while({ i < vm:states:length() }, {
			local StateGroup is st: vm:states:get(index: i);
			sec:addLine(
				text: "  {{i + 1}}. {{st:displayLabel()}}",
				color: ansi(code: 195),
				rightText: "{{st:cities:length()}} cities"
			);
			i: i + 1;
		});
		ui:flushFinal();

		local StateGroup is defState: vm:selectedState();
		local Boolean is picked: false;
		while({ !picked }, {
			consOut(text: "Select state [{{defState:code}}]: ");
			readLine(onLine: local Function(String is lineText){
				local String is trimmed: lineText:trim();
				if({ trimmed == '' }, {
					picked: true;
				}, {
					if({ vm:selectStateByInput(input: trimmed) }, {
						picked: true;
					}, {
						line("  Unknown state '{{trimmed}}'. Enter a number (1-{{vm:states:length()}}), code, or name.");
					});
				});
			});
		});
	}

	## Prompts the user to select a major city in the chosen state from [vm].
	Function is chooseCity(WeatherViewModel is vm){
		local StateGroup is st: vm:selectedState();
		local Cleo is ui: buildMenuUi(subtitle: 'Step 2 of 2');
		local CleoSection is sec: ui:addSection(
			title: " Choose a City in {{st:name}} ({{st:code}}) ",
			titleColor: ansi(code: 120),
			titleBgColor: ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 252)
		);
		local Int is i: 0;
		while({ i < st:cities:length() }, {
			local CityLocation is city: st:cities:get(index: i);
			sec:addLine(
				text: "  {{i + 1}}. {{city:name}}",
				color: ansi(code: 195),
				rightText: city:gridLabel()
			);
			i: i + 1;
		});
		ui:flushFinal();

		local CityLocation is defCity: vm:selectedCity();
		local Boolean is picked: false;
		while({ !picked }, {
			consOut(text: "Select city [{{defCity:name}}]: ");
			readLine(onLine: local Function(String is lineText){
				local String is trimmed: lineText:trim();
				if({ trimmed == '' }, {
					picked: true;
				}, {
					if({ vm:selectCityByInput(input: trimmed) }, {
						picked: true;
					}, {
						line("  Unknown city '{{trimmed}}'. Enter a number (1-{{st:cities:length()}}) or city name.");
					});
				});
			});
		});
	}
}
