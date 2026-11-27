#! Package suitshowcase:view
#! Showcase page for DateSelector, TimeSelector, DateDropdown, TimeDropdown, and enhanced DateTime utilities.

Class is DateTimePageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', DateSelector],
		['base', 'scrap', DateDropdown],
		['base', 'scrap', TimeSelector],
		['base', 'scrap', TimeDropdown],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	DateTime is selectedDt: DateTime:now();
	TextEmitter is summaryLabel: TextEmitter(initial: '');
	DateSelector is datePicker: DateSelector();
	TimeSelector is timePicker12: TimeSelector();
	TimeSelector is timePicker24: TimeSelector();
	DateDropdown is dateDrop: DateDropdown();
	TimeDropdown is timeDrop: TimeDropdown();

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	local Function is updateSummary(DateTime is dt){
		:selectedDt: dt;
		summaryLabel:emit(value: DateTime:monthName(month: dt:getMonth()) . ' ' . (dt:getDay() as String) . ', ' . (dt:getYear() as String) . ' | ' . dt:formatTime12(includeSeconds: true) . ' | ISO: ' . dt:formatIso());
	}

	Function of SewNode is build(){
		:selectedDt: DateTime:now();
		:updateSummary(dt: selectedDt);

		:datePicker: DateSelector(
			value: selectedDt,
			tooltip: 'Select a date from the monthly calendar grid',
			onChange: local Function(DateTime is dt){
				local DateTime is merged: selectedDt:withDate(year: dt:getYear(), month: dt:getMonth(), day: dt:getDay());
				:updateSummary(dt: merged);
				dateDrop:setValue(next: merged);
				vm:statusText:emit(value: 'Date selected: ' . merged:formatDate());
			}
		);

		:timePicker12: TimeSelector(
			value: selectedDt,
			use24Hour: false,
			showSeconds: false,
			tooltip: '12-hour time selector',
			onChange: local Function(DateTime is dt){
				local DateTime is merged: selectedDt:withTime(hour: dt:getHour(), minute: dt:getMinute(), second: dt:getSecond());
				:updateSummary(dt: merged);
				timePicker24:setValue(next: merged);
				timeDrop:setValue(next: merged);
				vm:statusText:emit(value: 'Time selected: ' . merged:formatTime12());
			}
		);

		:timePicker24: TimeSelector(
			value: selectedDt,
			use24Hour: true,
			showSeconds: true,
			tooltip: '24-hour time selector with seconds',
			onChange: local Function(DateTime is dt){
				local DateTime is merged: selectedDt:withTime(hour: dt:getHour(), minute: dt:getMinute(), second: dt:getSecond());
				:updateSummary(dt: merged);
				timePicker12:setValue(next: merged);
				timeDrop:setValue(next: merged);
				vm:statusText:emit(value: 'Time selected: ' . merged:formatTime());
			}
		);

		:dateDrop: DateDropdown(
			value: selectedDt,
			tooltip: 'Dropdown calendar selector',
			onChange: local Function(DateTime is dt){
				local DateTime is merged: selectedDt:withDate(year: dt:getYear(), month: dt:getMonth(), day: dt:getDay());
				:updateSummary(dt: merged);
				datePicker:setValue(next: merged);
				vm:statusText:emit(value: 'Date dropdown: ' . merged:formatDate());
			}
		);

		:timeDrop: TimeDropdown(
			value: selectedDt,
			use24Hour: false,
			tooltip: 'Dropdown time selector',
			onChange: local Function(DateTime is dt){
				local DateTime is merged: selectedDt:withTime(hour: dt:getHour(), minute: dt:getMinute(), second: dt:getSecond());
				:updateSummary(dt: merged);
				timePicker12:setValue(next: merged);
				timePicker24:setValue(next: merged);
				vm:statusText:emit(value: 'Time dropdown: ' . merged:formatTime12());
			}
		);

		return SectionV(
			children: Array([
				Label(text: 'Date & Time Selectors', style: TextStyle:H1),
				TextScrap(text: summaryLabel, wrap: true, muted: true),
				Frame(
					title: 'Dropdown Selectors (DropdownPopup Overlay)',
					child: SectionH(
						children: Array([
							SectionV(title: 'DateDropdown', children: Array([dateDrop])),
							SectionV(title: 'TimeDropdown', children: Array([timeDrop]))
						])
					)
				),
				Frame(
					title: 'Standalone DateSelector & TimeSelector',
					child: SectionH(
						children: Array([
							SectionV(title: 'Calendar DateSelector', children: Array([datePicker])),
							SectionV(
								title: 'TimeSelector (12h & 24h)',
								children: Array([timePicker12, timePicker24])
							)
						])
					)
				)
			])
		);
	}
}
