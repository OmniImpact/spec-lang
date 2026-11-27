#! Package suitshowcase:view
#! Showcase page for TextInput, DecoratedTextInput, and Switch controls.

Class is InputsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Switch],
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

		return SectionV(
			children: Array([
				Label(text: 'Inputs & Toggles', heading: true),
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
					title: 'Switch Controls',
					child: SectionV(
						children: Array([
							SectionH(children: Array([swA, Label(text: 'Enable Feature A')])),
							SectionH(children: Array([swB, Label(text: 'Enable Feature B')]))
						])
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
