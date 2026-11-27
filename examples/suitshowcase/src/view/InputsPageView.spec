#! Package suitshowcase:view
#! Showcase page for TextInput, DecoratedTextInput, and Switch controls.

Class is InputsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Switch],
		['base', 'scrap', Checkbox],
		['base', 'scrap', RadioButton],
		['base', 'scrap', RadioGroup],
		['base', 'scrap', Accordion],
		['base', 'scrap', TextInput],
		['base', 'scrap', DecoratedTextInput],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	DecoratedTextInput is stepperInput: DecoratedTextInput();
	Switch is swA: Switch();
	Switch is swB: Switch();
	TextEmitter is echoLabel: TextEmitter(initial: '');
	TextEmitter is toggleStatus: TextEmitter(initial: 'Radio: Medium | Checkboxes: Auto-save');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		echoLabel:emit(value: 'Text: ' . vm:sampleInputText:current() . ' | Stepper: ' . (vm:stepperVal as String));

		local TextInput is textBox: TextInput(
			text: vm:sampleInputText:current(),
			placeholder: 'Type here...',
			minWidthPt: 180.0,
			tooltip: 'Supports Left/Right/Home/End cursor navigation and horizontal scrolling',
			onChange: local Function(String is next){
				vm:sampleInputText:emit(value: next);
				echoLabel:emit(value: 'Text: ' . next . ' | Stepper: ' . (vm:stepperVal as String));
			}
		);

		:stepperInput: DecoratedTextInput(
			text: (vm:stepperVal as String) . ' px',
			suffix: ' px',
			tooltip: 'Type a number or press Up/Down arrows',
			onLeftClick: local Function(){ vm:adjustStepper(delta: -1); },
			onRightClick: local Function(){ vm:adjustStepper(delta: 1); },
			onSubmit: local Function(String is raw){ vm:setStepperFromText(raw: raw); }
		);

		:swA: Switch(
			checked: vm:switchA:current(),
			tooltip: 'Toggle option A (Space or Enter when focused)',
			onToggle: local Function(Boolean is next){ vm:switchA:emit(value: next); }
		);
		:swB: Switch(
			checked: vm:switchB:current(),
			tooltip: 'Toggle option B (Space or Enter when focused)',
			onToggle: local Function(Boolean is next){ vm:switchB:emit(value: next); }
		);

		local Checkbox is cbAuto: Checkbox(
			checked: true,
			label: 'Auto-save changes',
			tooltip: 'Checkbox with Space/Enter keyboard support',
			onToggle: local Function(Boolean is next){
				toggleStatus:emit(value: 'Auto-save: ' . (if({ next }, { 'On' }, { 'Off' })));
			}
		);
		local Checkbox is cbLine: Checkbox(
			checked: false,
			label: 'Show whitespace markers',
			onToggle: local Function(Boolean is next){
				toggleStatus:emit(value: 'Whitespace: ' . (if({ next }, { 'On' }, { 'Off' })));
			}
		);
		local Checkbox is cbDis: Checkbox(
			checked: true,
			label: 'Disabled checked option',
			enabled: false
		);

		local Array of String is sizeOpts: Array(['Small', 'Medium', 'Large']);
		local RadioGroup is rgVert: RadioGroup(
			options: sizeOpts,
			selectedIndex: 1,
			onSelect: local Function(Int is idx){
				toggleStatus:emit(value: 'Vertical Radio: ' . sizeOpts:get(index: idx));
			}
		);
		local Array of String is modeOpts: Array(['Auto', 'Light', 'Dark']);
		local RadioGroup is rgHoriz: RadioGroup(
			options: modeOpts,
			selectedIndex: 0,
			horizontal: true,
			onSelect: local Function(Int is idx){
				toggleStatus:emit(value: 'Horizontal Radio: ' . modeOpts:get(index: idx));
			}
		);

		local Accordion is acc1: Accordion(
			title: 'General Preferences',
			expanded: true,
			tooltip: 'Click header or press Space/Enter to collapse/expand',
			child: SectionV(
				children: Array([
					Checkbox(checked: true, label: 'Restore previous session'),
					Checkbox(checked: false, label: 'Check for updates automatically')
				])
			)
		);
		local Accordion is acc2: Accordion(
			title: 'Advanced Options',
			expanded: false,
			child: SectionV(
				children: Array([
					RadioGroup(options: Array(['Balanced', 'Low Latency', 'Power Saver']), selectedIndex: 0)
				])
			)
		);

		return SectionV(
			children: Array([
				Label(text: 'Inputs & Toggles', style: TextStyle:H1),
				Frame(
					title: 'TextInput & DecoratedTextInput',
					child: SectionV(
						children: Array([
							SectionV(title: 'Single-Line TextInput', children: Array([textBox])),
							SectionV(title: 'DecoratedTextInput (with suffix + Up/Down)', children: Array([stepperInput])),
							TextScrap(text: echoLabel, muted: true)
						])
					)
				),
				Frame(
					title: 'Switch, Checkbox & RadioGroup',
					child: SectionV(
						children: Array([
							SectionH(children: Array([swA, Label(text: 'Enable Feature A')])),
							SectionH(children: Array([swB, Label(text: 'Enable Feature B')])),
							SectionV(title: 'Checkboxes', children: Array([cbAuto, cbLine, cbDis])),
							SectionV(title: 'RadioGroup (Vertical)', children: Array([rgVert])),
							SectionV(title: 'RadioGroup (Horizontal)', children: Array([rgHoriz])),
							TextScrap(text: toggleStatus, muted: true)
						])
					)
				),
				Frame(
					title: 'Accordion Sections',
					child: SectionV(
						children: Array([acc1, acc2])
					)
				)
			])
		);
	}

	Function is sync(){
		stepperInput:setText(next: (vm:stepperVal as String) . ' px');
		echoLabel:emit(value: 'Text: ' . vm:sampleInputText:current() . ' | Stepper: ' . (vm:stepperVal as String));
		swA:setChecked(next: vm:switchA:current());
		swB:setChecked(next: vm:switchB:current());
	}
}
